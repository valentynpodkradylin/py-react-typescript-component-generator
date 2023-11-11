from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias, Iterable
# from typed_argparse import TypedArgs


SRC_DIR = Path(__file__).parent / "src"

BaseFolder: TypeAlias = Literal["components", "pages"]


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@dataclass
class Element:
    name: str
    full_path: Path
    folder_type: BaseFolder


class AskParams:
    """Ask params from user, parse it and create Element structure"""

    def __init__(self) -> None:
        self._element: Element

    def ask(self) -> Element:
        base_folder = self._ask_base_folder()

        self._element = self._parse_as_element(
            self._ask_element(base_folder),
            base_folder
        )

        return self._element

    def ask_ok(self, filenames: Iterable[str]) -> None:
        filenames = "\n\t".join(filenames)
        while True:
            print(f"\nИтак, создаём файлы:\n"
                  f"{Colors.HEADER}\t{filenames} {Colors.ENDC}\n\n")
            match input("Ок? [Y]/N: ").strip().lower():
                case "y" | "": return
                case "n": exit("Ок, выходим, ничего не создал.")
                case _: print("Не понял, давай ещё раз.")

    def _parse_as_element(self, element_str: str, base_folder: BaseFolder) -> Element:
        element_as_list = element_str.split("/")
        print(f"element_as_list: {element_as_list}")

        element_name = element_as_list[-1]
        print(f"element_name: {element_name}")

        if len(element_as_list) > 1:
            relative_path = "/".join(element_as_list[:-1])
            print(f"relative_path: {relative_path}")
        else:
            relative_path = element_name

        return Element(
            full_path=SRC_DIR / base_folder / relative_path,
            name=element_name,
            folder_type=base_folder
        )

    def _ask_base_folder(self) -> BaseFolder:
        while True:
            match input('c - components, p - pages: ').strip().lower():
                case 'c': return 'components'
                case 'p': return 'pages'
                case _: print("Не понял, давай ещё раз.")

    def _ask_element(self, base_folder: BaseFolder) -> str:
        return input(f"Куда кладём? {base_folder}/").strip()


class FileCreator(ABC):
    def __init__(self, element: Element) -> None:
        self._element = element

    def create(self):
        self._create_empty_file()
        self._write_file_contents()

    def get_relative_filename(self) -> str:
        relative_path_start_index = 1 + len(str(SRC_DIR.resolve()))
        result = str(
            self.get_absolute_filename().resolve()
        )[relative_path_start_index:]

        return result

    def _create_empty_file(self):
        """Init file if not exists"""
        self.get_absolute_filename().parent.mkdir(parents=True, exist_ok=True)
        self.get_absolute_filename().touch(exist_ok=True)

    @abstractmethod
    def get_absolute_filename(self) -> Path:
        """Returns file in Path format"""
        pass

    @abstractmethod
    def _write_file_contents(self) -> None:
        """Fill file with contents"""
        pass


class ElementFilesCreator:
    def __init__(self, element: Element) -> None:
        self._element = element
        self._file_creators: list[FileCreator] = []

    def create(self) -> None:
        for file_creator in self._file_creators:
            file_creator.create()

    def register_file_creators(self, *file_creators: type[FileCreator]):
        for fc in file_creators:
            self._file_creators.append(fc(element=self._element))

    def get_relative_filenames(self) -> tuple[str, ...]:
        return tuple(fc.get_relative_filename() for fc in self._file_creators)


class TSXFileCreator(FileCreator):
    def get_absolute_filename(self) -> Path:
        return self._element.full_path / (self._element.name + ".tsx")

    def _write_file_contents(self):
        element_name = self._element.name
        self.get_absolute_filename().write_text(
            f"""
import {{ FC }} from "react";
import styles from "./{element_name}.module.css" 
                
interface {element_name}Props {{
                    
}}
                
const {element_name}: FC<{element_name}Props> = () => {{
    return (
        <div styles={{styles.{element_name}}}>
            {element_name}
        </div>
    );
}};
                
export default {element_name};""".strip())


class IndexFileCreator(FileCreator):
    def get_absolute_filename(self) -> Path:
        return self._element.full_path / "index.ts"

    def _write_file_contents(self) -> Path:
        current_file_content = self.get_absolute_filename().read_text()

        if current_file_content.strip():
            return

        self.get_absolute_filename().write_text(
            f"""import {{ default }} from "./{self._element.name}"; """.strip())


class CSSModuleFileCreator(FileCreator):
    def get_absolute_filename(self) -> Path:
        return self._element.full_path / (self._element.name + ".module.css")

    def _write_file_contents(self) -> Path:
        return self.get_absolute_filename().write_text(
            f""".{self._element.name} {{
}}""".strip())


def main():
    asker = AskParams()
    element = asker.ask()

    print(f"element.name: {element.name}")
    print(f"element.full_path: {element.full_path}")

    element_creator = ElementFilesCreator(element)
    element_creator.register_file_creators(
        TSXFileCreator,
        IndexFileCreator,
        CSSModuleFileCreator,
    )

    asker.ask_ok(element_creator.get_relative_filenames())
    element_creator.create()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

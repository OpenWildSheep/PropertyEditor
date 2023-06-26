from pathlib import Path
from typing import Tuple, List

from EntityLibPy import DataKind


class ColorConfig:
    background: Tuple[int, int, int] = (51, 51, 51)  # grey
    default: Tuple[int, int, int] = (255, 255, 255)  # white
    is_set: Tuple[int, int, int] = (255, 255, 0)  # yellow
    parent: Tuple[int, int, int] = (0, 255, 255)  # blue
    local: Tuple[int, int, int] = (0, 255, 75)  # green
    deleted_element: Tuple[int, int, int] = (255, 160, 0)  # another yellow
    invalid: Tuple[int, int, int] = (255, 80, 120)  # some kind of red
    light_grey: Tuple[int, int, int] = (204, 204, 204)


class Config:
    src_path: Path = Path(Path(__file__).parent.resolve(), "_sources")
    container_types: List[DataKind] = [
        DataKind.array,
        DataKind.unionSet,
        DataKind.objectSet,
        DataKind.primitiveSet,
        DataKind.object,
    ]
    default_dir_key: str = "default_dir"
    file_types = []
    color: ColorConfig = ColorConfig()

from dataclasses import dataclass
from enum import Enum
from typing import List


class BuildSystem(str, Enum):
    MAVEN = "maven"
    ANT = "ant"
    GRADLE = "gradle"


@dataclass
class ChangedMethod:
    file_path: str
    signatures: List[str]


@dataclass
class Paths:
    work_dir: str
    fixed_dir: str
    src_java_rel: str
    classes_dir: str



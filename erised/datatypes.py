from dataclasses import dataclass
import enum
from typing import Any, Dict, Optional, Tuple


class TaskType(enum.Enum):
    CALL = "call"
    ATTR_GET = "attr_get"
    ATTR_SET = "attr_set"


@dataclass
class Task:
    id: int
    type: TaskType
    attr: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


@dataclass
class Result:
    task_id: int
    value: Any
    exception: Optional[Exception]

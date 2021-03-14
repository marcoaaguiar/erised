import itertools
from dataclasses import dataclass, field
from operator import attrgetter
from typing import Any, Dict, Iterator, Optional, Tuple

_ID_COUNTER: Iterator[int] = itertools.count()


@dataclass
class TaskResult:
    task_id: int
    value: Any
    exception: Optional[Exception]


def _next_task_id():
    return next(_ID_COUNTER)


@dataclass
class Task:
    attr: str
    id: int = field(default_factory=_next_task_id, init=False)

    def do(self, obj: Any) -> TaskResult:
        raise NotImplementedError


@dataclass
class CallTask(Task):
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def do(self, obj: Any) -> TaskResult:
        result = None
        exception = None
        getter = attrgetter(self.attr)

        try:
            target = getter(obj)
            result = target(*self.args, **self.kwargs)
        except Exception as exc:
            exception = exc
            raise exception
        finally:
            return TaskResult(self.id, result, exception)


@dataclass
class GetArgTask(Task):
    name: str

    def do(self, obj: Any) -> TaskResult:
        result = None
        exception = None

        getter = attrgetter(self.attr)
        try:
            target = getter(obj)
            result = getattr(target, self.name)
        except Exception as exc:
            exception = exc
        finally:
            return TaskResult(self.id, result, exception)


@dataclass
class SetArgTask(Task):
    name: str
    value: Any

    def do(self, obj: Any) -> TaskResult:
        result = None
        exception = None

        getter = attrgetter(self.attr)
        try:
            target = getter(obj)
            setattr(target, self.name, self.value)
        except Exception as exc:
            exception = exc
        finally:
            return TaskResult(self.id, result, exception)

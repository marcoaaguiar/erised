import itertools
from multiprocessing import Queue
from typing import Any, Dict, Iterator, Optional, Tuple

from erised.datatypes import Result, Task, TaskType
from erised.future import Future, FutureState
from erised.remote import Remote


class Node:
    __initiated = False

    def __init__(
        self,
        parent: Optional["Node"] = None,
        root: Optional["Node"] = None,
        name: str = "",
    ):
        self.__parent = parent
        self.__root = root
        self.__name = name

        self.__initiated = True

    def __getattr__(self, name: str) -> "Node":
        return Node(
            parent=self,
            name=name,
            root=self if self.__root is None else self.__root,
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if self.__initiated:
            print("__setattr__", self.__path(), self.__name, name, value)
            self.__root.setattr(self.__path(), name, value)
        else:
            self.__dict__[name] = value

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.__root.submit(self.__path(), args, kwargs)

    def __path(self) -> str:
        return (
            f"{self.__parent.__path()}.{self.__name}"
            if self.__parent and self.__parent.__path()
            else self.__name
        )

    def retrieve(self):
        print(self.__name, self.__parent().__path())
        self.__root.getattr(self.__parent.__path(), self.__name)


class Proxy(Node):
    def __init__(self, obj):
        self.__obj = obj
        self.__queue_in: Queue[Result] = Queue()
        self.__queue_out: Queue[Task] = Queue()
        self.__process = Remote(self.__obj, self.__queue_out, self.__queue_in)
        self.__id_counter: Iterator[int] = itertools.count()

        self.__waiting_futures = {}

        self.__process.start()
        super().__init__()

    def _get(self, task_id, timeout=None):
        while True:
            result = self.__queue_in.get(timeout=timeout)

            future = self.__waiting_futures.pop(result.task_id)
            future._state = FutureState.FINISHED
            future._result = result.value
            future._exception = result.exception

            if result.task_id == task_id:
                break
        return result

    def submit(self, attr, args=None, kwargs=None):
        task = self.__create_task(
            task_type=TaskType.CALL,
            attr=attr,
            args=args or tuple(),
            kwargs=kwargs or dict(),
        )
        return self.__create_future(task)

    def setattr(self, attr, name, value):
        task = self.__create_task(
            task_type=TaskType.ATTR_SET,
            attr=attr,
            args=(name, value),
        )
        return self.__create_future(task)

    def getattr(self, attr, name):
        task = self.__create_task(
            task_type=TaskType.ATTR_GET,
            attr=attr,
            args=(name,),
        )
        return self.__create_future(task)

    def __create_task(
        self,
        task_type: TaskType,
        attr: str,
        args: Optional[Tuple[Any, ...]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Task:
        if kwargs is None:
            kwargs = {}

        task = Task(
            next(self.__id_counter),
            type=task_type,
            attr=attr,
            args=args or tuple(),
            kwargs=kwargs or dict(),
        )
        self.__queue_out.put(task)
        return task

    def __create_future(self, task):
        future = Future(task_id=task.id, proxy=self)
        self.__waiting_futures[task.id] = future
        return future

    def terminate(self):
        self.__process.terminate()

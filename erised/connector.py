from __future__ import annotations

import itertools
import multiprocessing as mp
import queue
from typing import Any, Dict, Iterator, Optional, Tuple

from erised.future import Future, FutureState
from erised.remote import run
from erised.task import CallTask, GetAttrTask, SetAttrTask, Task, TaskResult


class Connector:
    def __init__(self, obj: Any):
        self._obj = obj
        self._queue_in: mp.Queue[TaskResult] = mp.Queue()
        self._queue_out: mp.Queue[Task] = mp.Queue()

        self._process = mp.Process(
            target=run,
            kwargs={
                "obj": self._obj,
                "queue_in": self._queue_out,
                "queue_out": self._queue_in,
            },
        )
        self._waiting_futures: Dict[int, Future] = {}

        self._process.start()

    def call(
        self, attr: str, args: Tuple[Any, ...] = None, kwargs: Dict[str, Any] = None
    ) -> Future:
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = {}
        task = CallTask(
            attr=attr,
            args=args or tuple(),
            kwargs=kwargs or dict(),
        )
        self._queue_out.put(task)
        return self._create_future(task.id)

    def setattr(self, attr: str, name: str, value: Any) -> Future:
        task = SetAttrTask(attr=attr, name=name, value=value)
        self._queue_out.put(task)
        return self._create_future(task.id)

    def getattr(self, attr: str, name: str) -> Future:
        task = GetAttrTask(attr=attr, name=name)
        self._queue_out.put(task)
        return self._create_future(task.id)

    def terminate(self):
        self._process.terminate()

    def _create_future(self, task_id: int) -> Future:
        future = Future(task_id=task_id, connector=self)
        self._waiting_futures[task_id] = future
        return future

    def _get(self, task_id: Optional[int] = None, timeout: Optional[int] = None):
        if len(self._waiting_futures) == 0 or (
            task_id is not None
            and not min(self._waiting_futures) <= task_id <= max(self._waiting_futures)
        ):
            raise ValueError(
                f"Task wasn't set to run, or have already been run: task_id = {task_id}"
            )

        while len(self._waiting_futures) > 0:
            task_result = self._queue_in.get(timeout=timeout)

            future = self._waiting_futures.pop(task_result.task_id)
            future._state = FutureState.FINISHED
            future._result = task_result.value
            future._exception = task_result.exception

            if task_result.task_id == task_id:
                return

    def empty_queue(self):
        self._get()


class LocalConnector(Connector):
    def __init__(self, obj):
        self._obj = obj
        self._queue_in: queue.Queue[TaskResult] = queue.Queue()
        self._queue_out: queue.Queue[Task] = queue.Queue()
        self._id_counter: Iterator[int] = itertools.count()

        self._waiting_futures = {}

    def __del__(self):
        self._process_all_waiting_tasks()

    def terminate(self):
        self._process_all_waiting_tasks()

    def _get(self, task_id: int, timeout: Optional[int] = None):
        self._process_all_waiting_tasks()
        super()._get(task_id=task_id, timeout=timeout)

    def _process_all_waiting_tasks(self):
        while not self._queue_out.empty():
            task = self._queue_out.get()
            task_result = task.do(self._obj)
            self._queue_in.put(task_result)

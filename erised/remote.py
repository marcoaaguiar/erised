from __future__ import annotations

import multiprocessing as mp
from typing import Any

from erised.task import Task, TaskResult


def run(obj: Any, queue_in: mp.Queue[Task], queue_out: mp.Queue[TaskResult]) -> None:
    while True:
        task = queue_in.get()
        result = task.do(obj)
        queue_out.put(result)

        if result.exception:
            raise result.exception

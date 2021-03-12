from operator import attrgetter
from erised.datatypes import Result, Task, TaskType
from multiprocessing import Process, Queue


class Remote(Process):
    def __init__(self, obj, in_queue: Queue, out_queue: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.obj = obj
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self) -> None:
        while True:
            task = self.in_queue.get()

            self.process_task(task)

    def process_task(self, task: Task):
        if task.type == TaskType.CALL:
            self.process_task_call(task)
        elif task.type == TaskType.ATTR_GET:
            self.process_task_attr_get(task)
        elif task.type == TaskType.ATTR_SET:
            self.process_task_attr_set(task)
        else:
            raise ValueError(f"TaskType not recognized: {task.type}")

    def process_task_attr_get(self, task: Task):
        result = None
        exc = None

        getter = attrgetter(task.attr)
        try:
            result = getter(self.obj)
        except Exception as exc:
            self.out_queue.put(Result(task.id, result, exc))
            raise exc

    def process_task_attr_set(self, task: Task):
        result = None
        exc = None

        getter = attrgetter(task.attr)
        print(getter(self.obj))
        print("remote", task.attr, task.args)
        try:
            setattr(getter(self.obj), *task.args)
        except Exception as exc:
            raise exc
        finally:
            self.out_queue.put(Result(task.id, result, exc))

    def process_task_call(self, task: Task):
        result = None
        exception = None
        getter = attrgetter(task.attr)

        try:
            result = getter(self.obj)(*task.args, **task.kwargs)
        except Exception as exc:
            exception = exc
            raise exception
        finally:
            self.out_queue.put(Result(task.id, result, exception))

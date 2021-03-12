from __future__ import annotations
from concurrent.futures import CancelledError
from typing import Optional
import typing

from erised.datatypes import Result

if typing.TYPE_CHECKING:
    from erised.proxy import Proxy


class FutureState:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    CANCELLED = "CANCELLED"
    CANCELLED_AND_NOTIFIED = "CANCELLED_AND_NOTIFIED"
    FINISHED = "FINISHED"


class Future:
    def __init__(self, task_id: int, proxy: Proxy):
        self._task_id = task_id
        self._state: str = FutureState.RUNNING
        self._result: Optional[Result] = None
        self._exception: Optional[Exception] = None
        self._proxy = proxy

    def cancelled(self) -> bool:
        """Return True if the future was cancelled."""
        return self._state in [
            FutureState.CANCELLED,
            FutureState.CANCELLED_AND_NOTIFIED,
        ]

    def running(self) -> bool:
        """Return True if the future is currently executing."""
        return self._state == FutureState.RUNNING

    def done(self) -> bool:
        """Return True of the future was cancelled or finished executing."""
        return self._state in [
            FutureState.CANCELLED,
            FutureState.CANCELLED_AND_NOTIFIED,
            FutureState.FINISHED,
        ]

    def _wait_for_result(self, timeout=None):
        if self._state == FutureState.RUNNING:
            self._proxy._get(self._task_id, timeout=timeout)

    def __get_result(self):
        if self._exception:
            raise self._exception
        else:
            return self._result

    def result(self, timeout=None):
        if self._state in [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED]:
            raise CancelledError()
        if self._state in [FutureState.PENDING, FutureState.RUNNING]:
            self._wait_for_result(timeout=timeout)

        return self.__get_result()

    def exception(self, timeout=None):
        if self._state in [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED]:
            raise CancelledError()
        if self._state in [FutureState.PENDING, FutureState.RUNNING]:
            self._wait_for_result(timeout=timeout)
        elif self._state == FutureState.FINISHED:
            return self._exception

from __future__ import annotations

import enum
import typing
from concurrent.futures import CancelledError
from typing import Any, Optional

if typing.TYPE_CHECKING:
    from erised.proxy import Connector


class FutureState(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    CANCELLED = "CANCELLED"
    CANCELLED_AND_NOTIFIED = "CANCELLED_AND_NOTIFIED"
    FINISHED = "FINISHED"


class Future:
    def __init__(self, task_id: int, connector: Connector):
        self._task_id = task_id
        self._state: FutureState = FutureState.RUNNING
        self._result: Optional[Any] = None
        self._exception: Optional[Exception] = None
        self._connector = connector

    def cancel(self) -> bool:
        raise NotImplementedError("Cancelling is not implemented yet")

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

    def _wait_for_result(self, timeout: int = None):
        if self._state in [FutureState.PENDING, FutureState.RUNNING]:
            self._connector._get(self._task_id, timeout=timeout)

    def __get_result(self):
        if self._exception:
            raise self._exception
        else:
            return self._result

    def result(self, timeout: int = None):
        if self._state in [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED]:
            raise CancelledError()

        self._wait_for_result(timeout=timeout)
        return self.__get_result()

    def exception(self, timeout: int = None):
        if self._state in [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED]:
            raise CancelledError()

        self._wait_for_result(timeout=timeout)
        return self._exception

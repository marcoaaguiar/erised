from concurrent.futures import CancelledError

import pytest
from pytest_mock import MockerFixture

from erised.connector import Connector
from erised.task import CallTask, Task
from erised.future import Future, FutureState
from erised.proxy import Proxy


@pytest.fixture
def connector() -> Connector:
    proxy = Proxy(object(), local=True)
    return proxy._Proxy__connector  # type: ignore


@pytest.fixture
def task() -> Task:
    return CallTask("child", ("args",), {})


@pytest.fixture
def future(task: Task, connector: Connector):
    return Future(task.id, connector)


# Tests


def test_cancel(future: Future):
    with pytest.raises(NotImplementedError):
        future.cancel()


@pytest.mark.parametrize(
    "state", [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED]
)
def test_cancelled(future: Future, state: FutureState):
    future._state = state

    assert future.cancelled()


@pytest.mark.parametrize(
    "state",
    (
        state
        for state in FutureState
        if state not in [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED]
    ),
)
def test_not_cancelled(future: Future, state: FutureState):
    future._state = state

    assert not future.cancelled()


def test_running(future: Future):
    future._state = FutureState.RUNNING

    assert future.running()


@pytest.mark.parametrize(
    "state",
    (state for state in FutureState if state != FutureState.RUNNING),
)
def test_not_running(future: Future, state: FutureState):
    future._state = state

    assert not future.running()


@pytest.mark.parametrize(
    "state",
    [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED, FutureState.FINISHED],
)
def test_done(future: Future, state: FutureState):
    future._state = state

    assert future.done()


@pytest.mark.parametrize(
    "state",
    (
        state
        for state in FutureState
        if state
        not in [
            FutureState.CANCELLED,
            FutureState.CANCELLED_AND_NOTIFIED,
            FutureState.FINISHED,
        ]
    ),
)
def test_not_done(future: Future, state: FutureState):
    future._state = state

    assert not future.cancelled()


@pytest.mark.parametrize(
    "state",
    [FutureState.PENDING, FutureState.RUNNING],
)
def test_wait_for_result(future: Future, state: FutureState, mocker: MockerFixture):
    future._state = state
    mocked_get = future._connector._get = mocker.Mock()
    timeout = 42

    future._wait_for_result(timeout)

    mocked_get.assert_called_once_with(future._task_id, timeout=timeout)


@pytest.mark.parametrize(
    "state",
    [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED, FutureState.FINISHED],
)
def test_wait_for_result_dont_get(
    future: Future, state: FutureState, mocker: MockerFixture
):
    future._state = state
    mocked_get = future._connector._get = mocker.Mock()
    timeout = 42

    future._wait_for_result(timeout)

    mocked_get.assert_not_called()


@pytest.mark.parametrize(
    "state",
    [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED],
)
def test_result_cancelled(future: Future, state: FutureState):
    future._state = state

    with pytest.raises(CancelledError):
        future.result()


@pytest.mark.parametrize("state", [FutureState.PENDING, FutureState.RUNNING])
def test_result_pending_or_running(
    future: Future, state: FutureState, mocker: MockerFixture
):
    future._state = state
    wait_for_future = future._wait_for_result = mocker.Mock()
    result = future._result = mocker.Mock()

    assert future.result() is result
    wait_for_future.assert_called_once()


def test_result_finished_success(future: Future, mocker: MockerFixture):
    future._state = FutureState.FINISHED
    result = future._result = mocker.Mock()

    assert future.result() is result


def test_result_finished_raised_exception(future: Future):
    future._state = FutureState.FINISHED
    future._exception = exc = Exception("Test Exception")

    try:
        future.exception()
    except Exception as capture_exc:
        assert capture_exc is exc


@pytest.mark.parametrize(
    "state",
    [FutureState.CANCELLED, FutureState.CANCELLED_AND_NOTIFIED],
)
def test_exception_cancelled(future: Future, state: FutureState):
    future._state = state

    with pytest.raises(CancelledError):
        future.exception()


@pytest.mark.parametrize("state", [FutureState.PENDING, FutureState.RUNNING])
def test_exception_pending_or_running(
    future: Future, state: FutureState, mocker: MockerFixture
):
    future._state = state
    wait_for_future = future._wait_for_result = mocker.Mock()
    exc = future._exception = mocker.Mock()

    assert future.exception() is exc
    wait_for_future.assert_called_once()


def test_exception_finished(future: Future, mocker: MockerFixture):
    future._state = FutureState.FINISHED
    exc = future._exception = mocker.Mock()

    assert future.exception() is exc

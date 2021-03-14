from pytest_mock import MockerFixture
import pytest

from erised.proxy import Proxy


class SomeClass:
    class_param = 32

    def __init__(self, var):
        self.var = var
        self.not_argument = "foo"

    @property
    def a_property(self):
        return "a_property"

    def function(self, number):
        return number + self.var


@pytest.fixture
def obj():
    return SomeClass(5)


@pytest.fixture
def proxy(obj: SomeClass):
    return Proxy(obj, local=True)


def test_init(obj: SomeClass):
    proxy = Proxy(obj)
    assert proxy
    proxy.terminate()


def test_init_local(obj: SomeClass):
    proxy = Proxy(obj, local=True)
    assert proxy


def test_path(obj):
    proxy = Proxy(obj, local=True)

    assert proxy._Proxy__path() == ""
    assert proxy.child.subchild._Proxy__path() == "child.subchild"


def test_getattr(proxy: Proxy):
    assert isinstance(proxy.a_property, Proxy)


def test_getattr_not_exists(proxy: Proxy):
    """
    Since the remote object might mutate creating new attribuets,
    the __getattr__ shouldnt fail for a non existing attr at the proxy
    creation time
    """
    assert isinstance(proxy.non_existing_attr, Proxy)


def test_retrieve_calls_connector(mocker: MockerFixture):
    connector = mocker.Mock()
    connector.getattr = getattr = mocker.Mock()

    proxy = Proxy(
        obj=None,
        _connector=connector,
        _name="",
        _prefix="",
    )  # this shouldnt happen in practice

    proxy.child.var.retrieve()

    getattr.assert_called_once_with("child", "var")


def test_setattr_calls_connector(mocker: MockerFixture):
    connector = mocker.Mock()
    connector.setattr = setattr = mocker.Mock()

    proxy = Proxy(
        obj=None,
        _connector=connector,
        _name="",
        _prefix="",
    )  # this shouldnt happen in practice

    proxy.child.var = 20

    setattr.assert_called_once_with("child", "var", 20)


def test_call_calls_connector(mocker: MockerFixture):
    connector = mocker.Mock()
    connector.submit = submit = mocker.Mock()

    proxy = Proxy(
        obj=None,
        _connector=connector,
        _name="",
        _prefix="",
    )  # this shouldnt happen in practice

    proxy.child.method("some_string", 42, key="value")

    submit.assert_called_once_with(
        "child.method", ("some_string", 42), {"key": "value"}
    )

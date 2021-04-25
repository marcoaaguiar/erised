from __future__ import annotations

from typing import Any, Optional, overload

from erised.connector import Connector, LocalConnector
from erised.future import Future


class Proxy:
    __initiated = False

    @overload
    def __init__(self, obj: Any, *, local: bool = ...):
        ...

    @overload
    def __init__(
        self,
        obj: None,
        *,
        _name: str,
        _prefix: str,
        _connector: Connector,
    ):
        ...

    def __init__(
        self,
        obj: Optional[Any],
        *,
        local: bool = False,
        _name: str = "",
        _prefix: str = "",
        _connector: Optional[Connector] = None,
    ):
        if _connector is None:
            if obj is None:
                raise ValueError("Object can't be None")
            self.__connector = LocalConnector(obj) if local else Connector(obj)
        else:
            self.__connector = _connector

        self.__prefix = _prefix
        self.__name = _name

        self.__initiated = True

    def __getattr__(self, name: str) -> "Proxy":
        return Proxy(
            obj=None,
            _prefix=self.__path(),
            _name=name,
            _connector=self.__connector,
        )

    def __setattr__(self, name: str, value: Any):
        if name.startswith("_Proxy__"):
            self.__dict__[name] = value
        else:
            self.__connector.setattr(self.__path(), name, value)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.__connector.call(self.__path(), args, kwargs)

    def __path(self) -> str:
        return f"{self.__prefix}.{self.__name}" if self.__prefix else self.__name

    def terminate(self):
        self.__connector.terminate()

    def retrieve(self) -> Future:
        return self.__connector.getattr(self.__prefix, self.__name)

    def wait_all_futures(self):
        self.__connector.empty_queue()


from typing import Type

from rqt_py_common.message_helpers import get_message_class
from rosidl_runtime_py import message_to_yaml
from rosidl_runtime_py.utilities import get_service


class Node:
    def __init__(self, name: str, namespace: str = None):
        self._name = name
        self._namespace = namespace

    def __str__(self) -> str:
        if self._namespace not in [None, "", "/"]:
            return f"{self._namespace}/{self._name}"
        else:
            return f"/{self._name}"


class Topic:
    def __init__(self, name: str, t: str):
        self._name = name
        self._type = t
        self._class = get_message_class(self._type)

    def __str__(self) -> str:
        return f"{self._name} [{self._type}]"

    def name(self) -> str:
        return self._name

    def type(self) -> str:
        return self._type


class Service:
    def __init__(self, name: str, t: str):
        self._name = name
        self._type = t
        self._class = get_service(self._type)

        self.default_request_definition: str = message_to_yaml(self.Request())
        self.request_definition = self.default_request_definition

    def __str__(self) -> str:
        return f"{self._name} [{self._type}]"

    def name(self) -> str:
        return self._name

    def type(self) -> str:
        return self._type

    @property
    def Request(self) -> Type[any]:
        return self._class.Request

    @property
    def Response(self) -> Type[any]:
        return self._class.Response

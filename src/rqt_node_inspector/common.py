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

    def __str__(self) -> str:
        return f"{self._name} [{self._type}]"

    def name(self) -> str:
        return self._name

    def type(self) -> str:
        return self._type

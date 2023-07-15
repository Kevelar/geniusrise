from abc import ABCMeta
import os
import importlib
import inspect
import pydantic

from typing import Any, List, Optional, Tuple

from geniusrise.core import Spout


class DiscoveredSpout(pydantic.BaseModel):
    name: str
    klass: type
    methods: List[Tuple[str, List[str], Optional[str]]]
    init_args: dict


class Discover:
    def __init__(self, directory):
        self.directory = directory
        self.classes = {}

    def scan_directory(self):
        for root, _, files in os.walk(self.directory):
            if "__init__.py" in files:
                module = self.import_module(root)
                self.find_classes(module)
        return self.classes

    def import_module(self, path):
        path = path.replace("/", ".")
        module = importlib.import_module(path)
        return module

    def find_classes(self, module):
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Spout) and obj != Spout:
                self.classes[name] = DiscoveredSpout(
                    {
                        "name": name,
                        "klass": obj,
                        "methods": obj.get_methods,
                        "init_args": self.get_init_args(obj),
                    }
                )

    def get_init_args(self, cls):
        init_signature = inspect.signature(cls.__init__)

        init_params = init_signature.parameters
        init_args = {}
        for name, kind in init_params.items():
            if name == "self":
                continue
            if name == "kwargs" or name == "args":
                init_args["kwargs"] = Any
                continue
            if isinstance(kind.annotation, ABCMeta):
                init_args[name] = self.get_init_args(kind.annotation)
            elif kind.annotation == inspect.Parameter.empty:
                init_args[name] = "No type hint provided 😢"
            else:
                init_args[name] = kind.annotation
        return init_args

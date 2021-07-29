"""
https://refactoring.guru/design-patterns/observer/python/example
"""

from __future__ import annotations
from abc import ABC, abstractmethod


class Subject(ABC):
    """
    The Subject interface declares a set of methods for managing subscribers.
    """

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject.
        """
        raise NotImplementedError

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from the subject.
        """
        raise NotImplementedError

    @abstractmethod
    def notify(self) -> None:
        """
        Notify all observers about an event.
        """
        raise NotImplementedError


class Observer(ABC):
    """
    The Observer interface declares the update method, used by subjects.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    @classmethod
    @abstractmethod
    def update(cls, *args, **kwargs) -> None:
        """
        Receive update from subject.
        """
        raise NotImplementedError

    @abstractmethod
    def _update(self, *args, **kwargs) -> None:
        """
        """
        raise NotImplementedError

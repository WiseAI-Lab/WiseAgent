import abc
from typing import Any
from typing import Sequence


class Actor(abc.ABC):
    """Interface for an agent that can act.
    This interface defines an API for an Actor to interact with an Environment

    """

    def capture(self, info: Sequence[Any]):
        """Capture all information from environment.
        """

    def update(self, *args, wait: bool = False, **kwargs):
        """Perform an update of the actor parameters from past observations.
        Args:
          wait: if True, the update will be blocking.
        """


class Worker(abc.ABC):
    """An interface for (potentially) distributed workers."""

    @abc.abstractmethod
    def run(self):
        """Runs the worker."""

    @abc.abstractmethod
    def step(self):
        """Perform an update step of the learner's parameters."""


class Savable(abc.ABC):

    @abc.abstractmethod
    def save(self, value: Any):
        """
            Save a object
        """

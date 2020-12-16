import abc
from queue import PriorityQueue
from typing import TypeVar, Any, Union
from typing import Sequence

from wgent.base_types import Info

T = TypeVar('T')


class Actor(abc.ABC):
    """Interface for an agent that can act.
    This interface defines an API for an Actor to interact with an Environment

    """

    def capture(self, info: Sequence[Info]):
        """Capture all information from environment.
        """

    def update(self, wait: bool = False):
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

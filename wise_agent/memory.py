from queue import Queue
from typing import List, Mapping, Optional, Any

from wise_agent.acl import ACLMessage
from wise_agent.base_types import MemoryPiece
from wise_agent.core import Savable


class MemoryHandler(object):
    """behavior
    Handle the message in memory.
    Suppose some easy function to operate the behaviour.
    """
    @staticmethod
    def generate_memory_from_message(message: ACLMessage,
                                     priority: Optional[int] = 11,
                                     category: Optional[Any] = "test_behavior_category",
                                     behaviors: Optional[List[str]] = None) -> MemoryPiece:
        """
        priority:
        Args:
            message: ACLMessage, a message object
            priority: Optional[int], Default implement to the behaviour.
            category: Optional[Any],
            behaviors: Optional[List[str]], define which behaviour to execute this message.

        Returns: MemoryPiece

        """
        memory_piece = MemoryPiece(observation=None, content=message,
                                   priority=priority, category=category,
                                   executors=behaviors)
        return memory_piece

    @staticmethod
    def wait_and_put(queue: Queue, memory: MemoryPiece, timeout: Optional[float] = None):
        queue.put(tuple([memory.priority, memory]), timeout=timeout)

    @staticmethod
    def wait_and_get(queue: Queue, timeout: Optional[float] = None):
        return queue.get(timeout=timeout)[1]


class MemoryStorage(Savable):
    """
        Save a memory piece to a storage.
    """

    def __init__(self):
        self._memory: Mapping[Any, List[MemoryPiece]] = {}

    def save(self, piece: MemoryPiece):
        """
            Save a memory piece
        """
        if isinstance(piece, MemoryPiece):
            self._memory[piece.category].append(piece)
        else:
            raise ValueError("It's not belong to MemoryPiece")

from queue import Queue
from typing import List, Optional, Any

from wise_agent.acl import ACLMessage
from .types import MemoryPiece


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
        memory_piece = MemoryPiece(message=message,
                                   priority=priority,
                                   category=category,
                                   executors=behaviors)
        return memory_piece

    @staticmethod
    def wait_and_put(queue: Queue, memory: MemoryPiece, timeout: Optional[float] = None):
        queue.put(tuple([memory.priority, memory]), timeout=timeout)

    @staticmethod
    def wait_and_get(queue: Queue, timeout: Optional[float] = None):
        return queue.get(timeout=timeout)[1]


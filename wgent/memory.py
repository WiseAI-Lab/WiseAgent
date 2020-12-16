from queue import Queue
from typing import List, Mapping, Optional

from wgent.acl import ACLMessage
from wgent.base_types import Info, MemoryType, MemoryPiece, TaskPiece
from wgent.core import Savable


class MemoryHandler(object):

    @staticmethod
    def generate_memory_from_message(message: ACLMessage,
                                     priority: Optional[int] = 11,
                                     category: Optional[MemoryType] = MemoryType("test")):
        """
            observation: Info
            content: ACLMessage
            category: MemoryType
            priority: int  # Default implement to the behaviour.
        """
        memory_piece = MemoryPiece(observation=Info(None), content=message, priority=priority, category=category)
        return memory_piece

    def generate_task_for_behaviours(self, behaviors: List[str], message: ACLMessage):
        memory_piece = self.generate_memory_from_message(message)
        task_memory = TaskPiece(memory_piece=memory_piece, executors=behaviors)
        return task_memory

    @staticmethod
    def wait_and_put(queue, task_memory, timeout=None):
        queue.put(tuple([task_memory.memory_piece.priority, task_memory]), timeout=timeout)

    @staticmethod
    def wait_and_get(queue: Queue, timeout=None):
        return queue.get(timeout=timeout)[1]


class MemoryStorage(Savable):
    """
        Save a memory piece to a storage.
    """

    def __init__(self):
        self._memory: Mapping[MemoryType, List[MemoryPiece]] = {}

    def save(self, piece: MemoryPiece):
        """
            Save a memory piece
        """
        if isinstance(piece, MemoryPiece):
            self._memory[piece.category].append(piece)
        else:
            raise ValueError("It's not belong to MemoryPiece")

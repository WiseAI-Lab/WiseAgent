"""Common types used throughout Wgent."""
from typing import NewType, TypeVar, Sequence, NamedTuple, List, Any, Union

from wgent.acl import ACLMessage

Info = NewType("Info", Any)
State = TypeVar("State")
# E.g
# MessageType: Describe which the memory belong to.
MemoryType = NewType("MemoryType", str)


class MemoryPiece(NamedTuple):
    """
        Memory format in the pipe.
    """
    observation: Info
    content: ACLMessage
    category: MemoryType
    priority: int  # Default implement from the behaviour.


class TaskPiece(NamedTuple):
    memory_piece: MemoryPiece
    executors: Union[List[str], None]


class AgentState:
    ALIVE: str = "alive"
    DEAD: str = "dead"
    STOP: str = "stop"
    START: str = "start"
    RUNNING: str = "running"
    agent_statuses: Sequence[str] = [ALIVE, DEAD, RUNNING, STOP]
    agent_operators: Sequence[str] = [STOP, START]

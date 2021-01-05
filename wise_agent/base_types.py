"""Common types used throughout wise_agent."""
from typing import Sequence, NamedTuple, List, Any, Union

from wise_agent.acl import ACLMessage


class MemoryPiece(NamedTuple):
    """
        Memory format in the pipe.
    """
    observation: Any
    content: ACLMessage
    category: Any
    priority: int  # Default derive from the behaviour.
    executors: Union[List[str], None]


class AgentState:
    """
    stop is not running but alive,
    dead is not alive, running and stop
    running is alive and not dead and stop
    alive is not dead, but not ensure whether running or stop
    """
    ALIVE: str = "alive"
    DEAD: str = "dead"

    STOP: str = "stop"
    START: str = "start"
    RUNNING: str = "running"
    agent_statuses: Sequence[str] = [ALIVE, DEAD, RUNNING, STOP]
    agent_operators: Sequence[str] = [STOP, START]

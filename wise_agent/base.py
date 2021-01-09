from queue import PriorityQueue
from typing import Union, Optional

from wise_agent.acl import AID
from wise_agent.base_types import AgentState
from wise_agent.config import ConfigHandler
from wise_agent.core import Actor
from wise_agent.memory import MemoryHandler


class Agent_(Actor):
    """
        An agent, which have some basic property.
    """

    def __init__(self, aid: Union[AID, str]):
        self._aid: Union[AID, str] = aid  # Identifier
        self._status: str = AgentState.DEAD  # Represent the Agent State
        # Actually the agent should place their memory in brain, but I define the brain outside
        # this class because the brain is a thinking behaviour in 'wise_agent'.
        self.config_handler: Optional[ConfigHandler, None] = None
        self.memory_pieces_queue: PriorityQueue = PriorityQueue(maxsize=100)  # Delivery any message in agent.
        self.memory_handler = MemoryHandler()  # Some function to handle the memory in agent.

    @property
    def aid(self):
        """
        AID getter

        Returns: aid
        """
        return self._aid

    @aid.setter
    def aid(self, value: AID):
        """
        AID setter

        Args:
            value: AID

        Returns: None

        Raises:
            ValueError, aid should be 'AID' object.
        """
        if isinstance(value, AID):
            self._aid = value
        else:
            raise ValueError('aid object type must be AID!')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        """
            status setter
        """
        if value in AgentState.agent_statuses:
            self._status = value
        else:
            raise ValueError('status must belong to the status list!')

    def on_start(self, *args, **kwargs):
        """
            Init an agent.
        """

    def send(self, *args, **kwargs):
        """
            A send function and it will different between agents.
        """

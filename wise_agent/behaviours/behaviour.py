from asyncio import Future
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Dict, Optional

from wise_agent import core
from wise_agent.acl import ACLMessage
from wise_agent.base import Agent_


class Behaviour(core.Worker):
    """
        Class that states essential methods of a behaviour.
        All behaviours should inherit from this class.

    """
    internal = "internal"
    external = "external"
    parts = [internal, external]

    def __init__(self, agent: Agent_):
        """This method initializes the Behaviour class with an agent instance

            :param agent: agent instance that will execute the behaviours
            established by the protocol

        """
        self.agent: Agent_ = agent
        self.part: str = self.internal
        self.is_daemon = False
        # Define which size the pool are.
        cur_config = self.agent.config_handler.config.get("behaviours").get(self.__class__.__name__)
        self.pool_size = cur_config.get("pool_size")
        # Default pool
        self.is_process_pool = cur_config.get("is_process_pool")
        if self.is_process_pool:
            self._tasks_pool = ProcessPoolExecutor(
                max_workers=self.pool_size)
        else:
            self._tasks_pool = ThreadPoolExecutor(
                max_workers=self.pool_size, thread_name_prefix='behaviour_')

        self._running_tasks: Dict[str, Future] = {}

    def execute(self, message: ACLMessage):
        """
            For each type of message received.
        """

    def __str__(self):
        return self.__class__.__name__

    def name(self):
        return str(self)

    def step(self, *args, **kwargs):
        """
            Just like a iterable.
        """

    def run(self, *args, **kwargs):
        """
            When the process run in a daemon or other way, the logic code is here
        """

    def on_start(self, *args, **kwargs):
        """
            Init a Behaviour Function
            Init, but not run
        """


class InternalBehaviour(Behaviour):
    """
        A Internal Behaviour
    """

    def __init__(self, agent: Agent_):
        super(InternalBehaviour, self).__init__(agent)
        self.part = Behaviour.internal  # default internal


class ExternalBehaviour(Behaviour):
    """
        A External Behaviour
    """

    def __init__(self, agent: Agent_):
        super(ExternalBehaviour, self).__init__(agent)
        self.part = Behaviour.external  # default external

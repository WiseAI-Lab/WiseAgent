import queue
from functools import wraps

from wgent import core
from wgent.acl import ACLMessage
from wgent.base import Agent_


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


# def async_behaviour(fun):
#     @wraps(fun)
#     def wrapper(self, *args, **kwargs):  # add async definition
#         self.is_daemon = True  # Change the daemon property.
#         fun(self, *args, **kwargs)
#
#     return wrapper

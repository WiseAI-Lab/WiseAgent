"""
Behavier is a important part of agent.
"""
import abc
from threading import Timer

from wgent.acl import Filter
from wgent import Agent
from wgent.acl import ACLMessage
from wgent.utility import AgentStoppedError


class Behaviour(abc.ABC):
    """
        Class that states essential methods of a behaviour.
        All behaviours should inherit from this class.

    """

    def __init__(self, agent: Agent) -> None:
        """This method initializes the Behaviour class with an agent instance

            :param agent: agent instance that will execute the behaviours
            established by the protocol

        """
        self.agent = agent

    def execute(self, message: ACLMessage) -> None:
        """Executes the actual behaviour of the protocol
            for each type of messege received.
        """

    def on_start(self) -> None:
        """Always executed when the protocol is initialized
        """


class TimedBehaviour(Behaviour):
    """Class that implements timed behaviours
    """

    def __init__(self, agent: Agent, time: int):
        """ Initialize method
        """
        super(TimedBehaviour, self).__init__(agent)
        self.time = time
        self.timer = None

        self.filter_self = Filter()
        self.filter_self.set_sender(self.agent.aid)

    def on_start(self) -> None:
        """This method overrides the on_start method from Behaviour class
            and implements aditional settings to the initialize method of TimedBehaviour behaviour.
        """
        Behaviour.on_start(self)
        self.timed_behaviour()

    def timed_behaviour(self) -> None:
        """This method is always used when the implemented behaviour
            needs timed restrictions.
            In this case, it uses the twisted callLater method, which
            receives a method and delay as parameters to be executed

        """
        self.timer = Timer(self.time, self.on_time)
        self.timer.start()

    def on_time(self) -> None:
        """This method executes the handle_all_proposes method if any
            FIPA_CFP message sent by the agent does not get an answer.
        """
        if self.agent.stopped:
            self.timer.cancel()
            raise AgentStoppedError("Timed Behaviour stop...")
        self.timer.run()

    def execute(self, message) -> None:
        super(TimedBehaviour, self).execute(message)
        if self.filter_self.filter(message):
            return

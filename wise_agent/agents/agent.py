from typing import Union, List, Mapping, Optional
from wise_agent.acl import AID
from wise_agent.behaviours.brain import BrainBehaviour
from wise_agent.behaviours import Behaviour
import asyncio
from wise_agent import base
from wise_agent.base_types import MemoryPiece


class Agent(base.Agent_):
    """
        An agent, which have a brain to thinking.
    """
    # Agent alive when it have brain.
    brain_behaviour: Optional[BrainBehaviour] = None
    transport_behaviour = None

    def __init__(self, aid: Union[AID, str]):
        super(Agent, self).__init__(aid)
        # The behaviours are split two styles such as the people.
        self._behaviours: Mapping[str, List[Behaviour]] = {Behaviour.internal: [],
                                                           Behaviour.external: []}  # Record all behaviours
        # Agent have property such as the game's role.

    @property
    def behaviours(self) -> List[Behaviour]:
        """
        Return the table with a List.

        Returns: List[Behaviour]

        """
        new_arr: List[Behaviour] = []
        for _, behaviours in self._behaviours.items():
            new_arr.extend(behaviours)
        return new_arr

    def add_behaviours(self, behaviours: List[Behaviour]):
        """Summary

        Parameters
        ----------
        behaviours : List[Behaviour]

        Raises
        ------
        ValueError
            Description
        """
        for v in behaviours:
            if not issubclass(v.__class__, Behaviour):
                raise ValueError(
                    'behaviour must be a subclass of the Behaviour class!')
            else:
                self._behaviours[v.part].append(v)

    def react(self, *args, **kwargs):
        """
            TODO: A agent react in brain but not define now.

        Returns:

        """

    def send(self, memory: MemoryPiece, is_outside=False):
        """
        Send a memory.

        Args:
            memory: MemoryPiece
            is_outside: Boolean

        Returns: None

        """
        self.memory_handler.wait_and_put(self.memory_pieces_queue, memory)
        # In online Agent, the task possible send outside to other agent.
        if is_outside and self.transport_behaviour:
            message = memory.content
            message.set_sender(self.aid)
            message.set_datetime_now()
            self.transport_behaviour.push(message)

    def on_start(self):
        """
        Init an agent.
        You can define the basic behaviour for your agent and add it to 'Agent.behaviours' to manage.
        You can define a loop behaviour like 'DaemonBehaviour' in example used by 'asyncio' so as
        the 'Agent.on_start()', it shouldn't block before the 'asyncio.run(...)'.

        Remember the super()... in your definition!!!

        Example:

        def on_start(self):
            # Define your behaviours before
            # And place the super() to the end.
            super(DefinedAgent, self).on_start()

        Returns: Any

        """
        # Check brain first
        if self.brain_behaviour is None:
            raise ValueError("Agent should have a brain behaviour.")
        self.brain_behaviour = self.brain_behaviour(self)

        # Check the behaviours second
        daemon_tasks: List[Behaviour] = []
        for behaviour in self.behaviours:
            if behaviour.is_daemon:
                behaviour.on_start()
                daemon_tasks.append(behaviour)
            else:
                behaviour.on_start()
        if self.transport_behaviour is not None:
            self.transport_behaviour = self.transport_behaviour(self)  # use kafka to be the transport.
            self.add_behaviours([self.transport_behaviour])
        # Add brain behaviour
        self.add_behaviours([self.brain_behaviour])
        # Run brain behaviour in async.
        asyncio.run(self.brain_behaviour.on_start(daemon_tasks))

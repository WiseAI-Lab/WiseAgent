from typing import Union, List, Mapping, Optional
from wgent.acl import AID, ACLMessage
from wgent.brain import BrainBehaviour
from wgent.config import ConfigHandler
from wgent.behaviours import Behaviour
import asyncio
from wgent import base
from wgent.base_types import TaskPiece


class Agent(base.Agent_):
    """
        An agent, which have a brain to thinking.
    """

    def __init__(self, aid: Union[AID, str]):
        super(Agent, self).__init__(aid)
        # The behaviours are split two styles such as the people.
        self._behaviours: Mapping[str, List[Behaviour]] = {Behaviour.internal: [],
                                                           Behaviour.external: []}  # Record all behaviours
        # Agent have property such as the game's role.
        self.config_handler = ConfigHandler()
        # Agent alive when it have brain.
        self.brain_behaviour: Optional[Behaviour] = None

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

    def send(self, task: TaskPiece):
        """
        Send a task.

        Args:
            task: TaskPiece

        Returns: None

        """

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
        # Check the behaviours first
        daemon_tasks: List[Behaviour] = []
        for behaviour in self.behaviours:
            if behaviour.is_daemon:
                behaviour.on_start()
                daemon_tasks.append(behaviour)
            else:
                behaviour.on_start()

        self.brain_behaviour = BrainBehaviour(self)
        # Add brain behaviour
        self.add_behaviours([self.brain_behaviour])
        # Run brain behaviour in async.
        asyncio.run(self.brain_behaviour.on_start(daemon_tasks))

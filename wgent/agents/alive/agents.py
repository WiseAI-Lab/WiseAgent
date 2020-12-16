"""
    Alive agent Definition.
"""

from wgent.acl import AID
from wgent.agents import agent
from typing import Union

from wgent.base_types import TaskPiece
from wgent.behaviours.transport import ConfluentKafkaTransportBehaviour


class OfflineAgent(agent.Agent):
    """
        Only do some task offline.
    """

    def __init__(self, aid: Union[AID, str]):
        super(OfflineAgent, self).__init__(aid)

    def on_start(self):
        """
            Maybe you can do something here.
        """
        super(OfflineAgent, self).on_start()

    def send(self, task: TaskPiece):
        """
        In offline Agent, the task will only execute among this agent's behaviour.

        Args:
            task: TaskPiece, the 'Memory' will encompass in a 'TaskPiece'.

        Returns: None

        """
        # Take it into memory ana execute inside.
        self.memory_handler.wait_and_put(self.memory_pieces_queue, task)


class OnlineAgent(agent.Agent):
    """
        Only do some task online and it default contains the Transport Behaviour.
    """
    transport_behaviour = ConfluentKafkaTransportBehaviour

    def __init__(self, aid: Union[AID, str]):
        super(OnlineAgent, self).__init__(aid)

    def on_start(self):
        """
        When current agent is on start, the transport behaviour will start along with it.

        Returns: None

        """
        # start the transport
        # You can define your transport behaviour and change the 'self.transport_behaviour'.
        self.transport_behaviour = self.transport_behaviour(self)  # use kafka to be the transport.
        self.add_behaviours([self.transport_behaviour])
        # Start the brain behaviour
        super(OnlineAgent, self).on_start()

    def send(self, task: TaskPiece, is_outside: bool = False):
        """
        In online Agent, the task will execute among this agent's behaviour and
            if 'is_outside' is True that it send the message which in task to
            the 'ACLMessage.receivers' through the self.transport.

        Args:
            task: TaskPiece, the 'Memory' will encompass in a 'TaskPiece'.
            is_outside: bool, whether send the message to other agent.

        Returns: None

        """
        # Take it into memory ana execute inside.
        self.memory_handler.wait_and_put(self.memory_pieces_queue, task)
        # In online Agent, the task possible send outside to other agent.
        if is_outside:
            message = task.memory_piece.content
            message.set_sender(self.aid)
            message.set_datetime_now()
            self.transport_behaviour.push(message)

import asyncio
import time
from typing import Any, Tuple
from wise_agent.acl.messages import MessageType
from wise_agent.agents.agent import Agent
from wise_agent.acl import AID, ACLMessage
from wise_agent.behaviours import InternalBehaviour
from wise_agent.behaviours.brain.visbb.FlaskVisualizationBrainBehaviour.behaviour import \
    FlaskVisualizationBrainBehaviour
from wise_agent.memory import MemoryHandler


# Define behaviour.
class OnceBehaviour(InternalBehaviour):
    """
        Only execute one time, not a daemon behaviour.
    """

    def __init__(self, agent):
        super(OnceBehaviour, self).__init__(agent)
        self.memory_handler = MemoryHandler()

    def execute(self, message: ACLMessage):
        print(f"I am OnceBehaviour and I receive this task to do:\n"
              f"Time: {time.time()}, message id: {message.conversation_id}")

    def step(self):
        """
            A example step to define a task that send a message to self and solve in function 'execute'
        """
        message = ACLMessage(MessageType.REQUEST)
        task = self.memory_handler.generate_memory_from_message(message, behaviors=[self.name()])
        self.agent.send(task)

    def run(self):
        # Only Do once time.
        self.step()


class DaemonBehaviour(InternalBehaviour):
    def __init__(self, agent):
        super(DaemonBehaviour, self).__init__(agent)
        self.is_daemon = True
        self.memory_handler = MemoryHandler()

    def execute(self, message: ACLMessage):
        print(f"I am Daemon and I receive this message to do:\n"
              f"Time: {time.time()}, message id: {message.conversation_id}")

    def step(self):
        """
            Step should not be async cause it will execute in once process,
            but you can set the Exception to except the await
        """
        print("I am a daemon behaviour and send a message")
        message = ACLMessage(MessageType.REQUEST)
        task = self.memory_handler.generate_memory_from_message(message, behaviors=[self.name()])
        self.agent.send(task)

    async def run(self, *args, **kwargs):
        """
            A daemon function should be async otherwise it will throw the exception from asyncio.
        """
        while True:
            # Run 'step' once 5 seconds.
            await asyncio.sleep(5)
            self.step()


class AgentTestOnline(Agent):
    """
        Implement the OnlineAgent and default transport is confluent-kafka.
    """

    def __init__(self, aid):
        super(AgentTestOnline, self).__init__(aid)

    def on_start(self):
        self.add_behaviours([OnceBehaviour(self), DaemonBehaviour(self)])
        super(AgentTestOnline, self).on_start()


class RuledAgentOnline(Agent):
    """
        Implement the OnlineAgent and default transport is confluent-kafka.
    """

    def __init__(self, aid):
        super(RuledAgentOnline, self).__init__(aid)
        self.sensors = {
            'temperature_sensor': ...,
            # ...
        }
        self.temperature_sensor = None
        self.mqtt_config = {
            'host': ...,
            'port': ...,
            'topic': ...
        }
        self.mqtt_consumer = None

    def update(self, sensor: Tuple[str, Any], wait: bool = False):
        if sensor[0] in self.sensors.keys():
            pass
        super(RuledAgentOnline, self).update()

    def operate(self):
        ...

    def capture(self, info):
        """

        Args:
            info:

        Returns:

        """
        ...

    def on_start(self):
        self.add_behaviours([OnceBehaviour(self), DaemonBehaviour(self)])
        super(RuledAgentOnline, self).on_start()


class AgentTestOffline(Agent):
    """
        Implement the OfflineAgent that it cannot contract other agents.
    """

    def __init__(self, aid):
        super(AgentTestOffline, self).__init__(aid)

    def on_start(self):
        """
        Returns: None

        """
        self.add_behaviours([OnceBehaviour(self), DaemonBehaviour(self)])
        super(AgentTestOffline, self).on_start()


if __name__ == '__main__':
    aid = AID.create_offline_aid()
    a1 = AgentTestOffline(aid)
    # # Define the brain behaviour
    a1.brain_behaviour = FlaskVisualizationBrainBehaviour
    # # Define the transport behaviour
    # # a1.transport_behaviour = ConfluentKafkaTransportBehaviour
    a1.on_start()

"""
    Example: Agent take an message behaviours
"""
from wgent.core.agent import Agent
from wgent.utility import start_loop


class KafkaAgent_2(Agent):
    def __init__(self):
        name = 'test_3@localhost:9092@test'
        super(KafkaAgent_2, self).__init__(name)


a2 = KafkaAgent_2()
a2.debug = True

agents = [a2]
while True:
    start_loop(agents)
# agent.behaviours.append([self])

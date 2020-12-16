"""
    Example: Agent take an message behaviours
"""
from agents.agent import Agent
from wgent.utility import start_loop


class KafkaAgent_2(Agent):
    def __init__(self):
        name = 'test_2@localhost:32769@topic1'
        super(KafkaAgent_2, self).__init__(name)


a2 = KafkaAgent_2()
a2.debug = True
start_loop(a2)

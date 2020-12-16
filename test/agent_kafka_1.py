from agents.agent import Agent
from wgent.utility import start_loop


class KafkaAgent_1(Agent):
    def __init__(self):
        name = 'test_1@115.159.153.135:32769@topic1'
        super(KafkaAgent_1, self).__init__(name)


# class KafkaAgent_2(Agent):
#     def __init__(self):
#         name = 'test_2@localhost:32769@topic1'
#         super(KafkaAgent_2, self).__init__(name)
#
#
# a2 = KafkaAgent_2()
# a2.debug = True
a1 = KafkaAgent_1()
a1.debug = True
start_loop([a1])

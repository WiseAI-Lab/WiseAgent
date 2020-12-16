"""
    Example: Agent take an message behaviours
"""
from wgent.acl.messages import ACLMessage
from agents.agent import Agent_
from wgent.utility import start_loop
from wgent.behaviours.normal.protocols import FipaRequestProtocol


class MainAgent(Agent_):
    def __init__(self):
        name = 'main@localhost:32769@topic1'
        super(MainAgent, self).__init__(name)


class InformAllAgentsClose(FipaRequestProtocol):
    def __init__(self, agent):
        super(InformAllAgentsClose, self).__init__(agent)
        self.agent = agent

    def on_start(self):
        acl = ACLMessage(ACLMessage.INFORM)
        acl.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
        acl.content = self.agent.START
        self.agent.send(acl)

    def execute(self, message):
        super(InformAllAgentsClose, self).execute(message)


a3 = MainAgent()
a3.debug = True
system_b = InformAllAgentsClose(a3)
a3.system_behaviours.append(system_b)
start_loop(a3)

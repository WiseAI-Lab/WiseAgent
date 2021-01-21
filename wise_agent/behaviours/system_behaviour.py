import random
from datetime import datetime
from pickle import dumps, loads

from terminaltables import AsciiTable
from twisted.internet import reactor

from wise_agent.core.types import AgentInfo
from wise_agent.acl import ACLMessage
from wise_agent.misc.utility import display_message, logger
from .protocols import FipaSubscribeProtocol, FipaRequestProtocol, TimedBehaviour


class SubscribeBehaviour(FipaSubscribeProtocol):
    """
    This class implements the behaviour of the
    agent that identifies it to the AMS.
    """

    def __init__(self, agent, message):
        """Summary

        Parameters
        ----------
        agent : TYPE
            Description
        message : TYPE
            Description
        """
        super(SubscribeBehaviour, self).__init__(agent,
                                                 message,
                                                 is_initiator=True)

    def handle_agree(self, message):
        """Summary

        Parameters
        ----------
        message : TYPE
            Description
        """
        display_message(self.agent.aid.name, 'Identification process done.')

    def handle_refuse(self, message):
        """Summary

        Parameters
        ----------
        message : TYPE
            Description
        """
        if self.agent.debug:
            display_message(self.agent.aid.name, message.content)

    def handle_inform(self, message):
        """Summary

        Parameters
        ----------
        message : TYPE
            Description
        """
        if self.agent.debug:
            display_message(self.agent.aid.name, 'Table update')
        self.agent.agent_factory.table = loads(message.content)


class CompConnection(FipaRequestProtocol):
    """
    This class implements the agent's behaviour
    that answers the solicitations the AMS
    makes to detect if the agent is connected or not.
    """

    def __init__(self, agent):
        """Summary

        Parameters
        ----------
        agent : TYPE
            Description
        """
        super(CompConnection, self).__init__(agent=agent,
                                             message=None,
                                             is_initiator=False)

    def handle_request(self, message):
        """Summary

        Parameters
        ----------
        message : TYPE
            Description
        """
        super(CompConnection, self).handle_request(message)
        if self.agent.debug:
            display_message(self.agent.aid.localname, 'request message received')
        reply = message.create_reply()
        reply.set_performative(ACLMessage.INFORM)
        reply.set_content(f"{self.agent.aid} still alive")
        reactor.callLater(random.uniform(0.0, 1.0), self.agent.send, reply)


class ComportSendConnMessages(TimedBehaviour):
    def __init__(self, agent, message, time):
        super(ComportSendConnMessages, self).__init__(agent, time)
        self.message = message

    def on_time(self):
        super(ComportSendConnMessages, self).on_time()
        self.agent.add_all(self.message)
        self.agent.send(self.message)
        if self.agent.debug:
            display_message(self.agent.aid.name, 'Checking connection...')


# Behaviour that verifies the answer time of the agents
# and decides whether to disconnect them or not.

class ComportVerifyConnTimed(TimedBehaviour):
    def __init__(self, agent, time):
        super(ComportVerifyConnTimed, self).__init__(agent, time)

    def on_time(self):
        super(ComportVerifyConnTimed, self).on_time()
        table = list([['agent', 'delta']])
        for agent in self.agent.agent_factory.table.values():
            agent_name = agent.name
            date = agent.delta
            now = datetime.now()
            delta = now - date
            table.append([agent_name, str(delta.total_seconds())])
            if delta.total_seconds() > 20.0:
                self.agent.agent_factory.table.delete(agent_name)
                display_message(self.agent.aid.name, 'Agent {} disconnected.'.format(agent_name))

        if self.agent.debug:
            display_message(self.agent.aid.name, 'Calculating response time of the agents...')
            table = AsciiTable(table)
            logger.info(table.table)


class CompConnectionVerify(FipaRequestProtocol):
    """FIPA Request Behaviour of the Clock agent.
    """

    def __init__(self, agent, message):
        super(CompConnectionVerify, self).__init__(agent=agent,
                                                   message=message,
                                                   is_initiator=True)

    def handle_inform(self, message):
        if self.agent.debug:
            display_message(self.agent.aid.name, message.content)
        date = datetime.now()
        agent = self.agent.agent_factory.table.get(name=message.sender.name)
        agent._replace(delta=date)
        self.agent.agent_factory.table.update(message.sender.name, agent)


class PublisherBehaviour(FipaSubscribeProtocol):
    """
    FipaSubscribe behaviour of Publisher type that implements
    a publisher-subscriber communication, which has the AMS agent
    as the publisher and the agents of the plataform as subscribers.
    Two procedures are implemented in this behaviour:
        - The first one is the identification procedure, which
          verifies the availability in the database and stores it
          if positive.
        - The second one is the updating procedure, which updates the
          distributed tables that contain the adresses of the agents
          in the pleteform. It is updated every time that an agent
          enters or leaves the network."""

    STATE = 0

    def __init__(self, agent):
        super(PublisherBehaviour, self).__init__(agent,
                                                 message=None,
                                                 is_initiator=False)

    def handle_subscribe(self, message):

        sender = message.sender

        if self.agent.agent_factory.table.get(sender):
            display_message(self.agent.aid.name,
                            'Failure when Identifying agent ' + sender.name)

            # prepares the answer message
            reply = message.create_reply()
            reply.set_content(
                'There is already an agent with this identifier. Please, choose another one.')
            # sends the message
            self.agent.send(reply)
        else:
            # registers the agent in the database.
            agent_info = AgentInfo(name=sender.name,
                                   host=sender.host,
                                   port=sender.port,
                                   delta=datetime.now())
            # registers the agent in the table of agents
            self.agent.agent_factory.table.add(agent_info)
            # registers the agent as a subscriber in the protocol.
            self.register(message.sender)
            display_message(
                self.agent.aid.name, 'Agent ' + sender.name + ' successfully identified.')

            # prepares and sends answer messages to the agent
            reply = message.create_reply()
            reply.set_performative(ACLMessage.AGREE)
            reply.set_content(
                'Agent successfully identified.')
            self.agent.send(reply)

            # prepares and sends the update message to
            # all registered agents.
            if self.STATE == 0:
                reactor.callLater(10.0, self.notify)
                self.STATE = 1

    def handle_cancel(self, message):
        self.deregister(self, message.sender)
        display_message(self.agent.aid.name, message.content)

    def notify(self):
        message = ACLMessage(ACLMessage.INFORM)
        message.set_protocol(ACLMessage.FIPA_SUBSCRIBE_PROTOCOL)
        message.set_content(dumps(self.agent.agent_factory.table.values()))
        message.set_system_message(is_system_message=True)
        self.STATE = 0
        super(PublisherBehaviour, self).notify(message)

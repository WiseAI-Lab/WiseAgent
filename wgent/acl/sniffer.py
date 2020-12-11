import logging

from wgent.acl.messages import ACLMessage
from wgent.behaviours.protocols import FipaRequestProtocol, TimedBehaviour
from wgent import Agent
from wgent.utility import display_message


class SnifferTimedBehaviour(TimedBehaviour):
    """
        Check agent if alive to update their status
    """

    def __init__(self, agent, time):
        super(SnifferTimedBehaviour, self).__init__(agent, time)

    def on_start(self):
        super(SnifferTimedBehaviour, self).on_start()

    def on_time(self):
        acl = ACLMessage()
        acl.set_performative(ACLMessage.REQUEST)
        acl.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
        acl.set_content("Check Status")
        self.agent.send(acl)


class SnifferCompConnection(FipaRequestProtocol):
    """
    This class implements the agent's behaviour
    that answers the solicitations the AMS
    makes to detect if the agent is connected or not.
    Default behaviour for each agent to manage the agent's status
    """

    def __init__(self, agent):
        """Summary

        Parameters
        ----------
        agent : TYPE
            Description
        """
        super(SnifferCompConnection, self).__init__(agent=agent,
                                                    message=None,
                                                    is_initiator=False)

    def handle_request(self, message):
        """Summary

        Parameters
        ----------
        message : TYPE
            Description
        """
        super(SnifferCompConnection, self).handle_request(message)
        if self.agent.debug:
            display_message(self.agent.aid.localname, 'request message received')
        # reply = message.create_reply()
        # reply.set_performative(ACLMessage.INFORM)
        # reply.set_content('Im Live')
        # self.agent.send(reply)

    def handle_inform(self, message):
        super(SnifferCompConnection, self).handle_inform(message)
        try:
            reply_list = message.reply_to

            # update table
            name, server, topic = message.sender.split('@')
            if name not in self.agent.agent_instance.table.keys():
                self.agent.agent_instance.table[name] = (server, topic)
                print("Update {}'s Table to {}".format(self.agent.aid, self.agent.agent_instance.table))
            else:
                print("Do not need to update table")
        except Exception as e:
            logging.info(e)

    def on_start(self):
        # It is a sniffer
        pass


class Sniffer(Agent):
    """
        NETWORK INSPECT
    """

    def __init__(self):
        name = 'sniffer@localhost:9092@test'
        super(Sniffer, self).__init__(name)

    def on_start(self):
        self.con = SnifferCompConnection(self)
        self.behaviours.append(self.con)
        super(Sniffer, self).on_start()
        self.agent_instance.start()

    def update_agent_to_db(self):
        """
            Update agent to db
        :return:
        """

    def update_msg_to_db(self):
        """
            Update message to db
        :return:
        """


def start_sniffer():
    a = Sniffer()
    a.on_start()


if __name__ == '__main__':
    start_sniffer()

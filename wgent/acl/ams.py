"""
Ams
"""
import logging
from wgent.acl.messages import ACLMessage

from wgent.behaviours.protocols import FipaRequestProtocol
from wgent.core.agent import Agent_
from wgent.utility import display_message


class AmsCompConnection(FipaRequestProtocol):
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
        super(AmsCompConnection, self).__init__(agent=agent,
                                                message=None,
                                                is_initiator=False)

    def handle_request(self, message):
        """Summary

        Parameters
        ----------
        message : TYPE
            Description
        """
        super(AmsCompConnection, self).handle_request(message)
        if self.agent.debug:
            display_message(self.agent.aid.localname, 'request message received')

    def handle_inform(self, message):
        super(AmsCompConnection, self).handle_inform(message)
        try:
            # update table
            name, server, topic = message.sender.split('@')
            if name not in self.agent.agent_instance.table.keys():
                self.agent.agent_instance.table[name] = (server, topic)
                print("Update {}'s Table to {}".format(self.agent.aid, self.agent.agent_instance.table))
            else:
                print("Do not need to update table")
        except Exception as e:
            logging.info(e)


class Ams(Agent_):
    """
        NETWORK INSPECT
    """

    def __init__(self):
        name = 'ams@localhost:9092@test'
        super(Ams, self).__init__(name)

    def on_start(self):
        self.con = AmsCompConnection(self)
        self.behaviours.append(self.con)
        super(Ams, self).on_start()
        self.agent_instance.start()

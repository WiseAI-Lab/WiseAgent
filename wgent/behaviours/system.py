#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   system.py    
@Contact :   sfreebobo@163.com
@License :   (C)Copyright 2020-2021

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2020/12/10 20:39   bobo      1.0         None
'''

# ---------------------System Behaviours-----------------------
import copy
import time

from wgent.acl import Filter
from wgent.acl.messages import ACLMessage
from wgent.behaviours.base import TimedBehaviour
from wgent.behaviours.protocols import FipaRequestProtocol
from wgent.utility import logger, AgentStoppedError


class CompConnection(FipaRequestProtocol):
    """
    1. Default behaviour for each agent is to manage the agent's status
    2. Update agent's config
    3. Add new behaviour for agent ? (So I can know all method in Agent Class ?)
    4. ...

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

        self.status_operators = self.agent.status_operators

    def handle_inform(self, message):
        """
            Solve message from system.
        :param message:
        :return:
        """
        super(CompConnection, self).handle_inform(message)
        # 1. 判断通知是否符合加密规则
        content = message.content
        if content in self.status_operators:
            if content == self.agent.START:
                # 2. Start Agent (Reload all behaviour)
                self.agent.restart()
            elif content == self.agent.STOP:
                # 3. Stop Agent (Stop all normal behaviours)
                self.agent.stop()
            else:
                pass
            logger.debug("Agent {}...".format(self.agent.status))

    def on_start(self):
        """

        :return:
        """
        acl = ACLMessage(ACLMessage.INFORM)  # INFORM
        acl.set_protocol(ACLMessage.FIPA_CONTRACT_NET_PROTOCOL)  # Online
        self.agent.send(acl)

    def execute(self, message):
        super(CompConnection, self).execute(message)


class HeartbeatBehaviour(TimedBehaviour):
    def __init__(self, agent, time):
        super(HeartbeatBehaviour, self).__init__(agent, time)
        self.time_out = 10
        self.filter_heartbeat = Filter()
        self.filter_heartbeat.set_performative(ACLMessage.HEARTBEAT)
        self.filter_heartbeat.set_sender(agent.aid)

    def execute(self, message):
        super(HeartbeatBehaviour, self).execute(message)
        # ACLMessage.HEARTBEAT
        if self.filter_heartbeat.filter(message):
            self.handle_heartbeat(message)

    def handle_heartbeat(self, message):
        """
            Handle the heartbeat event
        :param message:
        :return:
        """
        # 1.check sender and update the status in table
        receiver_str = str()
        for receiver in message.receivers:
            receiver_str += receiver + '-'
        res = '[MESSAGE RECEIVED]', message.performative, 'FROM', message.sender, 'TO', receiver_str
        logger.info(res)
        flag = self.agent.update_table_by_acl(message)
        if flag:
            logger.info("New Agent Online: ", self.agent.agent_instance.table)
            logger.info("Update Table to: {}".format(self.agent.agent_instance.table))

    def timed_behaviour(self):
        super(HeartbeatBehaviour, self).timed_behaviour()

    def on_time(self):
        """
            timer to check all state in table
        :return:
        """
        # Check if timeout occur in table, ('localhost:9092', 'test', 'alive', '154236541654')
        try:
            if not self.agent.stopped:
                self.update_status_in_table()
                self.send_heartbeat_info()
                super(HeartbeatBehaviour, self).on_time()
        except AgentStoppedError:
            logger.info("Agent stop normal behaviours.")
        except Exception as e:
            logger.exception(e)

    def update_status_in_table(self):
        """
            Check all status of agent in table.
        :return:
        """
        table = self.agent.agent_instance.table
        for name, value in table.items():
            # !!! Don't update yourself status if in the table
            # 1.Initial all property
            new_value = list(copy.copy(value))
            last_time = int(value[-1])
            now = int(time.time())
            status = value[-2]
            # 2.update status, Stop unequal Dead.
            if now - last_time > self.time_out and status != self.agent.STOP and status != self.agent.DEAD:
                # time out, update status to DEAD
                status = self.agent.DEAD
                logger.info("Agent {} change its status to {}".format(name, status))
                new_value[-2] = status
                self.agent.agent_instance.table[name] = tuple(new_value)
                logger.info(self.agent.agent_instance.table)

    def send_heartbeat_info(self):
        acl = ACLMessage()
        acl.set_performative(ACLMessage.HEARTBEAT)
        acl.set_protocol(ACLMessage.FIPA_QUERY_PROTOCOL)
        acl.set_content(self.agent.status)
        self.agent.send(acl)

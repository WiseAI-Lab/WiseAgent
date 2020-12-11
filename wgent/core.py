"""Framework for Intelligent Agents Development - wgent
"""
import copy
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from queue import PriorityQueue

from wgent.acl.messages import ACLMessage
from wgent.acl.transports import KafkaTransport, ConfluentKafkaTransport
from wgent.behaviours.protocols import Behaviour
from wgent.behaviours.system import CompConnection, HeartbeatBehaviour
from wgent.acl.aid import AID
from wgent.utility import string2timestamp, logger
from collections import namedtuple
from functools import partial

"""The base agent interface."""

AgentInfo = namedtuple('AgentInfo', ['server_host', 'topic', 'status', 'last_time'])


# -----------------Network Manager--------------------

class AgentFactory(object):
    try:
        transport = KafkaTransport
    except:
        transport = ConfluentKafkaTransport
    """This class implements the actions and attributes
        of the Agent protocol. Its main function is to store
        important information to the agent communication protocol.

        Attributes
        ----------
        agent_ref : Agent
            Agent object
        aid : AID
            Agent AID
        ams : dictionary
            A dictionary of form: {'name': ams_IP, 'port': ams_port}
        ams_aid : AID
            AID of AMS
        debug : Boolean
            If True activate the debug mode
        messages : list
            List of messages to be sent to another agents
        on_start : method
            method that executes the agent's behaviour defined both
            by the user and by the System-PADE when the agent is initialised
        react : method
            method that executes the agent's behaviour defined
            both by the user and by the System-PADE.
        table : dictionary
            table stores the active agents, a dictionary with keys: name and
            values: AID
        """

    def __init__(self, agent_ref):
        """Init the AgentFactory class

        Parameters
        ----------
        agent_ref : Agent_
            agent object instance
        """

        self.agent_ref = agent_ref  #
        self.debug = agent_ref.debug
        self.aid = agent_ref.aid  # stores the agent's identity.
        self.messages = []
        self.react = agent_ref.react
        self.table = None
        self.is_table_updated = False

    @staticmethod
    def build_transport(self):
        """This method initializes the Agent transport

        Parameters
        ----------
        Returns
        -------
        AgentProtocol
            return a protocol instance
        """
        self.transport = self.transport()
        return self.transport

    async def send(self):
        """
            Send the message to receivers.
        """
        for message in self.messages:
            await self.transport.push(message, self.table)
            self.messages.remove(message)  # origin is a table

    def start(self):
        """
            Init this that the message in self.messages will auto-send and auto-receive
        """
        self.table = self._init_table()  # manage the connection with other agent (Topic list)
        self.is_table_updated = True
        self.build_transport()  # Init the transport in this factory.
        self.agent_ref.start_transport_task(self.launch_transport)  # loop pull

    def launch_transport(self):
        while True:
            if self.is_table_updated:
                self.transport.pull(self.react, self.table)  # Transport Service
            self.is_table_updated = False


class AgentState:
    """
        Agent State
    """
    ALIVE = "alive"
    DEAD = "dead"
    STOP = "stop"
    START = "start"
    RUNNING = "running"
    agent_statuses = [ALIVE, DEAD, RUNNING, STOP]
    agent_operators = [STOP, START]


# ----------------------Agent Definition---------------------
class Agent_(object):
    """
        Base Agent contains the aid, status and behaviours.
        aid: The uniqueness of an agent
        status: Reflect the agent's status now.
        behaviours: A list which contain actions of the agent prepare to execute.
    """

    def __init__(self, aid: AID or str):
        """Initialization

        Parameters
        ----------
        aid : AID or str
            Agent AID
        """
        # agent info
        self.__aid = aid
        self.__status = None
        self.debug = False
        # network; connection
        self.agent_instance = None
        transport = "kafka"
        self.transport = KafkaTransport if transport == "kafka" else ConfluentKafkaTransport

        self.produce_queue = PriorityQueue(maxsize=100)  # Send the message
        self.system_queue = PriorityQueue(maxsize=20)  # Send the message
        # behaviour
        self.__behaviours = []  # About another agent's message
        self.system_behaviours = []  # About the ams message
        # thread or process
        self.op = True
        self.max_main_workers = 5
        self.max_system_workers = 5
        self.max_transport_workers = 5  # Not split the consumer and producer.
        # 1. System Task(System Behaviour)
        # 2. Main Task(Normal Behaviour)
        # 3. Transport Task(Network Task)
        if self.op:
            self.main_executor = ThreadPoolExecutor(max_workers=self.max_main_workers, thread_name_prefix='agent_')
            self.system_executor = ThreadPoolExecutor(max_workers=self.max_system_workers, thread_name_prefix='system_')
            self.transport_executor = ThreadPoolExecutor(max_workers=self.max_transport_workers,
                                                         thread_name_prefix='transport_')
        else:
            self.main_executor = ProcessPoolExecutor(max_workers=self.max_main_workers)
            self.system_executor = ProcessPoolExecutor(max_workers=self.max_system_workers)
            self.transport_executor = ProcessPoolExecutor(max_workers=self.max_transport_workers)
        self._stopped = False
        self._restarting = False
        self.running_tasks = {}  # A sequence of Future

    # ----------------Property-----------------------
    @property
    def aid(self):
        """Summary

        Returns
        -------
        TYPE
            Description
        """
        return self.__aid

    @aid.setter
    def aid(self, value):
        """AID setter
        """
        if isinstance(value, AID):
            self.__aid = value
        else:
            raise ValueError('aid object type must be AID!')

    @property
    def behaviours(self):
        """Summary

        Returns
        -------
        TYPE
            Description
        """
        return self.__behaviours

    @behaviours.setter
    def behaviours(self, value):
        """Summary

        Parameters
        ----------
        value : TYPE
            Description

        Raises
        ------
        ValueError
            Description
        """
        for v in value:
            if not issubclass(v.__class__, Behaviour):
                raise ValueError(
                    'behaviour must be a subclass of the Behaviour class!')
        else:
            self.__behaviours = value

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, value):
        """
            status setter
        """
        if value in AgentState.agent_statuses:
            self.__status = value
        else:
            raise ValueError('status must belong to the status list!')

    # ---------------------Message-----------------
    def react(self, message):
        """This method should be overriden and will
        be executed all the times the agent receives
        any kind of message.

        Parameters
        ----------
        message : ACLMessage
            receive message
        """
        try:
            message = message.value()  # confluent
        except Exception:
            message = message.value  # kafka

        try:
            message = json.loads(message.decode('utf-8'))
            if isinstance(message, str):
                message = json.loads(message)
        except Exception as e:
            if self.debug:
                raise e
            else:
                logger.exception(e)
                return
        return message

    def send(self, message):
        """
            This method calls the method self._send to sends
        an ACL message to the agents specified in the receivers
        parameter of the ACL message.

        If the number of receivers is greater than 20, than a split
        will be done.


        :param message:
        :return:
        """
        self.wait_and_put(self.produce_queue, message)

    def _send(self, message):
        """This method effectively sends the message to receivers
        by connecting the receiver and sender sockets in a network

        Parameters
        ----------
        message : ACLMessage
            Message to be sent
        """
        new_receivers = []
        if message.receivers:
            for receiver in message.receivers:
                for name in self.agent_instance.table:
                    if receiver.localname in name and receiver.name != self.aid:
                        # corrects the port and host parameters randomly generated when only a name
                        # is given as a identifier of a receiver.
                        addr = self.agent_instance.table[name]
                        host, port = addr[0].split(':')
                        topic = addr[1]
                        receiver.setPort(port)
                        receiver.setHost(host)
                        receiver.set_topic(topic)
                        new_receivers.append(receiver)
                        # makes a connection to the agent and sends the message.
        else:
            # empty as for everyone
            for name, addr in self.agent_instance.table.items():
                cur_aid = name + '@' + addr[0] + '@' + addr[1]
                new_receivers.append(AID(cur_aid))
        message.receivers = new_receivers

        self.agent_instance.messages.append(message)
        receiver_str = str()
        for receiver in message.receivers:
            receiver_str += receiver.name + '-'
        res = '[MESSAGE SENT]', message.performative, 'FROM', message.sender.name, 'TO', receiver_str
        logger.info(res)
        self.start_transport_task(self.agent_instance.send)

    # -----------------Task--------------------------
    def add_running_task(self, action, future):
        """
            Record the running task
        :param action: An object
        :param future: Result from "concurrent.futures.Executor"
        :return:
        """
        self.running_tasks[action] = future
        return True

    def remove_running_task(self, key):
        """
            Remove the item from "running_task"
        :param key: value in array
        :return:
        """
        return self.running_tasks.pop(key)

    def start_transport_task(self, target, *args):
        """
            Start a transport worker of Network Manager by "concurrent.futures.Executor".
        :param target: func
        :param args:
        :return:
        """
        return self.start_task(self.transport_executor, target, *args)

    def start_main_task(self, target, *args):
        """
            Start a main worker of main by "concurrent.futures.Executor".
        :param target: func
        :param args:
        :return:
        """
        return self.start_task(self.main_executor, target, *args)

    def start_system_task(self, target, *args):
        """
            Start a system worker of main by "concurrent.futures.Executor".
        :param target: func
        :param args:
        :return:
        """
        return self.start_task(self.system_executor, target, *args)

    def start_task(self, task, target, *args):
        """
            Start a worker of main by "concurrent.futures.Executor".
        :param task:
        :param target:
        :param args:
        :return:
        """
        future = task.submit(target, *args)  # concurrent.futures.Future
        task_name = f"{target.__str__() + getattr(target, '__name__')}_{int(time.time())}"
        func = partial(self.future_done_callback, task_name)
        future.add_done_callback(func)
        self.add_running_task(task_name, future)
        return future

    def future_done_callback(self, task_name, future):
        """
            Check the situation of task
        :param task_name:
        :param future:
        :return:
        """

        if task_name in self.running_tasks.keys():
            exception = future.exception()
            if exception:
                logger.exception("{} :::: {}".format(task_name, exception))
            self.remove_running_task(task_name)

    def consumer_task(self, behaviour, acl):
        """
            The thread or process for producer in kafka.

        :return:
        """
        if self._stopped:
            return
        behaviour.execute(acl)

    def producer_task(self):
        """
            Execute a task for waiting to send message
        :return:
        """
        while True:
            message = self.wait_and_get(self.produce_queue)
            message.set_sender(self.aid)
            message.set_message_id()
            message.set_datetime_now()
            self._send(message)

    def system_task(self):
        """
            Execute a task for executing the system's message
        :return:
        """
        while True:
            behaviour, message = self.wait_and_get(self.system_queue)
            behaviour.execute(message)

    # -------------Utils--------------
    @staticmethod
    def wait_and_get(queue):
        return queue.get()[1]

    @staticmethod
    def wait_and_put(queue, item):
        return queue.put((int(time.time()), item))

    # ------------Manage Status---------------
    def stop(self):
        """
            Just stop to execute the normal behaviour
        :return:
        """
        self._stopped = True
        self.main_executor.shutdown(False)  # Only shutdown the main Executor
        self.status = AgentState.STOP

    def restart(self):
        """

        :return:
        """
        self._stopped = False
        self._restarting = True
        self.on_start()
        self._restarting = False
        self.status = AgentState.ALIVE

    def on_start(self):
        """
        This method defines the initial behaviours of an agent.

        :return:
        """

        self.status = AgentState.ALIVE
        # Agent Network Manager launch
        if not self.agent_instance:
            self.agent_instance = AgentFactory(self)
            self.agent_instance.transport = self.transport  # Define the transport
            self.agent_instance.start()
        # Check if restart, True doesn't need to run above
        if not self._restarting:
            # Start a worker for sending message
            self.start_transport_task(self.producer_task)
            self.start_system_task(self.system_task)
            # System Behaviour launch
            for system_behaviour in self.system_behaviours:
                self.start_system_task(system_behaviour.on_start)
        else:
            # restart the main executor
            if self.op:
                self.main_executor = ThreadPoolExecutor(max_workers=self.max_main_workers, thread_name_prefix='agent_')
            else:
                self.main_executor = ProcessPoolExecutor(max_workers=self.max_main_workers)
        # Current Agent Behaviour launch
        self.launch_agent_behaviours()

    def launch_agent_behaviours(self):
        """Aux method to send behaviours
        """
        for behaviour in self.behaviours:
            self.start_main_task(behaviour.on_start)

    @property
    def stopped(self):
        return self._stopped


class Agent(Agent_):
    """
    """

    def __init__(self, aid: str):
        super(Agent, self).__init__(aid=aid)

    def restart_network(self, aid: AID or str):
        """This method instantiates the ams agent

        Parameters
        ----------
        """
        if not self.agent_instance:
            self.agent_instance = AgentFactory(agent_ref=self)

        if isinstance(aid, AID):
            name = aid.name
            server_addr = aid.host + ":" + aid.port
            topic = aid.topic
        else:
            name, server_addr, topic = aid.split('@')
        self.agent_instance.table[name] = (server_addr, topic, AgentState.ALIVE, int(time.time()))
        self.agent_instance.is_table_updated = True

    # Heartbeat Using...
    def update_table_by_acl(self, message):
        """
            Update table by message info.
        :param message: ACL object
        :return: True is new agent online and False if exist agent's status update.
        """
        if not isinstance(message, ACLMessage):
            raise TypeError("Only support ACLMessage.")
        sender = message.sender
        datetime_str = message.datetime
        name, server, topic = sender.split('@')
        if name in self.agent_instance.table.keys() and sender != self.aid:
            value = self.agent_instance.table[name]
            new_value = list(copy.copy(value))  # copy origin info
            new_value[-1] = int(string2timestamp(datetime_str))  # update time which is the
            if message.content in AgentState.agent_statuses and message.content != new_value[-2]:  #
                new_value[-2] = message.content  # content is status
                self.agent_instance.table[name] = new_value  # update info
                self.agent_instance.is_table_updated = True
                return True
            else:
                self.agent_instance.table[name] = new_value  # update info
                return False
        else:
            # new agent online.
            new_value = AgentInfo(server, topic, message.content, int(time.time()))
            self.agent_instance.table[name] = tuple(new_value)
            self.agent_instance.is_table_updated = True
            return True

    def react(self, message):
        """
            React to the message
        :param message:
        :return:
        """
        message = super(Agent, self).react(message)
        acl = ACLMessage()
        acl.from_dict(message)
        for behaviour in self.system_behaviours:
            self.wait_and_put(self.system_queue, (behaviour, acl))  # queue in main_executor
        # If not stop that run the normal behaviours.
        if not self._stopped:
            for behaviour in self.behaviours:
                # Future version:0.0.2
                self.start_transport_task(self.consumer_task, behaviour, acl)

    def on_start(self):
        """
            Initial agent here.
        :return:
        """
        # Add Behaviours
        if not self._restarting:
            comp_connection = CompConnection(self)
            self.system_behaviours.append(comp_connection)  # system
            heartbeat = HeartbeatBehaviour(self, 5)
            self.behaviours.append(heartbeat)  # normal as main
        super(Agent, self).on_start()


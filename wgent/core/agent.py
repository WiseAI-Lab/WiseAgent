"""Framework for Intelligent Agents Development - wgent
"""
import copy
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from queue import PriorityQueue

from confluent_kafka.cimpl import KafkaException
from kafka import KafkaConsumer, KafkaProducer
from confluent_kafka import Consumer, Producer
from wgent.acl.filters import Filter
from wgent.acl.messages import ACLMessage
from wgent.behaviours.protocols import FipaRequestProtocol, Behaviour, TimedBehaviour
from wgent.config import CONFIG_PATH, DEFAULT_AGENT_CONFIG
from wgent.core.aid import AID
from wgent.utility import BehaviourError, AgentStoppedError, string2timestamp
from collections import namedtuple
from functools import partial

logging.basicConfig(filename='logger.log', level=logging.INFO)

# Primitive Agent_ Class
# python3
# Copyright 2018 DeepMind Technologies Limited. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The base agent interface."""

AgentInfo = namedtuple('AgentInfo', ['server_host', 'topic', 'status', 'last_time'])


# -----------------Network Manager--------------------
class Transport(object):
    def __init__(self):
        # broker info
        # self._consumer = None
        self._producer = None
        self.pause_call_func = None
        self.consumers = {}
        self.config = {
            ''
        }
        self.transport_executor = ThreadPoolExecutor(max_workers=5)

    def launch_task(self, target, *args):
        future = self.transport_executor.submit(target, *args)
        return future

    def send_topic(self, message, tables: dict):
        """
            Send message to Topic
        :return:
        """

    def receive_process(self, call_func, tables: dict, is_table_updated=False):
        """
            Receive message rom topic which in tables
        :param call_func:
        :param tables:
        :param is_table_updated:
        :return:
        """
        if is_table_updated:
            server_dict = {}
            for name, addr in tables.items():  # ('localhost:9092', 'topic_1', 'alive', '1564651235')
                server_host, topic = addr[0], addr[1]
                if server_host not in server_dict.keys():
                    server_dict[server_host] = [topic]
                else:
                    server_dict[server_host].append(topic)
            if self.server_dict == server_dict:
                return
            else:
                self.server_dict = server_dict
            # 2. update subscription
            for server_host, topics in server_dict.items():
                consumer_name = "{}".format(server_host)
                if consumer_name not in self.consumers.keys():
                    _consumer = self.new_consumer(server_host)
                    self.consumers[consumer_name] = _consumer
                else:
                    _consumer = self.consumers[consumer_name]
                _consumer.subscribe(topics=topics)

    def new_consumer(self, server_host):
        """
            Create a new consumer
        :param server_host:
        :return:
        """

    def start_consumer(self, call_func):
        for _, consumer in self.consumers.items():
            self.pause_call_func = call_func
            while True:
                records = consumer.poll(200)
                if records:
                    break
            for pa, msgs in records.items():
                for msg in msgs:
                    call_func(msg)
            return

    def resume_receive(self, tables: dict):
        """
            Resume subscribe now
        :return:
        """
        if self.pause_call_func:
            self.receive_process(self.pause_call_func, tables)
            logging.info("Resume subscriber success and the callback function is {}".format(self.pause_call_func))
        else:
            logging.exception("Resume subscriber error that the callback function is None. Try Resubscribe again!!!")


class KafkaTransport(Transport):
    """
        _tables: {'name':('server','topic')}, exp: {'local':('localhost','9092')}
    """

    def __init__(self):
        super(KafkaTransport, self).__init__()
        self.server_dict = None

    def send_topic(self, message, tables: dict):
        """
        Send the message to topic.
        :param message:
        :param tables: {'local_agent': ('localhost:9092', 'test')}
        :return: is success
        """
        log_info = {}
        # receiver: AID or ('localhost:9092', 'test')
        if not message.receivers:
            message.receivers.append(message.sender)
        for receiver in message.receivers:
            if isinstance(receiver, AID):
                key = receiver.name.split('@')[0]
                if key in tables.keys():
                    addr = tables[key]
                else:
                    logging.info("Receiver AID not in tables")
                    continue
            elif isinstance(receiver, set):
                key = receiver.split('@')[0]
                if key in tables.keys():
                    addr = tables[key]
                else:
                    logging.info("Receiver address not in tables")
                    continue
            else:
                logging.info("Cannot identify the receiver format.")
            server_host, topic = addr[0], addr[1]
            self._producer = KafkaProducer(
                bootstrap_servers=server_host,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            message_json = message.as_json()
            future = self._producer.send(topic, message_json)
            log_info[receiver] = future.succeeded()
            self._producer.flush()
        return log_info

    def receive_process(self, call_func, tables: dict, is_table_updated=False):
        """
            Receive the message from the topics and set a callback function to solve.
        :param call_func: Solve the message
        :param tables: Solve the message
        :param is_table_updated: is table updated
        """
        # TODO Add a executor to solve diff kafka !!!
        super(KafkaTransport, self).receive_process(call_func, tables, is_table_updated)
        # 3.Pull data by Consumer
        self.start_consumer(call_func)

    def new_consumer(self, server_host):
        group_id = f"Agent_{server_host}_{int(time.time())}"
        consumer = KafkaConsumer(bootstrap_servers=server_host, group_id=group_id)
        return consumer


class ConfluentKafkaTransport(Transport):
    """
        _tables: {'name':('server','topic')}, exp: {'local':('localhost','9092')}
    """

    def __init__(self):
        super(ConfluentKafkaTransport, self).__init__()

    def send_topic(self, message, tables: dict):
        """
        Send the message to topic.
        :param message:
        :param tables: {'local_agent': ('localhost:9092', 'test')}
        :return: is success
        """
        log_info = {}
        # receiver: AID or ('localhost:9092', 'test')
        if not message.receivers:
            message.receivers.append(message.sender)
        for receiver in message.receivers:
            if isinstance(receiver, AID):
                key = receiver.name.split('@')[0]
                if key in tables.keys():
                    addr = tables[key]
                else:
                    logging.exception("Receiver AID not in tables")
                    continue
            elif isinstance(receiver, set):
                key = receiver.split('@')[0]
                if key in tables.keys():
                    addr = tables[key]
                else:
                    logging.exception("Receiver address not in tables")
                    continue
            else:
                logging.exception("Cannot identify the receiver format.")
            server_host, topic = addr[0], addr[1]
            self._producer = Producer(
                {
                    'bootstrap.servers': server_host,
                }
            )
            message_json = message.as_json()
            mes = None
            try:
                self._producer.produce(topic, message_json.encode('utf-8'), callback=self.delivery_report)
            except BufferError:
                mes = "if the internal producer message queue is full (``queue.buffering.max.messages`` exceeded)"
            except KafkaException:
                mes = "for other errors, see exception code"
            except NotImplementedError:
                mes = "if timestamp is specified without underlying library support."
            finally:
                if mes:
                    logging.exception(mes)
            self._producer.flush()
        return log_info

    @staticmethod
    def delivery_report(err, msg):
        """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
        if err is not None:
            print('Message fail to: {}'.format(err))
        else:
            print('Message success to {} [{}]'.format(msg.topic(), msg.partition()))

    def receive_process(self, call_func, tables: dict, is_table_updated=False):
        super(ConfluentKafkaTransport, self).receive_process(call_func, tables, is_table_updated)
        self.start_consumer(call_func)

    def new_consumer(self, server_host):
        group_id = f"Agent_{server_host}_{int(time.time())}"
        consumer = Consumer({
            'bootstrap.servers': server_host,
            'group.id': group_id,
        })
        return consumer


class AgentFactory(object):
    transport = KafkaTransport

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
        conn_count : int
            Number of active connections
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
        agent_ref : Agent
            agent object instance
        """
        self.conn_count = 0
        self.agent_ref = agent_ref
        self.debug = agent_ref.debug
        self.aid = agent_ref.aid  # stores the agent's identity.
        self.messages = []
        self.react = agent_ref.react
        self.table = None
        self.is_table_updated = False

    @staticmethod
    def _init_table():
        table = {}
        error = False
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                content = f.read()
            if content:
                content = json.loads(content)
                if isinstance(content, dict) and 'topic' in content.keys():
                    host = content['topic']
                    name, server, topic = host.split('@')
                    table[name] = (server, topic, Agent.ALIVE, int(time.time()))
                else:
                    error = True
            else:
                error = True
        else:
            error = True

        if error:
            logging.info("Agent_config not exist.")
            with open(CONFIG_PATH, 'w') as f:
                f.write(json.dumps(DEFAULT_AGENT_CONFIG))
            name, server, topic = DEFAULT_AGENT_CONFIG['topic'].split('@')
            table[name] = (server, topic, Agent.ALIVE, int(time.time()))
        print("Initial agent's table: ", table)
        return table

    def build_transport(self):
        """This method initializes the Agent transport

        Parameters
        ----------
        addr : TYPE
            Description

        Returns
        -------
        AgentProtocol
            return a protocol instance
        """
        self.transport = self.transport()
        return self.transport

    def send(self):
        for message in self.messages:
            sended_message = True
            log_info = self.transport.send_topic(message, self.table)
            if sended_message:
                self.messages.remove(message)  # origin is a table

    def start(self):
        """
            Init this that the message in self.messages will auto-send and auto-receive
        """
        self.table = self._init_table()  # manage the connection with other agent (Topic list)
        self.is_table_updated = True
        self.build_transport()  # Init the transport in this factory.
        self.agent_ref.start_transport_task(self.launch_transport)

    def launch_transport(self):
        while True:
            # if self.agent_ref.stopped:
            #     return
            self.transport.receive_process(self.react, self.table, self.is_table_updated)  # Transport Service
            self.is_table_updated = False


# ---------------------System Behaviours-----------------------
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
            print("Agent {}...".format(self.agent.status))

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
        if self.agent.debug:
            print(res)
        logging.info(res)
        flag = self.agent.update_table_by_acl(message)
        if flag:
            print("New Agent Online: ", self.agent.agent_instance.table)
            logging.info("Update Table to: {}".format(self.agent.agent_instance.table))

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
            logging.info("Agent stop normal behaviours.")
        except Exception as e:
            logging.exception(e)

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
                print("Agent {} change its status to {}".format(name, status))
                new_value[-2] = status
                self.agent.agent_instance.table[name] = tuple(new_value)
                print(self.agent.agent_instance.table)

    def send_heartbeat_info(self):
        acl = ACLMessage()
        acl.set_performative(ACLMessage.HEARTBEAT)
        acl.set_protocol(ACLMessage.FIPA_QUERY_PROTOCOL)
        acl.set_content(self.agent.status)
        self.agent.send(acl)


# ----------------------Agent Definition---------------------
class Agent_(object):
    """
        Base Agent contains the aid, status and behaviours.
        aid: The uniqueness of an agent
        status: Reflect the agent's status now.
        behaviours: A list which contain actions of the agent prepare to execute.
    """

    ALIVE = "alive"
    DEAD = "dead"
    STOP = "stop"
    START = "start"
    RUNNING = "running"
    status_list = [ALIVE, DEAD, RUNNING, STOP]
    status_operators = [STOP, START]

    def __init__(self, aid):
        """Initialization

        Parameters
        ----------
        aid : AID
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
        # self.connection_tables = []  # which behaviours want to get info, if not in agent_instance's tables that will wait

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
        if value in self.status_list:
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
                logging.exception(e)
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
        if self.debug:
            print(res)
        logging.info(res)
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
                logging.exception("{} :::: {}".format(task_name, exception))
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
        self.status = self.STOP

    def restart(self):
        """

        :return:
        """
        self._stopped = False
        self._restarting = True
        self.on_start()
        self._restarting = False
        self.status = self.ALIVE

    def on_start(self):
        """
        This method defines the initial behaviours of an agent.

        :return:
        """

        self.status = self.ALIVE
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
        self.agent_instance.table[name] = (server_addr, topic, self.ALIVE, int(time.time()))
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
            if message.content in self.status_list and message.content != new_value[-2]:  #
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

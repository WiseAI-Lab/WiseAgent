"""
@File    :   transports.py    
@Contact :   sfreebobo@163.com
@License :   (C)Copyright 2020-2021

@Modify Time      @Author    @Version    @Description
------------      -------    --------    -----------
2020/12/10 20:34   Dongbo Xie      1.0         None
"""
# Base lib
import abc
from collections import namedtuple
from typing import NoReturn
import asyncio
import json
import time

# Message Queue lib
# TODO: Make a selection here.
from confluent_kafka import Consumer as ConfluentConsumer, Producer as ConfluentProducer
from kafka import KafkaConsumer, KafkaProducer

# Self lib
from wgent.acl import AID
from wgent.core import AgentState
from wgent.utility import logger, read_config

AgentInfo = namedtuple('AgentInfo', ['server_host', 'topic', 'status', 'last_time'])


# ------------------Table----------------
class AgentTable:
    """
        AgentTable: Literal
        --------------------------
        0 name: (server, topic, status, time)
        1 name: (server, topic, status, time)
        2 name: (server, topic, status, time)
        3 name: (server, topic, status, time)
        ...
        --------------------------
        Example:
            Loop Table
            1.For
            table = AgentTable()
            for name, info in table:
                ...
            2.Iter
            table = iter(AgentTable)
            next(table)

    """

    def __init__(self):
        self._table = {}
        self._init()

    # ---------------------Basic Func--------------------
    def _init(self) -> NoReturn:
        # IF the config file exist.
        config_content = read_config()
        # info
        system_name = config_content['system_name']
        system_address = config_content['system_address']
        system_port = config_content['system_port']
        system_topic = config_content['system_topic']
        # congregate
        info = AgentInfo(server_host=f"{system_address}:{system_port}", topic=system_topic,
                         status=AgentState.ALIVE, last_time=int(time.time()))
        self.add(system_name, info)

    def whole(self) -> dict:
        """
            Return the whole table for a dict.
        """
        return self._table

    def add(self, name: str, info: AgentInfo) -> NoReturn:
        """
            Add a user to table.
        """
        self._table[name] = info

    def get(self, name: str) -> AgentInfo:
        """
            Get the information by name.
        """
        if name in self._table.keys():
            return self._table[name]
        else:
            raise KeyError("Input user's name not exist.")

    def update(self, name: str, info: AgentInfo) -> NoReturn:
        """
            Update the user's info.
        """
        self._table[name] = info

    def in_table(self, name: str) -> bool:
        """
            Check a name whether in table.
        """
        if name in self._table.keys():
            return True
        else:
            return False

    # ----------------------Other Func---------------------
    def list_by_topic(self) -> dict:
        """
            Return a dict contain pairs of list with the same topic and without the name.
        """
        server_dict = {}
        for _, addr in self:
            server_host, topic = addr[0], addr[1]
            if server_host not in server_dict.keys():
                server_dict[server_host] = [topic]
            else:
                server_dict[server_host].append(topic)
        return server_dict

    # -----------------------Magic Func--------------------
    def __iter__(self):
        return iter(self._table.items())

    def __next__(self):
        return next(self)


# -------------------Transport------------
class Transport(object):
    def __init__(self):
        pass

    def push(self, message, tables: AgentTable):
        """
            Send the message
        """

    def pull(self, call_func, tables: AgentTable):
        """
            Receive the message
        """


class MessageQueueTransport(Transport):
    """
        Message Queue Transport, a subscription-production transport for agent contract,
        bases on the kafka of apache.
    """

    def __init__(self):
        super(MessageQueueTransport, self).__init__()
        # broker info
        self._producer = None  # Record a producer
        self.pause_call_func = None  # call_func for consumer
        self.consumers = {}  # consumers from diff server.

    # ---------------Main Func-----------------
    def push(self, message, table: AgentTable) -> NoReturn:
        self._send_process(message, table)

    def pull(self, call_func, table: AgentTable) -> NoReturn:
        self._receive_process(call_func, table)

    # --------------Inter Func-----------------

    async def _wait_poll(self, consumer: KafkaConsumer, interval_time: int = 200) -> NoReturn:
        """
            TODO: It doesn't test.
        """
        records = consumer.poll(interval_time)
        for pa, msgs in records.items():
            for msg in msgs:
                await self.pause_call_func(msg)

    def _start_consumer(self, call_func) -> NoReturn:
        """
            TODO: It should not a loop for the consumers table.
        """
        self.pause_call_func = call_func
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(self._wait_poll(consumer)) for _, consumer in self.consumers.items()]
        while True:
            # It should wait the tasks all done.
            ones, pend = loop.run_until_complete(asyncio.wait(tasks))
            print(ones, pend)

    def resume_receive(self, table: AgentTable) -> NoReturn:
        """
            Resume subscribe now
        :return:
        """
        if self.pause_call_func:
            self._receive_process(self.pause_call_func, table)
            logger.info("Resume subscriber success and the callback function is {}".format(self.pause_call_func))
        else:
            logger.exception("Resume subscriber error that the callback function is None. Try Resubscribe again!!!")

    @staticmethod
    def _filter_receivers(message, table: AgentTable) -> tuple:
        """
            It is a Iterable function to filter the data
        """
        if not message.receivers:
            message.receivers.append(message.sender)
        iter_r = iter(message.receivers)
        while True:
            try:
                receiver = next(iter_r)
                # Check AID
                if isinstance(receiver, AID):
                    key = receiver.name.split('@')[0]
                    if table.in_table(key):
                        addr = table.get(key)
                    else:
                        logger.info("Receiver AID not in tables")
                        continue
                elif isinstance(receiver, str):
                    key = receiver.split('@')[0]
                    if table.in_table(key):
                        addr = table.get(key)
                    else:
                        logger.info("Receiver AID not in tables")
                        continue
                else:
                    logger.info("Cannot identify the receiver format.")
                    continue
                yield tuple([receiver, addr[0], addr[1]])
            except StopIteration:
                break

    def _receive_process(self, call_func, table: AgentTable) -> NoReturn:
        """
            Receive message rom topic which in tables
            or Update the consumer's subscription when the table update.
        :param call_func:
        :param table:
        :return:
        """
        # 1. Gather server and topics
        server_dict = table.list_by_topic()
        if self.server_dict == server_dict:
            return
        else:
            self.server_dict = server_dict

        # 2. Update subscription in consumer
        for server_host, topics in server_dict.items():
            consumer_name = "{}".format(server_host)
            if consumer_name not in self.consumers.keys():
                _consumer = self._new_consumer(server_host)
                self.consumers[consumer_name] = _consumer
            else:
                _consumer = self.consumers[consumer_name]
            _consumer.subscribe(topics=topics)
        # 3. Start consumers
        self._start_consumer(call_func)

    # ---------------Abc Func------------------
    @abc.abstractmethod
    def _send_process(self, message, table: AgentTable) -> NoReturn:
        """
            Send message to topic.
        """

    @abc.abstractmethod
    def _new_consumer(self, server_host: str) -> KafkaConsumer:
        """
            Create a new consumer
        :param server_host:
        :return: KafkaConsumer
        """


class KafkaTransport(MessageQueueTransport):
    """
        Implement from the kafka-python lib.
    """

    def __init__(self):
        super(KafkaTransport, self).__init__()
        self.server_dict = None

    def _send_process(self, message, table: AgentTable) -> NoReturn:
        """
        Send the message to topic.
        :param message:
        :param table: AgentTable
        :return: is success
        """
        # If not receiver that is own.
        receiver, server_host, topic = self._filter_receivers(message, table)
        if not self._producer:
            self._producer = KafkaProducer(
                bootstrap_servers=server_host,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        message_json = message.as_json()
        future = self._producer.send(topic, message_json)
        logger.info(f"TRANSPORT---------<{receiver}: {future.succeeded()}>---------TRANSPORT")
        self._producer.flush()

    def _new_consumer(self, server_host: str) -> KafkaConsumer:
        group_id = f"Agent_{server_host}_{int(time.time())}"
        consumer = KafkaConsumer(bootstrap_servers=server_host, group_id=group_id)
        return consumer


class ConfluentKafkaTransport(MessageQueueTransport):
    """
        Implement from the confluent-kafka lib.
    """

    def __init__(self):
        super(ConfluentKafkaTransport, self).__init__()

    def _send_process(self, message, table: AgentTable) -> NoReturn:
        """
        Send the message to topic.
        :param message:
        :param table: AgentTable
        """
        receiver, server_host, topic = self._filter_receivers(message, table)
        if not self._producer:
            self._producer = ConfluentProducer(
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
        except NotImplementedError:
            mes = "if timestamp is specified without underlying library support."
        finally:
            if mes:
                logger.exception(mes)
        self._producer.flush()

    def _new_consumer(self, server_host: str) -> ConfluentConsumer:
        group_id = f"Agent_{server_host}_{int(time.time())}"
        consumer = ConfluentConsumer({
            'bootstrap.servers': server_host,
            'group.id': group_id,
        })
        return consumer

    @staticmethod
    def delivery_report(err, msg) -> NoReturn:
        """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
        if err is not None:
            logger.info('Message fail to: {}'.format(err))
        else:
            logger.info('Message success to {} [{}]'.format(msg.topic(), msg.partition()))

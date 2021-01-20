import copy
from concurrent.futures._base import Future
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from typing import Union, List, Dict, Tuple, Optional
import queue

from littletable import Table
from twisted.internet import protocol, reactor

from behaviours.system_behaviour import CompConnection, SubscribeBehaviour
from wise_agent.acl import ACLMessage
from wise_agent.misc.config import ConfigHandler
from wise_agent.misc.utility import start_task, logger, display_message
from wise_agent.acl import AID
from wise_agent.behaviours import Behaviour
from wise_agent.base import Actor
from .memory import MemoryHandler
from .peer import PeerProtocol
from .types import MemoryPiece, AgentState, AgentInfo


# -------------------Table----------------
class TransportTable:
    """
        TransportTable to record the information about the connector.
    """

    def __init__(self, table_name="agents"):
        self.table_name = table_name
        self._table = Table(table_name)

    # ---------------------Basic Func--------------------
    def whole(self) -> Table:
        """
            Return the whole table for a dict.
        """
        return self._table.info()

    def add(self, info):
        """
            Add to table.
        """
        self._table.insert(info)

    def get(self, name):
        """
            Get the information.
        """
        if isinstance(name, AID):
            name = name.name
        res = self._table.where(name=name).obs
        if res and isinstance(res, list):
            res = res[0]
        return res

    def delete(self, name):
        self._table.remove(self._table.where(name=name).obs)

    def update(self, name: str, info):
        """
            Update the user's info.
        """
        obs_info = self._table.where(name=name).obs
        if 0 < len(obs_info) < 2:
            self._table.remove(obs_info[0])
            self._table.insert(info)
        else:
            raise ValueError("Too much results for this name")

    def values(self):
        all_data = self._table.obs
        res = [agent for agent in all_data]
        return res

    def in_table(self, *args) -> bool:
        """
            Check a name whether in table.
        """
        return True if self._table.where(*args).obs else False

    def __str__(self):
        return self.table_name


class AgentProtocol(PeerProtocol):
    """This class implements the protocol to be followed by the
    agents during the communication process. The communication
    between agent and AMS agent, angent and Sniffer, and
    between agents is modeled in this class.

    This class does not stores persistent information, it
    is kept in the AgentFactory class.

    Attributes
    ----------
    fact : factory protocol
        Description
    message : ACLMessage
        Message object in the FIPA-ACL standard
    """

    def __init__(self, fact):
        """Init AgentProtocol class

        Parameters
        ----------
        fact : factory protocol
            instance of AgentFactory
        """
        self.fact = fact

    def connectionMade(self):
        """This method is always executed when
        a conection is established between an agent
        in client mode and an agent in server mode.
        Now, nothing is made here.
        """
        PeerProtocol.connectionMade(self)

    def connectionLost(self, reason):
        """This method is always executede when a connnection is lost.

        Parameters
        ----------
        reason : twisted exception
            Identifies the problem in the lost connection.
        """
        if self.message is not None:
            message = PeerProtocol.connectionLost(self, reason)
            self.message = None
            # executes the behaviour Agent.react to the received message.
            self.fact.react(message)

    def send_message(self, message):
        """This method call the functionality send_message from
        the peer protocol

        Parameters
        ----------
        message : ACLMessage
            Message object in the FIPA-ACL standard
        """
        PeerProtocol.send_message(self, message)

    def dataReceived(self, data):
        """This method is always executed when
        a new data is received by the agent,
        whether the agent is in client or server mode.
        Parameters
        ----------
        data : bytes
            some data received by the agent.
        """
        PeerProtocol.dataReceived(self, data)


class AgentFactory(protocol.ClientFactory):
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
        self.ams = agent_ref.ams  # stores the  ams agent's identity.
        self.messages = []
        self.react = agent_ref.react
        self.on_start = agent_ref.on_start
        self.ams_aid = AID('ams@' + self.ams['name'] + ':' + str(self.ams['port']))
        self.table = TransportTable()

    def buildProtocol(self, addr):
        """This method initializes the Agent protocol

        Parameters
        ----------
        addr : TYPE
            Description

        Returns
        -------
        AgentProtocol
            return a protocol instance
        """
        protocol = AgentProtocol(self)
        return protocol

    def clientConnectionFailed(self, connector, reason):
        """This method is called upon a failure
        in the connection between client and server.

        Parameters
        ----------
        connector : TYPE
            Description
        reason : TYPE
            Description
        """
        pass

    def clientConnectionLost(self, connector, reason):
        """This method is called when the connection between
        a client and server is lost.

        Parameters
        ----------
        connector : TYPE
            Description
        reason : TYPE
            Description
        """
        pass


class Agent_(Actor):
    """
        An agent, which have some basic property.
    """

    def __init__(self, aid: Union[AID, str]):
        self._aid: Union[AID, str] = aid  # Identifier
        self._status: str = AgentState.DEAD  # Represent the Agent State
        # Actually the agent should place their memory in brain, but I define the brain outside
        # this class because the brain is a thinking behaviour in 'wise_agent'.
        self.config_handler: Optional[ConfigHandler, None] = None
        self.memory_pieces_queue: queue.PriorityQueue = queue.PriorityQueue(
            maxsize=100)  # Delivery any message in agent.
        self.memory_handler = MemoryHandler()  # Some function to handle the memory in agent.
        # The behaviours are split two styles such as the people.
        self.behaviours = list()
        self.system_behaviours = list()
        # Step Configuration
        self.step_timeout = 0.1
        self.sleep_time = 0.1

        # Agent have property such as the game's role.
        self.is_process_pool = False
        self.pool_size = 5

        if self.is_process_pool:
            self._tasks_pool = ProcessPoolExecutor(
                max_workers=self.pool_size)
        else:
            self._tasks_pool = ThreadPoolExecutor(
                max_workers=self.pool_size, thread_name_prefix='agent_')
        self._running_tasks: Dict[str, Future] = {}
        # ALL: create a aid object with the aid of ams
        self.debug = True
        self.ams = dict()
        self.agent_factory = None
        self.ILP = None

    @property
    def aid(self):
        """
        AID getter

        Returns: aid
        """
        return self._aid

    @aid.setter
    def aid(self, value: AID):
        """
        AID setter

        Args:
            value: AID

        Returns: None

        Raises:
            ValueError, aid should be 'AID' object.
        """
        if isinstance(value, AID):
            self._aid = value
        else:
            raise ValueError('aid object type must be AID!')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        """
            status setter
        """
        if value in AgentState.agent_statuses:
            self._status = value
        else:
            raise ValueError('status must belong to the status list!')

    @property
    def debug(self):
        """Summary
        """
        return self.__debug

    @debug.setter
    def debug(self, value):
        """Debug
        """
        if isinstance(value, bool):
            self.__debug = value
        else:
            raise ValueError('debug object type must be bool')

    @property
    def ams(self):
        """AMS
        """
        return self.__ams

    @ams.setter
    def ams(self, value):
        """AMS
        """
        self.__ams = dict()
        if value == dict():
            self.__ams['name'] = 'localhost'
            self.__ams['port'] = 8000
        else:
            try:
                self.__ams['name'] = value['name']
                self.__ams['port'] = value['port']
            except Exception as e:
                raise e

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
    def system_behaviours(self):
        """Summary

        Returns
        -------
        TYPE
            Description
        """
        return self.__system_behaviours

    @system_behaviours.setter
    def system_behaviours(self, value):
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
            self.__system_behaviours = value

    def add_all(self, message):
        """Add all registered agents in the receivers list message

        Parameters
        ----------
        message : ACLMessage
            Some message
        """
        message.receivers = list()
        for agent in self.agent_factory.table.values():
            message.add_receiver(agent.name)

    def send(self, memory: Union[MemoryPiece, ACLMessage]):
        """This method calls the method self._send to sends
        an ACL message to the agents specified in the receivers
        parameter of the ACL message.
        If the number of receivers is greater than 20, than a split
        will be done.

        Parameters
        ----------
        memory : MemoryPiece
            Message to be sent
        """
        # Inform all behaviours
        if not isinstance(memory, MemoryPiece):
            memory = self.memory_handler.generate_memory_from_message(memory)
        self.push(memory)
        # Send message to agent
        message = memory.message
        message.set_sender(self.aid)
        message.set_message_id()
        message.set_datetime_now()

        c = 0.0
        if len(message.receivers) >= 20:
            receivers = [message.receivers[i:i + 20] for i in range(0, len(message.receivers), 20)]
            for r in receivers:
                reactor.callLater(c, self._send, message, r)
                c += 0.5
        else:
            self._send(message, message.receivers)
        return message

    def _send(self, message, receivers):
        """This method effectively sends the message to receivers
        by connecting the receiver and sender sockets in a network

        Parameters
        ----------
        message : ACLMessage
            Message to be sent
        receivers : list
            List of receivers agents
        """
        # "for" iterates on the message receivers
        for receiver in receivers:
            for agent in self.agent_factory.table.values():
                # "if" verifies if the receiver name is among the available agents
                name = agent.name
                if receiver.localname in name and receiver.localname != self.aid.localname:
                    # corrects the port and host parameters randomly generated when only a name
                    # is given as a identifier of a receiver.
                    host = agent.host
                    port = agent.port
                    receiver.set_port(port)
                    receiver.set_host(host)
                    # makes a connection to the agent and sends the message.
                    self.agent_factory.messages.append((receiver, message))
                    if self.debug:
                        logger.info(('[MESSAGE DELIVERY]',
                                     message.performative,
                                     'FROM',
                                     message.sender.name,
                                     'TO',
                                     receiver.name))
                    try:
                        reactor.connectTCP(host, port, self.agent_factory)
                    except:
                        self.agent_factory.messages.pop()
                        display_message(self.aid.name, 'Error delivery message!')
                    break
            else:
                if self.debug:
                    display_message(
                        self.aid.localname, 'Agent ' + receiver.name + ' is not active')
                else:
                    pass

    def push(self, memory: MemoryPiece):
        """
        Send a memory.

        Args:
            memory: MemoryPiece
            is_outside: Boolean

        Returns: None

        """
        assert isinstance(memory, MemoryPiece), "Agent send the Memory, so pack it as a memory."
        self.memory_handler.wait_and_put(self.memory_pieces_queue, memory)

    def on_start(self, *args, **kwargs):
        """
        Init an agent.
        Remember the super()... in your definition!!!
        """
        for system_behaviour in self.system_behaviours:
            system_behaviour.on_start()

        # sqlite(database) cursor cannot use in diff thread so that stop pool here.
        # for system_behaviour in self.system_behaviours:
        #     self._running_tasks = start_task(self._running_tasks, self._tasks_pool, system_behaviour.on_start)

    def react(self, message):
        memory_piece = self.memory_handler.generate_memory_from_message(message)
        self._dispatch_behaviour(memory_piece)
        # self._running_tasks = start_task(self._running_tasks, self._tasks_pool, self._dispatch_behaviour,
        #                                  memory_piece)

    # -----------------Task--------------------------
    def _dispatch_behaviour(self, memory_piece: MemoryPiece):
        """
            Dispatch the behaviour to execute the ACLMessage
        """
        if not isinstance(memory_piece, MemoryPiece):
            raise ValueError("It should be a Tuple(int, TaskPiece) object in Queue")
        executors: List[str] = memory_piece.executors
        behaviours = copy.copy(self.system_behaviours)
        behaviours.extend(self.behaviours)
        cur_behaviour_names: Dict[str, Behaviour] = {b.__class__.__name__: b for b in behaviours}
        if executors is None:
            # all behaviours
            executors = list(cur_behaviour_names.keys())

        for behaviour in executors:
            # Check it whether in behaviours
            if behaviour in cur_behaviour_names.keys():
                cur_behaviour_names[behaviour].execute(memory_piece.message)
            else:
                logger.exception(f"Behaviour:{behaviour} not exist in agent.behaviours.")

    def pause_agent(self):
        """This method makes the agent stops listeing to its port
        """
        self.ILP.stopListening()

    def resume_agent(self):
        """This method resumes the agent after it has been pause. Still not working
        """
        self.on_start()
        self.ILP.startListening()


class Agent(Agent_):
    """
        An agent, which have a brain to thinking.
    """

    # Agent alive when it have brain.
    def __init__(self, aid: Union[AID, str]):
        super(Agent, self).__init__(aid)

    def react(self, message, *args, **kwargs):
        """
            TODO: A agent react in brain but not define now. Brain Behaviour here

        Returns:

        """
        super(Agent, self).react(message)

    def update_ams(self, ams):
        """This method instantiates the ams agent

        Parameters
        ----------
        ams : dictionary
            AMS dictionary {'name': ams_IP, 'host': ams_host, 'port': ams_port}
        """
        self.ams = ams
        self.agent_factory = AgentFactory(agent_ref=self)


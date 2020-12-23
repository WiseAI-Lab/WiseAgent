from wise_agent.acl.filters import Filter
from wise_agent.acl.messages import ACLMessage
from wise_agent.behaviours import Behaviour


class FipaProtocol(Behaviour):
    """ This class implements a basis for all FIPA-compliant
        protocols
    """

    def __init__(self, agent, message, is_initiator):
        """Inicializes the class that implements a FipaProtocol

            :param agent: instance of the agent that will execute the protocol's
                         established behaviours.
            :param message: message to be sent by the agent when is_initiator
                         parameter is true.
            :param is_initiator: boolean type parameter that specifies if the
                         protocol instance will act as Initiator or Participant.

        """
        super(FipaProtocol, self).__init__(agent)

        self.is_initiator = is_initiator
        self.message = message

        self.filter_self = Filter()
        self.filter_self.set_sender(self.agent.aid)

        self.filter_not_undestood = Filter()
        self.filter_not_undestood.set_performative(ACLMessage.NOT_UNDERSTOOD)

        if self.message is not None:
            self.filter_conversation_id = Filter()
            self.filter_conversation_id.set_conversation_id(self.message.conversation_id)

    def handle_not_understood(self, message):
        """This method should be overridden when implementing a protocol.
            This method is always executed when the agent receives a
            FIPA_NOT_UNDERSTOOD type message

            :param message: FIPA-ACL message
        """
        pass

    def execute(self, message):
        """This method overrides the execute method from Behaviour class.
            The selection of the method to be executed after the receival
            of a message is implemented here.

            :param message: FIPA-ACL message
        """
        super(FipaProtocol, self).execute(message)
        if not self.filter_self.filter(message):
            self.message = message

            if self.filter_not_undestood.filter(self.message):
                self.handle_not_understood(message)
                return
        else:
            return


class FipaSubscribeProtocol(FipaProtocol):
    """This class implements the FipaSubscribeProtocol protocol,
        inheriting from the Behaviour class and implementing its methods.
    """

    def __init__(self, agent, message=None, is_initiator=True):
        """Initialize method
        """

        super(FipaSubscribeProtocol, self).__init__(agent, message, is_initiator)

        self.subscribers = set()

        # filter
        self.filter_protocol = Filter()
        self.filter_protocol.set_protocol(ACLMessage.FIPA_SUBSCRIBE_PROTOCOL)

        self.filter_subscribe = Filter()
        self.filter_subscribe.set_performative(ACLMessage.SUBSCRIBE)

        self.filter_agree = Filter()
        self.filter_agree.set_performative(ACLMessage.AGREE)

        self.filter_inform = Filter()
        self.filter_inform.set_performative(ACLMessage.INFORM)

        self.filter_refuse = Filter()
        self.filter_refuse.set_performative(ACLMessage.REFUSE)

        self.filter_cancel = Filter()
        self.filter_cancel.set_performative(ACLMessage.CANCEL)

        self.filter_failure = Filter()
        self.filter_failure.set_performative(ACLMessage.FAILURE)

    def on_start(self):
        """his method overrides the on_start method from Behaviour class
            and implements aditional settings to the initialize method
            of FipaSubscribeProtocol protocol.
        """
        super(FipaSubscribeProtocol, self).on_start()

        if self.is_initiator and self.message != None:
            if self.message.performative == ACLMessage.SUBSCRIBE:
                self.agent.send(self.message)

    def handle_subscribe(self, message):
        """
            handle_subscribe

        """
        pass

    def handle_agree(self, message):
        """
            handle_agree

        """
        pass

    def handle_refuse(self, message):
        """
            handle_refuse

        """
        pass

    def handle_inform(self, message):
        """
            handle_inform

        """
        pass

    def handle_cancel(self, message):
        """
            handle_cancel

        """
        pass

    def execute(self, message):
        """This method overrides the execute method from FipaProtocol class.
            The selection of the method to be executed after the receival
            of a message is implemented here.

            :param message: FIPA-ACL message
        """
        super(FipaSubscribeProtocol, self).execute(message)

        if self.filter_protocol.filter(self.message):
            if self.filter_subscribe.filter(self.message):
                self.handle_subscribe(message)

            elif self.filter_cancel.filter(self.message):
                self.handle_cancel(message)

            elif self.filter_inform.filter(self.message):
                self.handle_inform(message)

            elif self.filter_agree.filter(self.message):
                self.handle_agree(message)

            elif self.filter_failure.filter(self.message):
                self.handle_failure(message)
            else:
                return
            if self.filter_receiver.filter(self.message):
                self.handle_receiver(message)
                return
        else:
            return

    def register(self, aid):
        """register

        """
        self.subscribers.add(aid)

    def deregister(self, aid):
        """deregister

        """
        self.subscribers.remove(aid)

    def notify(self, message):
        """notify

        """
        for sub in self.subscribers:
            message.add_receiver(sub)
        self.agent.send(message)


class FipaRequestProtocol(FipaProtocol):
    """This class implements the FipaRequestProtocol protocol,
        inheriting from the Behaviour class and implementing its methods.
    """

    def __init__(self, agent, message=None, is_initiator=True):
        """Inicializes the class that implements FipaRequestProtocol protocol

            :param agent: instance of the agent that will execute the protocol's
                         established behaviours.
            :param message: message to be sent by the agent when is_initiator
                         parameter is true.
            :param is_initiator: boolean type parameter that specifies if the
                         protocol instance will act as Initiator or Participant.

        """
        super(FipaRequestProtocol, self).__init__(agent, message, is_initiator)

        self.filter_protocol = Filter()
        self.filter_protocol.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)

        self.filter_Request = Filter()
        self.filter_Request.set_performative(ACLMessage.REQUEST)

        self.filter_refuse = Filter()
        self.filter_refuse.set_performative(ACLMessage.REFUSE)

        self.filter_Agree = Filter()
        self.filter_Agree.set_performative(ACLMessage.AGREE)

        self.filter_failure = Filter()
        self.filter_failure.set_performative(ACLMessage.FAILURE)

        self.filter_inform = Filter()
        self.filter_inform.set_performative(ACLMessage.INFORM)

        self.filter_receiver = Filter()
        self.filter_receiver.set_receiver(agent.aid)

    def on_start(self):
        """
        This method overrides the on_start method from Behaviour class
            and implements aditional settings to the initialize method
            of FipaRequestProtocol protocol.
        """

        super(FipaRequestProtocol, self).on_start()

        if self.is_initiator and self.message != None:
            self.agent.send(self.message)

    def handle_request(self, message):
        """This method should be overridden when implementing a protocol.
            This method is always executed when the agent receives a
            FIPA_REQUEST type message

            :param message: FIPA-ACL message
        """
        pass

    def handle_refuse(self, message):
        """This method should be overridden when implementing a protocol.
            This method is always executed when the agent receives a
            FIPA_REFUSE type message

            :param message: FIPA-ACL message
        """
        pass

    def handle_agree(self, message):
        """This method should be overridden when implementing a protocol.
            This method is always executed when the agent receives a
            FIPA_AGREE type message

            :param message: FIPA-ACL message
        """
        pass

    def handle_failure(self, message):
        """This method should be overridden when implementing a protocol.
            This method is always executed when the agent receives a
            FIPA_FAILURE type message

            :param message: FIPA-ACL message
        """
        pass

    def handle_inform(self, message):
        """
        This method should be overridden when implementing a protocol.
            This method is always executed when the agent receives a
            FIPA_IMFORM type message

            :param message: FIPA-ACL message
        """
        pass

    def handle_receiver(self, message):
        pass

    def execute(self, message):
        """This method overrides the execute method from FipaProtocol class.
            The selection of the method to be executed after the receival
            of a message is implemented here.

            :param message: FIPA-ACL message
        """
        super(FipaRequestProtocol, self).execute(message)
        self.message = message
        if self.filter_protocol.filter(self.message):

            if self.filter_Request.filter(self.message):
                self.handle_request(message)

            elif self.filter_refuse.filter(self.message):
                self.handle_refuse(message)

            elif self.filter_Agree.filter(self.message):
                self.handle_agree(message)

            elif self.filter_failure.filter(self.message):
                self.handle_failure(message)

            elif self.filter_inform.filter(self.message):
                self.handle_inform(message)

            else:
                return
        else:
            return

from .aid import AID
from .messages import ACLMessage


class Filter:
    """
    This class instantiates a filter object. The filter has the purpose of
    selecting messages with pre established attributes in the filter object
    """

    def __init__(self):
        self.conversation_id = None
        self.sender = None
        self.performative = None
        self.protocol = None
        self.receiver = None

    def set_sender(self, aid):
        self.sender = aid

    def set_receiver(self, aid):
        self.receiver = aid

    def set_performative(self, performative):
        self.performative = performative

    def set_conversation_id(self, conversation_id):
        self.conversation_id = conversation_id

    def set_protocol(self, protocol):
        self.protocol = protocol

    def filter(self, message):
        state = True

        if self.conversation_id != None and self.conversation_id != message.conversation_id:
            state = False

        if self.sender != None and self.sender == message.sender:
            state = False

        if self.receiver != None and self.receiver not in message.receivers:
            state = False

        if self.performative != None and self.performative != message.performative:
            state = False

        if self.protocol != None and self.protocol != message.protocol:
            state = False

        return state


if __name__ == '__main__':
    message = ACLMessage(ACLMessage.REQUEST)
    message.set_sender(AID('john'))
    message.add_receiver('mary')
    message.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)

    filtro = Filter()
    filtro.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)

    if filtro.filter(message):
        print(message.encode("dict"))
    else:
        print('The message was blocked by the protocol.')

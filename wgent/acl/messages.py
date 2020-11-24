"""Framework for Intelligent Agents Development - PADE

The MIT License (MIT)

Copyright (c) 2019 Lucas S Melo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import copy

import dicttoxml

"""
    FIPA-ACL message creation and handling module
    -----------------------------------------------------

    This module contains a class which implements an ACLMessage
    type object. This object is the standard FIPA message used
    in the exchange of messages between agents.

"""
import json
from datetime import datetime
from uuid import uuid1
from wgent.core.aid import AID


class ACLMessage(object):
    """Class that implements a ACLMessage message type
    """

    ACCEPT_PROPOSAL = 'accept-proposal'
    AGREE = 'agree'
    CANCEL = 'cancel'
    CFP = 'cfp'
    CONFIRM = 'confirm'
    DISCONFIRM = 'disconfirm'
    FAILURE = 'failure'
    INFORM = 'inform'
    NOT_UNDERSTOOD = 'not-understood'
    PROPOSE = 'propose'
    QUERY_IF = 'query-if'
    QUERY_REF = 'query-ref'
    REFUSE = 'refuse'
    REJECT_PROPOSAL = 'reject-proposal'
    REQUEST = 'request'
    REQUEST_WHEN = 'request-when'
    REQUEST_WHENEVER = 'request-whenever'
    SUBSCRIBE = 'subscribe'
    INFORM_IF = 'inform-if'
    PROXY = 'proxy'
    PROPAGATE = 'propagate'
    HEARTBEAT = 'heartbeat'
    FIPA_REQUEST_PROTOCOL = 'fipa-request protocol'
    FIPA_QUERY_PROTOCOL = 'fipa-query protocol'
    FIPA_REQUEST_WHEN_PROTOCOL = 'fipa-request-when protocol'
    FIPA_CONTRACT_NET_PROTOCOL = 'fipa-contract-net protocol'
    FIPA_SUBSCRIBE_PROTOCOL = 'fipa-subscribe-protocol'

    performatives = ['accept-proposal', 'agree', 'cancel',
                     'cfp', 'call-for-proposal', 'confirm', 'disconfirm',
                     'failure', 'inform', 'not-understood',
                     'propose', 'query-if', 'query-ref',
                     'refuse', 'reject-proposal', 'request',
                     'request-when', 'request-whenever', 'subscribe',
                     'inform-if', 'proxy', 'propagate', 'heartbeat']

    protocols = ['fipa-request protocol', 'fipa-query protocol', 'fipa-request-when protocol',
                 'fipa-contract-net protocol']

    def __init__(self, performative=None):
        """ This method initializes a ACLMessage object when it is instantiated.

            :param performative: Type of the message to be created according to FIPA standard.
            It can be INFORM, CFP, AGREE, PROPOSE...
            All these types are attributes of ACLMessafe class.
        """
        if performative != None:
            if performative.lower() in self.performatives:
                self.performative = performative.lower()
        else:
            self.performative = None

        self.conversation_id = str(uuid1())
        self.messageID = str(uuid1())
        self.datetime = datetime.now()
        self.system_message = False
        self.sender = None
        self.receivers = list()
        self.reply_to = list()
        self.content = None
        self.language = None
        self.encoding = None
        self.ontology = None
        self.protocol = None
        self.reply_with = None
        self.in_reply_to = None
        self.reply_by = None

    def __gt__(self, other):
        if self.to_timestamp(other.datetime) - self.to_timestamp(self.datetime) < 0:
            return True
        else:
            return False

    @staticmethod
    def to_timestamp(datetime_data):
        if isinstance(datetime_data, str):
            datetime_data = datetime.astimezone(datetime_data)
        return datetime_data.timestamp()

    def __lt__(self, other):
        if self.to_timestamp(other.datetime) - self.to_timestamp(self.datetime) > 0:
            return True
        else:
            return False

    def set_performative(self, performative):
        """Method to set the Performative parameter of the ACL message.

           :param performative: performative type of the message.
           It can be any of the attributes of the ACLMessage class.
        """
        self.performative = performative

    def set_system_message(self, is_system_message):
        self.system_message = is_system_message

    def set_datetime_now(self):
        self.datetime = datetime.now()

    def set_sender(self, aid):
        """Method to set the agent that will send the message.

        :param aid: AID type object that identifies the agent that will send the message.
        """
        if isinstance(aid, AID):
            self.sender = aid
        else:
            self.set_sender(AID(name=aid))

    def add_receiver(self, aid):
        """Method used to add recipients for the message being created.

        :param aid: AID type object that identifies the agent that will receive the message.
        """

        if isinstance(aid, AID):
            self.receivers.append(aid)
        else:
            self.add_receiver(AID(name=aid))

    def add_reply_to(self, aid):
        """Method used to add the agents that should receive the answer of the message.

        :param aid: AID type object that identifies the agent that will receive the answer of this message.

        """
        if isinstance(aid, AID):
            self.reply_to.append(aid)
        else:
            self.add_reply_to(AID(aid))

    def set_content(self, data):
        self.content = data

    def set_language(self, data):
        self.language = data

    def set_encoding(self, data):
        self.encoding = data

    def set_ontology(self, data):
        self.ontology = data

    def set_protocol(self, data):
        self.protocol = data

    def set_conversation_id(self, data):
        self.conversation_id = data

    def set_message_id(self):
        self.messageID = str(uuid1())

    def set_reply_with(self, data):
        self.reply_with = data

    def set_in_reply_to(self, data):
        self.in_reply_to = data

    def set_reply_by(self, data):
        self.reply_by = data

    def __str__(self):
        """
            returns a printable version of the message in ACL string representation
        """

        p = '('

        p = p + str(self.performative) + '\n'

        if self.conversation_id:
            p = p + ":conversationID " + self.conversation_id + '\n'

        if self.sender:
            p = p + ":sender " + str(self.sender) + "\n"

        if self.receivers:
            p = p + ":receiver\n (set\n"
            for i in self.receivers:
                p = p + str(i) + '\n'

            p = p + ")\n"
        if self.content:
            p = p + ':content "' + str(self.content) + '"\n'

        if self.reply_with:
            p = p + ":reply-with " + self.reply_with + '\n'

        if self.reply_by:
            p = p + ":reply-by " + self.reply_by + '\n'

        if self.in_reply_to:
            p = p + ":in-reply-to " + self.in_reply_to + '\n'

        if self.reply_to:
            p = p + ":reply-to \n" + '(set\n'
            for i in self.reply_to:
                p = p + i + '\n'
            p = p + ")\n"

        if self.language:
            p = p + ":language " + self.language + '\n'

        if self.encoding:
            p = p + ":encoding " + self.encoding + '\n'

        if self.ontology:
            p = p + ":ontology " + self.ontology + '\n'

        if self.protocol:
            p = p + ":protocol " + self.protocol + '\n'

        p = p + ")\n"

        return p

    def create_reply(self):
        """Creates a reply for the message
        Duplicates all the message structures
        exchanges the 'from' AID with the 'to' AID
        """

        message = ACLMessage()

        message.set_performative(self.performative)
        message.set_system_message(is_system_message=self.system_message)

        if self.language:
            message.set_language(self.language)
        if self.ontology:
            message.set_ontology(self.ontology)
        if self.protocol:
            message.set_protocol(self.protocol)
        if self.conversation_id:
            message.set_conversation_id(self.conversation_id)

        for i in self.reply_to:
            message.add_receiver(i)

        if not self.reply_to:
            message.add_receiver(self.sender)

        if self.reply_with:
            message.set_in_reply_to(self.reply_with)

        return message

    def __setstate__(self, state):
        self.__init__()
        self.__dict__.update(state)

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        return state

    def as_dict(self) -> dict:
        dict_data = copy.copy(self.__dict__)
        dict_data['sender'] = str(dict_data['sender'])
        dict_data['datetime'] = str(dict_data['datetime'])
        dict_data['receivers'] = [str(receiver) for receiver in dict_data['receivers']]
        dict_data['reply_to'] = [str(reply) for reply in dict_data['reply_to']]
        return dict_data

    def as_json(self) -> str:
        return json.dumps(self.as_dict())

    def as_xml(self):
        dict_text = self.as_dict()
        dict_text['sender'] = str(dict_text['sender'].name)
        dict_text['receivers'] = [str(r.name) for r in dict_text['receivers']]
        dict_text['reply_to'] = [str(r.name) for r in dict_text['reply_to']]
        return dicttoxml.dicttoxml(dict_text, root=True, custom_root='ACLMessage')

    def from_json(self, json_text: str) -> None:
        dict_text = json.loads(json_text)
        self.from_dict(dict_text)

    def from_dict(self, dict_text: dict) -> None:
        if "ACLMessage" in dict_text.keys():
            dict_text = dict_text['ACLMessage']
        self.__dict__.update(dict_text)  # simple version, not validate now


if __name__ == '__main__':
    msg = ACLMessage()
    msg.set_sender(AID(name='Lucas'))
    msg.add_receiver(AID(name='Allana'))
    msg.set_content('51A Feeder 21I5')

    print(msg)
    print(msg.as_dict())
    dict_data = msg.as_dict()
    dict_data["performative"] = "text"
    msg.from_dict(dict_data)
    print(msg.as_xml())

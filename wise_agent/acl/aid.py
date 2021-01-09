"""
    Agent Identifier Class
"""
from wise_agent.utility import random_string


class AID(object):
    def __init__(self, name: str or None = None,
                 resolvers: None or list = None,
                 user_defined_properties=None):
        """
        Agent Identifier Class
        Optional parameters:
                String name with this form: localname@myAdress:port
                String[] resolvers
                ContentObject co
        """

        if name is not None:
            if '@' in name:
                self.name = name
                self.localname, adress = self.name.split('@')
                if ':' in adress:
                    self.host, self.port = adress.split(':')
                    self.port = int(self.port)
                else:
                    self.host, self.port = None, None
            else:
                self.localname = name
                self.host = 'localhost'
                self.port = '9092'
                self.name = self.localname + '@' + self.host + ':' + str(self.port)
        else:
            self.name = None  # string
        if resolvers is not None:
            self.resolvers = resolvers
        else:
            self.resolvers = list()  # AID
        if user_defined_properties is not None:
            self.user_defined_properties = user_defined_properties
        else:
            self.user_defined_properties = list()  # properties

    @classmethod
    def create_offline_aid(cls):
        agent_name = f"local_agent_{random_string(10)}"
        name = f"{agent_name}@localhost:0000@local"
        return cls(name)

    def set_local_name(self, name):
        """
        sets local name of the agent (string)
        """
        self.localname = name
        self.name = self.localname + '@' + self.host + ':' + str(self.port)

    def set_host(self, host):
        """
        sets host of the agent (string)
        """
        self.host = host
        self.name = self.localname + '@' + self.host + ':' + str(self.port)

    def set_port(self, port):
        """
        sets port of the agent (string)
        """
        self.port = port
        self.name = self.localname + '@' + self.host + ':' + str(self.port)

    def match(self, other):
        """
        returns True if two AIDs are similar
        else returns False
        """

        if other is None:
            return True

        if (self.name is not None and other.name is not None
                and not (other.get_name() in self.name)):
            return False
        return True

    def __eq__(self, other):
        """
        Comparision operator (==)
        returns True if two AIDs are equal
        else returns False
        """
        if other is None:
            return False

        if (self.name is not None and other.get_name() is not None
                and self.name != other.get_name()):
            return False

        return True

    def __ne__(self, other):
        """
        != operator
        returns False if two AIDs are equal
        else returns True
        """

        return not (self == other)

    def __hash__(self):
        h = hash(self.name)
        for i in self.user_defined_properties:
            h = h + hash(i)
        return h

    def __str__(self):
        """
        returns a printable version of an AID
        """

        return self.name

    def __repr__(self):
        return self.name

    def as_xml(self):
        """
        returns a printable version of an AID in XML
        """
        sb = "<agent-identifier>\n\t" + self.encode_tag("name", self.name) + "\n"
        sb = sb + "</agent-identifier>\n"

        return sb

    @staticmethod
    def encode_tag(tag, content):
        """
        encodes a content between 2 XML tags using the tag parameter

                <tag>content</tag>

        return string
        """
        sb = "<" + tag + ">" + content + "</" + tag + ">"

        return sb

"""
    launch the agent.

    """
import importlib
import signal
from datetime import datetime

import click
from twisted.internet import reactor

from wise_agent.core.types import AgentInfo
from wise_agent.behaviours.system_behaviour import ComportVerifyConnTimed, ComportSendConnMessages, \
    CompConnectionVerify, \
    PublisherBehaviour, CompConnection, SubscribeBehaviour
from wise_agent.acl import AID, ACLMessage
from wise_agent.misc.config import ConfigHandler
import argparse

parser = argparse.ArgumentParser()  # 添加参数
parser.add_argument('--config_path', help='Config file path', default="example_launch_config.json")
args = parser.parse_args()


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
interrupted = False


def start_agent(config_path: str):
    """
        Start an Agent.
    Args:
        config_path: config for an agent
    Returns:

    """
    click.clear()
    click.echo(click.style('''
            This is
            \      /\      / | |
             \    /  \    /  | |
              \  /    \  /   | |
               \/      \/    | |
            Python Agent Development framework
            ''', fg='green'))
    click.echo(click.style('''
            WiseAgent is a free software under development by:
            - Dongbox JiaYing University in China
            https://github.com/WiseAI-Lab/WiseAgent''', fg='blue'))

    config = ConfigHandler(config_path)
    agents = config.get("agents")
    agent_list = []
    agent_manager = None
    # Import Agent and  set the Ams
    for _, agent in agents.items():
        agent_module = importlib.import_module(agent.get("import_path"))
        name = agent.get("name")
        aid = agent.get("aid")
        is_ams = agent.get("is_ams", False)
        # IF ams
        agent_class = getattr(agent_module, name)
        # instance
        aid_instance = AID(aid)
        agent_instance = agent_class(aid_instance)
        agent_instance.config_handler = config

        if is_ams and not agent_manager:
            # TODO: Set an attribute to agent.
            server = AID(aid)
            agent_instance.update_ams({"name": server.host, "port": server.port})
            # Agent Manager Behaviours
            if not getattr(agent_instance, "comport_ident"):
                agent_instance.comport_ident = PublisherBehaviour(agent_instance)
                agent_instance.system_behaviours.append(agent_instance.comport_ident)
            message = ACLMessage(ACLMessage.REQUEST)
            message.set_protocol(ACLMessage.FIPA_REQUEST_PROTOCOL)
            agent_instance.add_all(message)
            message.set_content('CONNECTION')
            message.set_system_message(is_system_message=True)

            agent_instance.comport_conn_verify = CompConnectionVerify(agent_instance, message)
            agent_instance.comport_send_conn_messages = ComportSendConnMessages(agent_instance, message, 10.0)
            agent_instance.comport_conn_verify_timed = ComportVerifyConnTimed(agent_instance, 20.0)

            agent_instance.system_behaviours.append(agent_instance.comport_conn_verify)
            agent_instance.system_behaviours.append(agent_instance.comport_send_conn_messages)
            agent_instance.system_behaviours.append(agent_instance.comport_conn_verify_timed)
            # Set it
            agent_manager = agent_instance

        agent_list.append(agent_instance)
    assert agent_manager, "Agents should choose an ams."
    # On Start the agent
    reactor.suggestThreadPoolSize(30)
    for agent in agent_list:
        # Register agent in ams
        if agent != agent_manager:
            # Update the ams in another agent.
            agent.comport_connection = CompConnection(agent)
            agent.system_behaviours.append(agent.comport_connection)
            # SubscribeBehaviour
            message = ACLMessage(ACLMessage.SUBSCRIBE)
            message.set_protocol(ACLMessage.FIPA_SUBSCRIBE_PROTOCOL)
            ams_aid = agent_manager.aid
            message.add_receiver(ams_aid)
            message.set_content('IDENT')
            message.set_system_message(is_system_message=True)
            agent.comport_ident = SubscribeBehaviour(agent, message)
            agent.system_behaviours.append(agent.comport_ident)
            agent.update_ams(agent_manager.ams)
            # Table
            agent_info = AgentInfo(name=ams_aid.name,
                                   host=ams_aid.host,
                                   port=ams_aid.port,
                                   delta=datetime.now())
            agent.agent_factory.table.add(agent_info)
        # Start it
        agent.on_start()
        ILP = reactor.listenTCP(agent.aid.port, agent.agent_factory)
        agent.ILP = ILP
    # del agent_list

    # Run Agent in async
    reactor.run()


if __name__ == '__main__':
    start_agent(args.config_path)

"""
    launch the agent.
"""
import importlib
import sys

from config import ConfigHandler
from wise_agent.agents.agent import Agent
import argparse

parser = argparse.ArgumentParser()  # 添加参数
parser.add_argument('--config_path', help='Config file path', default="example_launch_config.json")
args = parser.parse_args()


def start_agent(config_path: str, agent_class=Agent, init_behaviour_list: list = None):
    """
        Start a Agent.
    Args:
        config_path: config for an agent
        agent_class: Agent class
        init_behaviour_list: list

    Returns:

    """
    config = ConfigHandler(config_path)
    root_dir = config.get("root_dir")
    sys.path.append(f"{root_dir}/wise_agent/behaviours")
    aid = config.get_aid()
    # assert isinstance(agent_class, Agent), "`agent_class` should be an Agent."
    agent = agent_class(aid)
    agent.config_handler = config
    # behaviour in agent
    if init_behaviour_list:
        new_behaviours = []
        for b in init_behaviour_list:
            new_behaviours.append(b(agent))
        agent.add_behaviours(new_behaviours)
    # behaviour in config
    behaviours = config.get("behaviours")
    agent_behaviours = []
    try:
        for name, behaviour in behaviours.items():
            behaviour_module = importlib.import_module(behaviour.get("import_path"))
            behaviour_class = getattr(behaviour_module, name)
            agent_behaviours.append(behaviour_class(agent))
        agent.add_behaviours(agent_behaviours)
        agent.on_start(config)
    except AttributeError:
        raise


if __name__ == '__main__':
    start_agent(args.config_path)

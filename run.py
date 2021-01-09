"""
    launch the agent.
"""
import importlib
import sys

sys.path.append("C:\\Users\\bobo/wise_agent_1/wise_agent/behaviours")
print(sys.path)
from wise_agent.config import ConfigHandler
from wise_agent.agents.agent import Agent


class MainAgent(Agent):
    def __init__(self, aid):
        super(MainAgent, self).__init__(aid)


def start_agent(config_path: str):
    config = ConfigHandler(config_path)
    aid = config.get_aid()
    agent = MainAgent(aid)
    agent.config_handler = config
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
    url = "C:\\Users\\bobo\\.wiseai\\wise_agent_1\\agent_config.json"
    start_agent(url)

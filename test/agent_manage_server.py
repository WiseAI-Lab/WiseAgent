"""
    Agent Manege Server
    Manage the Agent Table
"""
from wgent import Agent


class AMS(Agent):
    def __init__(self):
        name = 'ams@localhost:9092@test'
        super(AMS, self).__init__(name)

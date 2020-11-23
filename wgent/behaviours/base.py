"""
Behavier is a important part of agent.
"""
import abc
from .protocols import Behaviour


class RLBehaviour(Behaviour):
    """
     RL Behaviour should contains some special function.
     But I don't know now.
    """
    pass


class Learner(RLBehaviour):
    def __init__(self):
        super(Learner).__init__()


class Actor(RLBehaviour):
    def __init__(self):
        super(Actor).__init__()

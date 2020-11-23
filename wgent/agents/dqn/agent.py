from wgent.agents import Agent
from tianshou.policy.modelfree import dqn
import torch
from torch import nn
from wgent.behaviours.networks import ResNet, BasicBlock
from tianshou.policy import DQNPolicy
import argparse
from tianshou.utils.net.common import Net
from wgent.behaviours.rl.rl_tianshou.DQNBehaviours import LearnerBehaviour, ActorBehaviour

def get_args():
    parser = argparse.ArgumentParser()
    # the parameters are found by Optuna
    parser.add_argument('--task', type=str, default='LunarLander-v2')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--eps-test', type=float, default=0.05)
    parser.add_argument('--eps-train', type=float, default=0.73)
    parser.add_argument('--buffer-size', type=int, default=100000)
    parser.add_argument('--lr', type=float, default=0.013)
    parser.add_argument('--gamma', type=float, default=0.99)
    parser.add_argument('--n-step', type=int, default=4)
    parser.add_argument('--target-update-freq', type=int, default=500)
    parser.add_argument('--epoch', type=int, default=10)
    parser.add_argument('--step-per-epoch', type=int, default=5000)
    parser.add_argument('--collect-per-step', type=int, default=16)
    parser.add_argument('--batch-size', type=int, default=128)
    parser.add_argument('--layer-num', type=int, default=1)
    parser.add_argument('--training-num', type=int, default=10)
    parser.add_argument('--test-num', type=int, default=100)
    parser.add_argument('--logdir', type=str, default='log')
    parser.add_argument('--render', type=float, default=0.)
    parser.add_argument(
        '--device', type=str,
        default='cuda' if torch.cuda.is_available() else 'cpu')
    return parser.parse_args()


class DQNAgent(Agent):
    def __init__(self):
        self.args = get_args()
        LearnerBehaviour(self)
        ActorBehaviour(self)
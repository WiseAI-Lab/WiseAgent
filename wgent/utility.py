import copy
import time
from datetime import datetime

import click


class BehaviourError(BaseException):
    pass


class AgentError(BaseException):
    pass


class AgentStoppedError(AgentError):
    pass


def display_message(name, data):
    """
        Method do displsy message in the console.
    """
    date = datetime.now()
    date = date.strftime('%d/%m/%Y %H:%M:%S.%f')[:-3]
    click.echo(click.style('[{}] {} --> '.format(name, date), fg='green') + str(data))


def string2timestamp(value):
    try:
        d = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
        t = d.timetuple()
        timestamp = int(time.mktime(t))
        timestamp = float(str(timestamp) + str("%06d" % d.microsecond)) / 1000000
        return timestamp
    except ValueError as e:
        d = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        t = d.timetuple()
        timestamp = int(time.mktime(t))
        timestamp = float(str(timestamp) + str("%06d" % d.microsecond)) / 1000000
        return timestamp


def start_loop(agents):
    if not isinstance(agents, list):
        agents = [agents]
    for agent in agents:
        cur_agent = copy.copy(agents)
        cur_agent.remove(agent)
        agent.on_start()

    while True:
        try:
            pass
        except KeyboardInterrupt:
            pass

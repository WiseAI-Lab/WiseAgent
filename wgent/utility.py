import copy
from datetime import datetime

import click


class BehaviourError(Exception):
    pass


def display_message(name, data):
    """
        Method do displsy message in the console.
    """
    date = datetime.now()
    date = date.strftime('%d/%m/%Y %H:%M:%S.%f')[:-3]
    click.echo(click.style('[{}] {} --> '.format(name, date), fg='green') + str(data))
    # print('[' + name + '] ' + date + str(data))


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
            for a in agents:
                a.terminate()
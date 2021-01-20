import click
import signal
import subprocess
import multiprocessing
import shlex
import time
import json
import datetime
import sys

def signal_handler(signal, frame):
    global interrupted
    interrupted = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
interrupted = False


def run_config_file(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    try:
        config = json.load(open(value))
    except FileNotFoundError:
        click.echo(click.style('Load Configuration for WiseAgent!', fg='red'))
        ctx.exit()

    main(config)
    ctx.exit()


def main(config):
    global interrupted

    click.clear()
    click.echo(click.style('''
        This is
         ____   _    ____  _____ 
        |  _ \ / \  |  _ \| ____|
        | |_) / _ \ | | | |  _|  
        |  __/ ___ \| |_| | |___ 
        |_| /_/   \_\____/|_____|

        Python Agent Development framework   
        ''', fg='green'))
    click.echo(click.style('''
        WiseAgent is a free software under development by:
        - Dongbox JiaYing University in China
        https://github.com/WiseAI-Lab/WiseAgent''', fg='blue'))

    agent_files = config.get('agent_files')
    if agent_files is None:
        click.echo(click.style('attribute agent_file is mandatory', fg='red'))
        return

    num = config.get('num')
    if num is None:
        num = 1

    port = config.get('port')
    if port is None:
        port = 2000

    processes = list()

    # -------------------------------------------------------------
    # Set an Agent as AMS - Agent Manager System
    # -------------------------------------------------------------
    session = config.get('session')
    pade_ams = config.get('ams')

    # TODO Set an agent as ams

    # -------------------------------------------------------------
    # Initial all agents - WiseAgent
    # -------------------------------------------------------------
    time.sleep(3.0)
    port_ = port
    for agent_file in agent_files:
        for i in range(num):
            commands = 'python {} {}'.format(agent_file, port_)
            if sys.platform == 'win32':
                commands = shlex.split(commands, posix=False)
            else:
                commands = shlex.split(commands)
            p = subprocess.Popen(commands, stdin=subprocess.PIPE)
            processes.append(p)
            time.sleep(0.5)
            port_ += 1

    while True:
        time.sleep(2.0)

        if interrupted:
            click.echo(click.style('\nStoping WiseAgent...', fg='red'))
            for p in processes:
                p.kill()
            break


@click.group()
def cmd():
    pass


@cmd.command()
@click.argument('agent_files', nargs=-1)
@click.option('--num', default=1)
@click.option('--port', default=2000)
@click.option('--config_file', is_eager=True, expose_value=False, callback=run_config_file)
def start(num, agent_files, port, secure, pade_ams, pade_web, pade_sniffer, username, password):
    config = dict()
    config['agent_files'] = agent_files
    config['pade_sniffer']['host'] = 'localhost'
    config['pade_sniffer']['port'] = 8001
    config['pade_web'] = dict()
    config['pade_web']['active'] = pade_web
    config['pade_web']['host'] = 'localhost'
    config['pade_web']['port'] = 5000

    main(config)

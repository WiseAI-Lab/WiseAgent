from __future__ import annotations
import copy
import json
import time
import logging
import os
from datetime import datetime
import click

# Env Config.
from wgent.config import DEFAULT_AGENT_CONFIG

WGENT_LOG_KEY = 'WGENT_LOG'
WGENT_LOG_FILE_KEY = 'WGENT_LOG_FILE'


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


def string2timestamp(value: str):
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


def start_loop(agents: list):
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


def read_config():
    """
        Read the config from file if exist else generate.
    """
    config_path = DEFAULT_AGENT_CONFIG.CONFIG_PATH
    if os.path.exists(DEFAULT_AGENT_CONFIG):
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                config_content = json.loads(content)
        except Exception as e:
            logger.info(f"Config {e}...Regenerate...")
            config_content = DEFAULT_AGENT_CONFIG
    else:
        config_content = DEFAULT_AGENT_CONFIG
        try:
            with open(config_path, 'w') as f:
                f.write(config_content)
        except Exception as e:
            raise IOError(f"Cannot write the agent config to {config_path}")
    return config_content


def get_logger(name: str) -> logging.Logger:
    """
    configured Loggers
    """
    WGENT_LOG = os.environ.get(WGENT_LOG_KEY, 'INFO')

    log_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 1.create logger and set level to debug
    logger = logging.getLogger(name)
    logger.handlers = []
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # create file handler and set level to debug
    if WGENT_LOG_FILE_KEY in os.environ:
        filepath = os.environ[WGENT_LOG_FILE_KEY]
    else:
        base_dir = './logs'
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)

        time_now = datetime.now()
        time_format = '%Y-%m-%d-%H-%M'

        filepath = f'{base_dir}/log-{time_now.strftime(time_format)}.txt'

    file_handler = logging.FileHandler(filepath, 'a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    # create console handler and set level to info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(WGENT_LOG)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    return logger


logger = get_logger("wgent_log")

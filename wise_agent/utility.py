from __future__ import annotations
import random
import time
import logging
import os
from asyncio import Future
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from typing import Dict, Union, Any

import click
# Env Config.

WGENT_LOG_KEY = 'WISE_AGENT_LOG'
WGENT_LOG_FILE_KEY = 'WISE_AGENT_LOG_FILE'


def display_message(name, data):
    """
        Method do display message in the console.
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


def random_string(length: int = 5):
    """
        Generate ranfom string in 'abcdefghijklmnopqrstuvwxyz' by length.
        >>> assert len(random_string(10)) == 10
    """
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    characters = random.sample(alphabet, length)
    return "".join(characters)


def start_task(running_tasks: Dict[str, Future],
               pool_executor: Union[ThreadPoolExecutor, ProcessPoolExecutor],
               target: Any,
               *args,
               ) -> Dict[str, Future]:
    """
        Start a worker of main by "concurrent.futures.Executor".
    :param running_tasks: List
    :param pool_executor: ThreadPoolExecutor or ProcessPoolExecutor
    :param target: Any
    :param args: Any
    :return:
    """

    def _future_done_callback(task_name: str, future: Future):
        """
            Check the situation of task
        :param task_name: str
        :param future: Future
        :return:
        """
        nonlocal running_tasks
        exception = future.exception()
        if exception:
            logger.exception("{} :::: {}".format(task_name, exception))

        try:
            running_tasks.pop(task_name)
        except KeyError:
            logger.exception("The task:{} is not in Brain._running_tasks".format(task_name))

    future: Future = pool_executor.submit(target, *args)  # concurrent.futures.Future
    # Define a key.
    task_name: str = f"random_{random_string(20)}_{target.__class__.__name__ + getattr(target, '__name__')}_{int(time.time())}"
    running_tasks[task_name] = future
    func = partial(_future_done_callback, task_name)
    # Add callback function.
    future.add_done_callback(func)
    # Add to a self-definition task dict.
    return running_tasks


def get_logger(name: str) -> logging.Logger:
    """
    configured Loggers
    """
    wise_agent_log = os.environ.get(WGENT_LOG_KEY, 'INFO')

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
    console_handler.setLevel(wise_agent_log)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    return logger


logger = get_logger("wgent_log")



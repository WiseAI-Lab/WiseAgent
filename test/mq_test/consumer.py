import json

from kafka import KafkaConsumer
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


def call_func(message):
    print(message)


def new_consumer():
    consumer = KafkaConsumer(bootstrap_servers='115.159.153.135:32768')
    consumer.subscribe(['topic1'])
    for msg in consumer:
        call_func(msg)


if __name__ == '__main__':
    t_exe = ThreadPoolExecutor(max_workers=5)
    t_exe.submit(new_consumer)
    while True:
        pass
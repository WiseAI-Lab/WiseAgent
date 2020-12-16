from kafka import KafkaConsumer
from wgent.behaviours.transport import AgentTable


def call_func(message):
    print(message)


def new_consumer(receivers):
    while True:
        for server_host, topics in receivers.items():
            consumer = KafkaConsumer(bootstrap_servers=server_host, group_id="Test", client_id="consumer_2", )
            consumer.subscribe(topics)
            records = consumer.poll(0)
            print(records.values())


if __name__ == '__main__':
    receivers = AgentTable().return_as_sub()
    new_consumer(receivers)

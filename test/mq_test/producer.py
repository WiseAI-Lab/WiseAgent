import json
from kafka import KafkaProducer
from wgent.acl.messages import ACLMessage
from wgent.behaviours.transport import AgentTable


def new_producer(receivers):
    for server_host, topics in receivers.items():
        msg = ACLMessage()
        producer = KafkaProducer(bootstrap_servers=server_host,
                                 value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        for _ in range(1):
            future = producer.send(topics[0], msg.encode("dict"))
            print(future.is_done)
        producer.flush()


if __name__ == '__main__':
    receivers = AgentTable().return_as_sub()
    new_producer(receivers)

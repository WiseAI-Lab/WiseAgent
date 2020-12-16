from confluent_kafka import Producer
from wgent.acl.messages import ACLMessage
from wgent.behaviours.transport import AgentTable


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


def new_producer(receivers):
    for server_host, topics in receivers.items():
        msg = ACLMessage()
        p = Producer({'bootstrap.servers': server_host, 'group.id': "Test", 'client.id': "producer_1"})
        p.produce(topics[0], msg.encode("json"), callback=delivery_report)
        p.flush()


if __name__ == '__main__':
    receivers = AgentTable().return_as_sub()
    new_producer(receivers)

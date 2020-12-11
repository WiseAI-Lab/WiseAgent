import json
from kafka import KafkaProducer
from wgent.acl.messages import ACLMessage
msg = ACLMessage()
producer = KafkaProducer(bootstrap_servers='localhost:32769', value_serializer=lambda v: json.dumps(v).encode('utf-8'))
for _ in range(1):
    future = producer.send('mytopic', msg.as_dict())
    print(future.is_done)
producer.flush()
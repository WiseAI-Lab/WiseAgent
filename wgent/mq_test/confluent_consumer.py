from confluent_kafka import Consumer


c = Consumer({
    'bootstrap.servers': '110.43.54.253:1025',
    'group.id': 'test',
    'auto.offset.reset': 'earliest'
})

c.subscribe(['topic1'])

while True:
    msg = c.poll(1.0)

    if msg is None:
        continue
    if msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue

    print('Received message: {}'.format(msg.value().decode('utf-8')))

c.close()
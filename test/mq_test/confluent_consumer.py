from confluent_kafka import Consumer


c = Consumer({
    'bootstrap.servers': '115.159.153.135:32771',
    'group.id': 'Test',
    'auto.offset.reset': 'earliest',
    'client.id': "consumer_1"
})

c.subscribe(['topic1'])

while True:
    msg = c.poll(0)

    if msg is None:
        continue
    if msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue

    print('Received message: {}'.format(msg.value().decode('utf-8')))

c.close()
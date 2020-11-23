from kafka import KafkaClient
from kafka import KafkaAdminClient, KafkaClient

admin_client = KafkaAdminClient(bootstrap_servers='localhost:9092', client_id='admin')
# client = KafkaClient(bootstrap_servers='localhost:9092')
# client = KafkaClient(bootstrap_server='localhost:9092')
cv = admin_client.to
print(cv)
# future = client.add_topic('test1')
# state = future.succeeded()
# print(state)
# print(future.is_done)
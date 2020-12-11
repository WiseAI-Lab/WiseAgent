from kafka.cluster import ClusterMetadata


config = ClusterMetadata.DEFAULT_CONFIG
config['bootstrap_servers'].append("localhost:9092")
cluster = ClusterMetadata(**config)
print(cluster.brokers())
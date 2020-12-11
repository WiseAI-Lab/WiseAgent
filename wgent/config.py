import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), ".agent_config.json")

VERSION = 0.1
AUTHOR = "dongbox"
DESCRIPTION = "Type your agent description here."
ENVIRONMENT = "Development"
# TODO: Change it to a request and get below info.
SYSTEM_NAME = "system"
SYSTEM_ADDRESS = "115.159.153.135"
SYSTEM_PORT = "32769"
SYSTEM_TOPIC = "topic1"

DEFAULT_AGENT_CONFIG = {
    'version': VERSION,
    'author': AUTHOR,
    'description': DESCRIPTION,
    'environment': ENVIRONMENT,
    'system_name': SYSTEM_NAME,
    'system_address': SYSTEM_ADDRESS,
    'system_port': SYSTEM_PORT,
    'system_topic': SYSTEM_TOPIC,
}

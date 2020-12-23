import copy
import json
import os
from typing import Dict, Optional

from wise_agent.core import Savable
from wise_agent.utility import logger


# Config Type
class Config:
    def __init__(self, configs: Optional[Dict] = None):
        super(Config, self).__init__()
        if configs is None:
            self.version = 0.1
            self.author = "dongbox"
            self.description = "Type your agent description here."
            self.environment = "Development"
            # TODO: Change it to a request and get below info.
            self.system_name = "system"
            self.system_address = "115.159.153.135"
            self.system_port = "32771"
            self.system_topic = "topic1"
            self.default_pool_size = 5
            self.is_process_pool = False
        else:
            self.__dict__ = copy.copy(configs)


class ConfigHandler(Savable):
    """
        Handle the config reader and writer.
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            self._default_path = os.path.join(os.path.dirname(__file__), ".agent_config.json")
        else:
            self._default_path = config_path
        self._is_updated = True  # update in save and read.
        self._config_cache = None  # control the IO.

    def _read_config(self) -> dict:
        """
            Read the config from file if exist else generate.
        """
        if os.path.exists(self._default_path):
            try:
                with open(self._default_path, 'r') as f:
                    content = f.read()
                    config_content = Config(json.loads(content))
            except Exception as e:
                logger.info(f"Config {e}...Regenerate...")
                config_content = self._save_config(Config())
        else:
            # generate a new config
            config_content = self._save_config(Config())
        return config_content

    def read(self):
        """
            Upper method for ConfigHandler to read the config.
        """
        if self._is_updated:
            self._is_updated = False
            self._config_cache = self._read_config()
        return self._config_cache

    def _save_config(self, config):
        """
            save a config to defined path.
        """
        try:
            content = config.__dict__
            with open(self._default_path, 'w') as f:
                json.dump(content, f)
            self._is_updated = True
            logger.info("Successfully Write the config.")
            return config
        except Exception as e:
            raise IOError(f"Cannot write the agent config to {self._default_path}, Error: {e}")

    def save(self, config):
        """
            Upper methodSave a config.
        """
        self._save_config(config)

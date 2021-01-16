import json
import os

from wise_agent.core import Savable
from wise_agent.utility import logger


class ConfigHandler(Savable):
    """
        Handle the config reader and writer.
    """

    def __init__(self, config_path: str):
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        except Exception as e:
            raise IOError(f"Cannot load config: {e}")
        self._config = self.init_check(config_data)
        self.config_path = self._config.get("config_path")

    @staticmethod
    def get_from_unknown_object(data):
        try:
            info = eval(data)
        except TypeError:
            info = data
        return info

    def init_check(self, config_data: dict):
        # Check agent name
        try:
            agent_name = config_data.get("agent_name", None)
            if not agent_name:
                top_name = config_data.get("name")
                repo_name = config_data.get("repository").get("name")
                agent_name = f"{repo_name}_{top_name}"
                config_data["agent_name"] = agent_name
        except TypeError:
            raise TypeError("")
        # Load configuration
        agent_configuration = self.get_from_unknown_object(config_data.get("configuration"))
        # Check Launch_types
        try:
            launch_types = agent_configuration.get("launch_types", None)
            assert isinstance(launch_types, list), "`launch_types` should be defined and is a list."

            if "server" in launch_types:
                server = agent_configuration.get("server")
                assert isinstance(server, dict)
                host = server.get("host", None)
                if not host or len(host) == 0:
                    agent_configuration["server"]["host"] = "localhost"
                port = server.get("port", None)
                if not port or len(port) == 0:
                    agent_configuration["server"]["port"] = 8989
                agent_configuration["if_server"] = True
            if "api" in launch_types:
                agent_configuration["if_api"] = True

            if "mq" in launch_types:
                # Confirm the system config
                mq_config = agent_configuration.get("mq_config")
                assert isinstance(mq_config, dict), "`mq_config` Error."
                # "system_name", "system_address", "system_port", "system_topic", "username", "password"
                mq_config_pre = ["sub_info", "pub_info"]  # self
                assert len(set(mq_config_pre).intersection(set(mq_config))) == len(mq_config_pre), \
                    f"`mq_config` should contains all information in {mq_config_pre}"
                agent_configuration["if_mq"] = True
            config_data["configuration"] = agent_configuration
        except Exception as e:
            raise ValueError(f"`launch_types` Error, {e}")

        # Check Behaviours
        behaviours = config_data.get("behaviours")
        assert isinstance(behaviours, dict)
        try:
            new_behaviours = {}
            for name, behaviour in behaviours.items():
                bev_pre = ["pool_size", "process_pool"]
                configuration = self.get_from_unknown_object(behaviour.get("configuration"))
                assert len(set(bev_pre).intersection(set(configuration.keys()))) == len(bev_pre), \
                    f"config in behaviour should contains all information in {bev_pre}"
                behaviour["configuration"] = configuration
                new_behaviours[name] = behaviour
            config_data["behaviours"] = new_behaviours

        except Exception as e:
            raise ValueError(e)
        return config_data

    def _read_config(self):
        """
            Read the config from file if exist else generate.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    content = f.read()
                    config_content = json.loads(content)
            except Exception as e:
                logger.info(f"Config {e}...Regenerate...")
                config_content = self._save_config(self._config)
        else:
            logger.info(f"Config not exist...Regenerate from current config...")
            # generate a new config
            config_content = self._save_config(self._config)

        return config_content

    def update(self):
        """
            Upper method for ConfigHandler to read the config.
        """
        config_content = self._read_config()
        self._config = config_content

    def get_aid(self):
        """
        Get the aid from config.
        Returns:

        """
        agent_name = self._config.get("agent_name")
        if_server = self._config.get("if_server", False)
        if_mq = self._config.get("if_mq", False)
        # assert if_api and if_http and if_mq, "Config should contains host and port."
        if if_server:
            data = self._config.get("server")
            host = data.get("host")
            port = data.get("port")
            server = f"{host}:{port}"
        elif if_mq:
            mq_config = self._config.get("mq_config")
            host = mq_config.get("host")
            port = mq_config.get("port")
            server = f"{host}:{port}"
        else:
            server = "localhost:8989"
        aid = f"{agent_name}@{server}"
        return aid

    def _save_config(self, config):
        """
            save a config to defined path.
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
            logger.info("Successfully Write the config.")
            return config
        except Exception as e:
            logger.exception(f"Error occur when saving the config: {e}")

    @property
    def config(self):
        return self._config

    def save(self, value):
        self._save_config(value)

    def get(self, value: str):
        """
        Get the value split by '.'
        Args:
            value:

        Returns:

        """

        data = None
        for v in value.split('.'):
            if data:
                data = data.get(v)
            else:
                data = self._config.get(v)
        return data

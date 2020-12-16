"""

"""
import contextlib
import importlib
import json
import logging
import os
from typing import Dict
import requests
import sys
import tempfile
import traceback
import zipfile

from os.path import join

# all agent and behaviours will be stored in temp directory
BASE_TEMP_DIR = tempfile.mkdtemp()
AGENT_DIRECTORY_PATH = join(BASE_TEMP_DIR, "wise_agent")

logger = logging.getLogger(__name__)

# web server.
DJANGO_SERVER = os.environ.get("DJANGO_SERVER", "localhost")
DJANGO_SERVER_PORT = os.environ.get("DJANGO_SERVER_PORT", "8000")

# location for wise-agent.
AGENT_DATA_BASE_DIR = join(AGENT_DIRECTORY_PATH, "agent_{agent_id}")
BEHAVIOURS_DATA_BASE_DIR = join(AGENT_DIRECTORY_PATH, "behaviours")

# wise_agent.agent_{agent_id}.on_start() module
AGENT_IMPORT_STRING = "wise_agent.agent_{agent_id}"
# wise_agent.behaviours.{behaviour_name}.{behaviour_name} class
BEHAVIOURS_IMPORT_STRING = "wise_agent.behaviours.{behaviour_name}"

AGENT_SCRIPTS = {}
BEHAVIOUR_SCRIPTS = {}

# API URL in 'Wise-agent'.
URLS = {
    "wise_agent": "...",
}


# ----------------------- Utility --------------------------
@contextlib.contextmanager
def stdout_redirect(where):
    sys.stdout = where
    try:
        yield where
    finally:
        sys.stdout = sys.__stdout__


@contextlib.contextmanager
def stderr_redirect(where):
    sys.stderr = where
    try:
        yield where
    finally:
        sys.stderr = sys.__stderr__


# -----------------------Create a package--------------------------
def create_dir(directory):
    """
        Creates a directory if it does not exists
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_dir_as_python_package(directory: str):
    """
    Create a directory and then makes it a python
    package by creating `__init__.py` file.

    Args:
        directory: str

    Returns:

    """
    create_dir(directory)
    init_file_path = join(directory, "__init__.py")
    with open(init_file_path, "w") as init_file:  # noqa
        # to create empty file
        pass


# ----------------------- Internet request-------------------------
def download_and_extract_file(url: str, download_location: str):
    """
    Function to extract download a file.

    Args:
        url: str, Get from 'url' by 'requests'.
        download_location: str,  It should include name of file as well.

    Returns:

    """
    try:
        response = requests.get(url)
    except Exception as e:
        logger.error("Failed to fetch file from {}, error {}".format(url, e))
        traceback.print_exc()
        response = None

    if response and response.status_code == 200:
        with open(download_location, "wb") as f:
            f.write(response.content)


def download_and_extract_zip_file(url: str, download_location: str, extract_location: str):
    """
    Function to extract download a zip file, extract it and then removes the zip file.

    Args:
        url: str, Get from 'url' by 'requests'.
        download_location: str, It should include name of file as well.
        extract_location: str, Store the file.

    Returns:

    """
    try:
        response = requests.get(url)
    except Exception as e:
        logger.error("Failed to fetch file from {}, error {}".format(url, e))
        response = None

    if response and response.status_code == 200:
        with open(download_location, "wb") as f:
            f.write(response.content)
        # extract zip file
        zip_ref = zipfile.ZipFile(download_location, "r")
        zip_ref.extractall(extract_location)
        zip_ref.close()
        # delete zip file
        try:
            os.remove(download_location)
        except Exception as e:
            logger.error(
                "Failed to remove zip file {}, error {}".format(
                    download_location, e
                )
            )
            traceback.print_exc()


def return_url_per_environment(url: str) -> str:
    """
    Ensure the base url in 'Wise-Agent'

    Args:
        url: str

    Returns:

    """
    base_url = "http://{0}:{1}".format(DJANGO_SERVER, DJANGO_SERVER_PORT)
    url = "{0}{1}".format(base_url, url)
    return url


def get_request_headers():
    """
    Do nothing.

    Returns:

    """
    return {}


def make_request(url, method, data=None):
    headers = get_request_headers()
    if method == "GET":
        try:
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        return response.json()

    elif method == "PUT":
        try:
            response = requests.put(url=url, headers=headers, data=data)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.exception(
                "The worker is not able to establish connection with EvalAI due to {}"
                % (response.json())
            )
            raise
        except requests.exceptions.HTTPError:
            logger.exception(
                f"The request to URL {url} is failed due to {response.json()}"
            )
            raise
        return response.json()

    elif method == "PATCH":
        try:
            response = requests.patch(url=url, headers=headers, data=data)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        except requests.exceptions.HTTPError:
            logger.info(
                f"The request to URL {url} is failed due to {response.json()}"
            )
            raise
        return response.json()

    elif method == "POST":
        try:
            response = requests.post(url=url, headers=headers, data=data)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        except requests.exceptions.HTTPError:
            logger.info(
                f"The request to URL {url} is failed due to {response.json()}"
            )
            raise
        return response.json()


def read_file_content(file_path):
    """
    Get a file content.
    Args:
        file_path: str

    Returns:

    """
    with open(file_path, "r") as obj:
        file_content = obj.read()
        if not file_content:
            file_content = " "
        return file_content


# ---------------------- Generate agent----------------------------
def load_agent(agent_id: int, request_urls: Dict):
    """
    Load a agent file from url.
    Args:
        agent_id:
        request_urls:

    Returns:

    """
    download_location = AGENT_DATA_BASE_DIR.format(agent_id)
    create_dir_as_python_package(download_location)

    agent_url = request_urls.get('agent')
    download_and_extract_file(agent_url, download_location)

    try:
        # import the challenge after everything is finished
        challenge_module = importlib.import_module(
            AGENT_IMPORT_STRING.format(agent_id=agent_id)
        )
        AGENT_SCRIPTS["agent_{}".format(agent_id)] = challenge_module
    except Exception:
        logger.exception(
            "Exception raised while creating Python module for agent_id: %s"
            % ("agent_{}".format(agent_id))
        )
        raise


def load_behaviours(request_urls: Dict):
    """
    Load behaviours into directory from urls.
    Args:
        request_urls:

    Returns:

    """
    create_dir_as_python_package(BEHAVIOURS_DATA_BASE_DIR)

    behaviour_urls: Dict[str, str] = request_urls.get('behaviours')
    for behaviour_name, bev_url in behaviour_urls.items():
        download_location = os.path.join(BEHAVIOURS_DATA_BASE_DIR, behaviour_name)
        download_and_extract_file(bev_url, download_location)
        try:
            # import the challenge after everything is finished
            behaviour_module = importlib.import_module(
                BEHAVIOURS_IMPORT_STRING.format(behaviour_name=behaviour_name)
            )
            BEHAVIOUR_SCRIPTS[behaviour_name] = behaviour_module
        except Exception:
            logger.exception(
                "Exception raised while creating Python module for behaviour_name: %s"
                % behaviour_name
            )
            raise


# ----------------------- Main ----------------------------------
def run_agent(agent_id: str):
    # log file.
    temp_run_dir = join(AGENT_DATA_BASE_DIR, "run")
    create_dir(temp_run_dir)

    stdout_file = join(temp_run_dir, "temp_stdout.txt")
    stderr_file = join(temp_run_dir, "temp_stderr.txt")

    stdout = open(stdout_file, "a+")
    stderr = open(stderr_file, "a+")

    try:
        logger.info(
            "{} starting...".format(agent_id)
        )

        with stdout_redirect(stdout), stderr_redirect(stderr):
            # Use the behaviours to param that the on_start will dynamic load the class and init it.
            AGENT_SCRIPTS["agent_id"].on_start(BEHAVIOUR_SCRIPTS["agent_id"])

    except Exception:
        stderr.write(traceback.format_exc())
        stdout.close()
        stderr.close()
        logger.exception(f"Agent Exec out.\nCheck the {stdout_file} and {stderr_file}")


def main(agent_id: int, credit: str):
    """
    Project Structure:
    - temp_dir
        - wise_agent
            - agent_id.py
                def on_start(): ... # It's the same in all agents.
            - behaviours
                BrainBehaviour.py
                    class BrainBehaviour(...): ...
                TransportBehaviour.py
                    class TransportBehaviour(...): ...
                ...
    # 1. User define agent in website that we will store their config in database.

    # ---------------BehaviourCategory-------------
    # id - name - parent_id - create_time

    # ---------------Behaviours--------------------
    # id - name - prerequisite_behaviours - prerequisite_agents - parent_behaviour - behaviour_category
    # - url - create_time  - author - description - is_office

    # ---------------AgentCategory-----------------
    # id - name - parent_id - create_time

    # ---------------BasicAgent--------------------
    # id - name - prerequisite_behaviours_category - behaviours - parent_agent - agent_category - url
    # - create_time - author - description - is_office

    # ---------------InitialAgent---------------------
    # - id - name - behaviours - basic_agent - credit - create_time - status
    Args:
        agent_id:
        credit:

    Returns:

    """
    print("Generate a new agent from basic agent and behaviour")
    # Make the basic directory.
    create_dir_as_python_package(AGENT_DIRECTORY_PATH)
    sys.path.append(AGENT_DIRECTORY_PATH)
    # Get the agent config by id and credit
    # request_url: dict{"agent": {"OnlineAgent": "..."},
    # "behaviours": {"BrainBehaviour":"...", "TransportBehaviour":"..."}}
    request_path = URLS.get("wise_agent")
    content = make_request(request_path, "POST", {"agent_id": agent_id, "credit": credit})
    try:
        request_urls = json.loads(content)
    except TypeError:
        raise
    # Load Agent
    load_agent(agent_id, request_urls)
    # Load Behaviours
    load_behaviours(request_urls)
    # content_dict

    # 2. We will authenticate the credit that they support.


if __name__ == "__main__":
    main()
    logger.info("Quitting Submission Worker.")

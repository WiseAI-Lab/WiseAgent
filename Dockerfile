# TODO: Not finishsed now as the agent are testing.
FROM python3.7

ADD ../wgent /wgent
WORKDIR /wgent

# pip 源
RUN pip install -r requirement.txt
CMD ["python agent.py --config {config_path} --port 7979"]
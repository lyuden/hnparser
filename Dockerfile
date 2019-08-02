FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    python3.7 \
    python3-setuptools \
    python3-pip \
    python3.7-venv

RUN mkdir /hnparser/
RUN python3.7 -m venv /hnparser/venv/

COPY requirements.txt /hnparser/


RUN /hnparser/venv/bin/pip install --upgrade pip
RUN /hnparser/venv/bin/pip install -r /hnparser/requirements.txt

WORKDIR /hnparser/

RUN cat /etc/hosts
RUN mkdir /setup/
COPY db_setup.py /setup/
COPY start.sh /setup

CMD ["/bin/bash","/setup/start.sh"]

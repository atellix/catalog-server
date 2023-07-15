FROM python:3.11-bullseye

RUN set -x \
    && apt-get update \
    && apt-get install -y locales vim \
    && echo -e 'LANG="en_US.UTF-8"\nLANGUAGE="en_US:en"\n' > /etc/default/locale \
    && cp /usr/share/i18n/SUPPORTED /etc/locale.gen \
    && dpkg-reconfigure -f noninteractive locales

RUN mkdir -p /usr/src/app/tracker
COPY requirements.txt /usr/src/app/
WORKDIR /usr/src/app
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

COPY src /usr/src/app
WORKDIR /usr/src/app/tracker


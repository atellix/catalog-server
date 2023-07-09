FROM python:3.9-buster

RUN set -x \
    && apt-get update \
    && apt-get install -y locales \
    && echo -e 'LANG="en_US.UTF-8"\nLANGUAGE="en_US:en"\n' > /etc/default/locale \
    && cp /usr/share/i18n/SUPPORTED /etc/locale.gen \
    && dpkg-reconfigure -f noninteractive locales

RUN mkdir -p /usr/src/build
WORKDIR /usr/src/build
RUN pip install --upgrade pip
RUN set -x \
    && git clone https://github.com/sqlcipher/sqlcipher.git sqlcipher \
    && cd sqlcipher \
    && ./configure --enable-tempstore=yes --prefix=/usr CFLAGS="-DSQLITE_HAS_CODEC" LDFLAGS="-lcrypto" \
    && make \
    && make install \
    && pip install git+https://github.com/mfrager/python-triplesec \
    && pip install git+https://github.com/mfrager/sqlalchemy@pysqlcipher3 \
    && pip install git+https://github.com/mfrager/flask-migrate@mfrager \
    && pip install git+https://github.com/tdhopper/pysqlcipher3

RUN set -x \
    && apt-get install -y vim

RUN set -x \
    && apt-get install -y unixodbc unixodbc-dev \
    && pip install git+https://github.com/mfrager/pyodbc.git@atellix

RUN mkdir -p /usr/src/build/virtodbc
COPY virtodbc.tar /usr/src/build/virtodbc/virtodbc.tar
RUN set -x \
    && cd /usr/src/build/virtodbc \
    && tar -xvf virtodbc.tar \
    && sh install.sh

RUN mkdir -p /usr/src/app/catalog
COPY requirements.txt /usr/src/app/
WORKDIR /usr/src/app
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

RUN set -x \
    && pip install git+https://github.com/mfrager/virtuoso-python.git@atellix2

COPY odbc.ini /etc/odbc.ini
COPY logging.cfg /usr/src/app/logging.cfg
COPY sql_tables /usr/src/app/sql_tables
COPY migrate.sh /usr/src/app/migrate.sh
COPY catalog /usr/src/app/catalog

#ARG githash
#RUN set -x \
#    && echo -n "$githash" > /usr/src/app/githash.txt
#RUN echo "Git Commit Hash: $githash"

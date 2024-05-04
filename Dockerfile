FROM python:3-stretch

WORKDIR /bbr-api

COPY requirements ./requirements/
RUN pip3 install -r requirements/production.txt

COPY app ./app/
COPY sdk ./sdk/
COPY doc ./doc/
COPY configuration ./configuration/
COPY migrations ./migrations/
COPY manage.py run.py entrypoint.sh alembic.ini run.py logging_config.ini ./

ENTRYPOINT [ "/bbr-api/entrypoint.sh" ]

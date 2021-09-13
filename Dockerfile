FROM python:3.9

RUN apt-get update
RUN apt-get install -y wkhtmltopdf
RUN rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=${PYTHONPATH}:${PWD}
RUN pip3 install poetry

RUN mkdir /app
COPY /src /app
COPY pyproject.toml /app
COPY runner.sh /app/runner.sh
RUN chmod +x /app/runner.sh
WORKDIR /app

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

ENTRYPOINT ["/app/runner.sh"]

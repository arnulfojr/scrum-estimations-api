FROM python:3.7-alpine

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install --disable-pip-version-check -r ./requirements.txt \
    && mkdir /app/out

COPY ./tests/ ./tests/

ENTRYPOINT ["/usr/local/bin/pytest"]

CMD ["--help"]

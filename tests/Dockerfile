FROM python:3.7-alpine

ENV PORT 5000

ENV APP_DIR "/app"

WORKDIR ${APP_DIR}

COPY ./requirements.txt ./requirements.txt
COPY ./requirements-test.txt ./requirements-test.txt

RUN apk add --no-cache build-base libffi-dev openssl-dev && \
    pip install --disable-pip-version-check -r ./requirements.txt && \
    pip install --disable-pip-version-check -r ./requirements-test.txt && \
    apk del build-base libffi-dev

COPY ./conf/ ./conf/

ENV PATH "${PATH}:${APP_DIR}/bin"
COPY ./bin/ ./bin/

ENV PYTHONPATH "${APP_DIR}/src"
COPY ./src/ ./src/
COPY ./tests/ ./tests/

ENTRYPOINT ["/usr/local/bin/pytest"]

CMD ["--help"]

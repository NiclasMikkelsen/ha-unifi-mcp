ARG BUILD_FROM=python:3.12-alpine
FROM ${BUILD_FROM}

# Endast stdlib används, så inget pip-steg behövs.
ENV PYTHONUNBUFFERED=1

COPY relay.py /relay.py
COPY run.sh /run.sh
RUN chmod 0755 /run.sh

ENTRYPOINT ["/run.sh"]

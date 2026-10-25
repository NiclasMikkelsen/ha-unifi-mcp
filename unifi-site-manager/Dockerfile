ARG BUILD_FROM=ghcr.io/enuno/unifi-mcp-server:latest
FROM ${BUILD_FROM}

USER root

COPY run.sh /run.sh
RUN chmod 0755 /run.sh

ENTRYPOINT ["/run.sh"]

ARG BUILD_FROM=ghcr.io/enuno/unifi-mcp-server:latest
FROM ${BUILD_FROM}

# HA-appar körs som root i sin egen container; upstream-imagen kör som uid 1000.
USER root

COPY run.sh /run.sh
RUN chmod 0755 /run.sh

ENTRYPOINT ["/run.sh"]

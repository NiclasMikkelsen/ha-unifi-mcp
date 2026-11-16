ARG BUILD_FROM=ghcr.io/enuno/unifi-mcp-server:latest
FROM ${BUILD_FROM}

USER root

COPY run.sh /run.sh
COPY healthcheck.py /healthcheck.py
RUN chmod 0755 /run.sh

# Ersätter upstream-kontrollen, som saknar run.sh:s miljö (se healthcheck.py).
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD ["/opt/venv/bin/python", "/healthcheck.py"]

ENTRYPOINT ["/run.sh"]

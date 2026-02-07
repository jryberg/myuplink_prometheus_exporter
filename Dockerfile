# Build run container
FROM python:3.14-trixie
LABEL maintainer="Johan Ryberg <johan@securit.se>"

# Debian settings
ENV DEBIAN_FRONTEND noninteractive

# Install needed tools
RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get -y install tini && \
    apt-get -y autoremove && \
    apt-get -y autoclean && \
    apt-get -y clean all && \
    rm -rf /var/lib/apt/lists/*

# Set up virtual environment and install dependencies
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Add files
COPY myuplink.py /usr/local/bin/
RUN chmod +x /usr/local/bin/myuplink.py

# Create non-root user and group
RUN groupadd --gid 10001 myuplink && \
    useradd --uid 10001 --gid myuplink --shell /usr/sbin/nologin --no-create-home myuplink

# Security hardening
RUN chmod -R o-w /opt/venv && \
    find / -perm /6000 -type f -exec chmod a-s {} + 2>/dev/null || true

USER myuplink:myuplink

ENTRYPOINT ["/usr/bin/tini", "-v", "--", "/opt/venv/bin/python3", "/usr/local/bin/myuplink.py"]

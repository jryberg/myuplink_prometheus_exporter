# Build run container
FROM debian:bullseye-slim
LABEL maintainer="Johan Ryberg <johan@securit.se>"

# Debian settings
ENV DEBIAN_FRONTEND noninteractive

# Install needed tools tools
RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get -y install python3 python3-pip tini apt-utils 
RUN pip3 install --upgrade pip && \
    pip3 install case-converter prometheus_client requests

# Add files
ADD myuplink.py /usr/local/bin/
RUN ln -s /usr/bin/tini /usr/local/bin/tini && \
    chmod +x /usr/local/bin/myuplink.py && \
    apt-get -y autoremove && \
    apt-get -y autoclean && \
    apt-get -y clean all && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/usr/local/bin/tini", "-v", "--", "/usr/local/bin/myuplink.py"]

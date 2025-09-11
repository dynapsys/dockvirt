FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# Use alternative mirrors and configure apt for better reliability
RUN echo "deb http://deb.debian.org/debian bullseye main" > /etc/apt/sources.list.d/debian.list || true
RUN sed -i 's|http://archive.ubuntu.com/ubuntu|http://us.archive.ubuntu.com/ubuntu|g' /etc/apt/sources.list || true
RUN sed -i 's|http://security.ubuntu.com/ubuntu|http://security.ubuntu.com/ubuntu|g' /etc/apt/sources.list || true

# Configure apt with more aggressive retries and timeouts
RUN echo 'Acquire::Retries "10";' > /etc/apt/apt.conf.d/80-retries
RUN echo 'Acquire::http::Timeout "300";' >> /etc/apt/apt.conf.d/80-retries
RUN echo 'Acquire::https::Timeout "300";' >> /etc/apt/apt.conf.d/80-retries

# Install packages in stages with fallback mechanisms
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update || (sleep 30 && apt-get update) || (sleep 60 && apt-get update)

RUN apt-get install -y --no-install-recommends --fix-missing \
    ca-certificates curl wget || \
    (apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    ca-certificates curl wget)

RUN apt-get install -y --no-install-recommends --fix-missing \
    iproute2 iputils-ping sudo make git \
    python3 python3-pip python3-venv python3-dev python3-setuptools \
    gcc build-essential

RUN apt-get install -y --no-install-recommends --fix-missing \
    qemu-kvm libvirt-daemon-system libvirt-clients virtinst qemu-utils \
    cloud-image-utils bridge-utils \
    acl python3-libvirt || \
    (apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    qemu-kvm libvirt-daemon-system libvirt-clients virtinst qemu-utils \
    cloud-image-utils bridge-utils \
    acl python3-libvirt)

RUN rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash dev && echo 'dev ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dev && chmod 0440 /etc/sudoers.d/dev
WORKDIR /workspace
ENV LIBVIRT_DEFAULT_URI=qemu:///system
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]

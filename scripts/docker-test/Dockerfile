FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    qemu-kvm libvirt-daemon-system libvirt-clients virt-install qemu-utils \
    cloud-image-utils bridge-utils wget curl iproute2 iputils-ping \
    sudo make git python3 python3-pip python3-venv python3-dev gcc \
 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash dev && echo 'dev ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dev && chmod 0440 /etc/sudoers.d/dev
WORKDIR /workspace
ENV LIBVIRT_DEFAULT_URI=qemu:///system
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]

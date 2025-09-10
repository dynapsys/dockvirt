#!/usr/bin/env bash
set -e
# Start libvirtd (daemonize)
mkdir -p /var/run/libvirt
/usr/sbin/libvirtd -d || true
sleep 2
# Ensure default libvirt network
virsh --connect qemu:///system net-define /usr/share/libvirt/networks/default.xml 2>/dev/null || true
virsh --connect qemu:///system net-start default 2>/dev/null || true
virsh --connect qemu:///system net-autostart default 2>/dev/null || true
# Relax /dev/kvm if present
if [ -e /dev/kvm ]; then
  chgrp kvm /dev/kvm || true
  chmod g+rw /dev/kvm || true
fi
exec "$@"

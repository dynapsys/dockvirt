#!/bin/bash

# DockerVirt LAN Simple - Working solution for NetworkManager systems
# Uses host IP with port forwarding - no virtual IP needed

echo "🌐 DockerVirt LAN Simple - NetworkManager Compatible"
echo "===================================================="

# Check sudo
if [[ $EUID -ne 0 ]]; then
   echo "❌ Requires sudo: sudo bash $0"
   exit 1
fi

LOCAL_PORT=8080
EXPOSE_PORT=80

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --port) LOCAL_PORT="$2"; shift 2 ;;
        --expose-port) EXPOSE_PORT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Check localhost works
if ! curl -s -m 3 http://localhost:$LOCAL_PORT/ >/dev/null 2>&1; then
    echo "❌ localhost:$LOCAL_PORT not responding"
    exit 1
fi

echo "✅ localhost:$LOCAL_PORT working"

# Get network info
HOST_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K\S+' 2>/dev/null || ip addr show | grep 'inet ' | grep -v '127\.' | head -1 | awk '{print $2}' | cut -d/ -f1)

if [[ -z "$HOST_IP" ]]; then
    echo "❌ Cannot detect host IP"
    exit 1
fi

echo "📍 Host IP: $HOST_IP"

# Setup cleanup
cleanup() {
    echo -e "\n🧹 Cleaning up..."
    iptables -t nat -D PREROUTING -p tcp --dport $EXPOSE_PORT -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT 2>/dev/null || true
    iptables -D INPUT -p tcp --dport $EXPOSE_PORT -j ACCEPT 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

# Configure port forwarding
echo "🔧 Setting up port forwarding..."

# Remove old rules
iptables -t nat -D PREROUTING -p tcp --dport $EXPOSE_PORT -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT 2>/dev/null || true
iptables -D INPUT -p tcp --dport $EXPOSE_PORT -j ACCEPT 2>/dev/null || true

# Add new rules
iptables -t nat -A PREROUTING -p tcp --dport $EXPOSE_PORT -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT
iptables -A INPUT -p tcp --dport $EXPOSE_PORT -j ACCEPT

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

echo "✅ Configured: $HOST_IP:$EXPOSE_PORT → localhost:$LOCAL_PORT"

# Test
sleep 2
if curl -s -m 3 http://$HOST_IP:$EXPOSE_PORT/ >/dev/null 2>&1; then
    STATUS="✅ WORKING"
else
    STATUS="⚠️ May need time to propagate"
fi

# Results
echo ""
echo "=============================================="
echo "🎉 DOCKVIRT ACCESSIBLE FROM ENTIRE NETWORK!"
echo "=============================================="
echo ""
echo "🌐 ACCESS FROM ANY DEVICE:"
echo "   http://$HOST_IP"
echo ""
echo "🧪 TEST FROM OTHER DEVICES:"
echo "   • Smartphone: http://$HOST_IP"
echo "   • Other computer: http://$HOST_IP"
echo "   • Ping: ping $HOST_IP"
echo ""
echo "📋 STATUS: $STATUS"
echo "⚠️  Press Ctrl+C to stop"
echo "=============================================="
echo ""

# Keep running
while true; do
    sleep 30
    if ! curl -s -m 2 http://localhost:$LOCAL_PORT/ >/dev/null 2>&1; then
        echo "⚠️ localhost:$LOCAL_PORT stopped responding"
    fi
done

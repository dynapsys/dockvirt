#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message and exit
error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

echo "Testing Docker Compose example..."

# 1. Navigate to the example directory
cd "$(dirname "$0")" || error "Failed to change to script directory"

# 2. Start the VM with dockvirt
echo "Starting VM with dockvirt..."
dockvirt up || error "Failed to start VM with dockvirt"
success "VM started successfully"

# 3. Get VM IP
VM_IP=$(virsh domifaddr compose-demo | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' | head -1)
[ -z "$VM_IP" ] && error "Failed to get VM IP address"

# 4. Test SSH connection
echo "Testing SSH connection to VM..."
ssh-keyscan -p 2222 "$VM_IP" >> ~/.ssh/known_hosts 2>/dev/null
ssh -p 2222 -o "StrictHostKeyChecking=no" ubuntu@"$VM_IP" exit || error "SSH connection failed"
success "SSH connection successful"

# 5. Copy files to VM
echo "Copying files to VM..."
scp -P 2222 -r . ubuntu@"$VM_IP":/var/lib/dockvirt/compose-demo/ || error "Failed to copy files to VM"

# 6. Run Docker Compose inside the VM
echo "Starting Docker Compose services..."
ssh -p 2222 ubuntu@"$VM_IP" "cd /var/lib/dockvirt/compose-demo && docker-compose up -d" || error "Failed to start Docker Compose services"

# 7. Wait for services to start
echo "Waiting for services to become healthy..."
for i in {1..10}; do
    if curl -s -f "http://$VM_IP/" >/dev/null; then
        success "Services are up and running!"
        break
    fi
    if [ $i -eq 10 ]; then
        error "Timed out waiting for services to start"
    fi
    sleep 5
done

# 8. Test the application endpoints
echo "Testing application endpoints..."

# Test main page
if ! curl -s -f "http://$VM_IP/" >/dev/null; then
    error "Main page is not accessible"
fi

# Test API endpoint
if ! curl -s -f "http://$VM_IP/api/status" | grep -q '"status":"success"'; then
    error "API endpoint is not working"
fi

# Test static content
if ! curl -s -f "http://$VM_IP/static/" >/dev/null; then
    error "Static content is not accessible"
fi

success "All tests passed!"

# 9. Show access information
echo ""
echo "========================================"
echo "  Access the application at: http://$VM_IP"
echo "  Or use the domain: http://compose.dockvirt.dev"
echo ""
echo "  SSH into the VM with:"
echo "  ssh -p 2222 ubuntu@$VM_IP"
echo ""
echo "  To stop the services and clean up:"
echo "  1. Stop Docker Compose: docker-compose down"
echo "  2. Stop the VM: dockvirt down --name compose-demo"
echo "========================================"
echo ""

exit 0

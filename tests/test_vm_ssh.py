#!/usr/bin/env python3
"""
Test VM SSH connectivity and basic commands.
"""
import os
import pytest
import paramiko
import socket
import time
import logging
from pathlib import Path
from paramiko.ssh_exception import (
    SSHException, AuthenticationException, 
    NoValidConnectionsError, BadHostKeyException
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration from conftest
SSH_USER = "ubuntu"
SSH_PASSWORD = "ubuntu"
SSH_TIMEOUT = 30
MAX_RETRIES = 5
RETRY_DELAY = 10
CONNECTION_TIMEOUT = 300  # 5 minutes

def wait_for_ssh(hostname, port=22, timeout=CONNECTION_TIMEOUT):
    """Wait until SSH port is available and responsive."""
    start_time = time.time()
    last_error = None
    
    while time.time() - start_time < timeout:
        try:
            # First check if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((hostname, port))
            sock.close()
            
            if result == 0:
                # Port is open, try SSH handshake
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(
                        hostname=hostname,
                        port=port,
                        username=SSH_USER,
                        password=SSH_PASSWORD,
                        timeout=10,
                        banner_timeout=20,
                        auth_timeout=20
                    )
                    ssh.close()
                    logger.info(f"SSH connection successful to {hostname}:{port}")
                    return True
                except Exception as e:
                    last_error = str(e)
                    logger.debug(f"SSH not ready yet: {last_error}")
                    time.sleep(5)
            else:
                logger.debug(f"Port {port} not open yet, waiting...")
                time.sleep(5)
                
        except Exception as e:
            last_error = str(e)
            logger.debug(f"Connection attempt failed: {last_error}")
            time.sleep(5)
    
    logger.error(f"SSH connection timed out. Last error: {last_error}")
    return False

class TestVMConnectivity:
    """Test VM connectivity and basic commands."""
    
    def execute_ssh_command(self, hostname, command, retries=3, delay=5):
        """Execute a command over SSH with retries."""
        last_error = None
        
        for attempt in range(retries):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                logger.info(f"Attempting SSH connection to {hostname} (attempt {attempt + 1}/{retries})")
                
                # Try password authentication first
                try:
                    ssh.connect(
                        hostname=hostname,
                        username=SSH_USER,
                        password=SSH_PASSWORD,
                        timeout=SSH_TIMEOUT,
                        banner_timeout=30,
                        auth_timeout=30,
                        look_for_keys=False,
                        allow_agent=False
                    )
                except AuthenticationException:
                    # If password auth fails, try with SSH key
                    logger.info("Password auth failed, trying SSH key...")
                    ssh.connect(
                        hostname=hostname,
                        username=SSH_USER,
                        key_filename=str(Path.home() / ".ssh" / "id_rsa"),
                        timeout=SSH_TIMEOUT,
                        banner_timeout=30,
                        auth_timeout=30
                    )
                
                # Execute the command
                stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
                exit_status = stdout.channel.recv_exit_status()
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                if exit_status != 0:
                    raise Exception(f"Command failed with status {exit_status}: {error}")
                    
                return output
                
            except (SSHException, NoValidConnectionsError, socket.error, Exception) as e:
                last_error = str(e)
                logger.warning(f"SSH command attempt {attempt + 1} failed: {last_error}")
                if attempt < retries - 1:
                    time.sleep(delay)
            finally:
                try:
                    ssh.close()
                except:
                    pass
        
        raise Exception(f"All SSH command attempts failed. Last error: {last_error}")
    
    def test_ssh_connectivity(self, vm_ip):
        """Test SSH connectivity to VM."""
        logger.info(f"Testing SSH connectivity to {vm_ip}...")
        
        if not wait_for_ssh(vm_ip):
            pytest.fail(f"SSH connection to {vm_ip} failed after timeout")
        
        # Test basic command execution
        try:
            output = self.execute_ssh_command(vm_ip, "echo 'SSH test successful'")
            assert "SSH test successful" in output
            logger.info("SSH connectivity test passed")
        except Exception as e:
            pytest.fail(f"SSH command execution failed: {str(e)}")
    
    def test_system_info(self, vm_ip):
        """Test getting system information from VM."""
        logger.info(f"Testing system information on {vm_ip}...")
        
        try:
            # Test uname
            uname = self.execute_ssh_command(vm_ip, "uname -a")
            logger.info(f"System info: {uname}")
            
            # Test disk space
            df = self.execute_ssh_command(vm_ip, "df -h")
            logger.info(f"Disk usage:\n{df}")
            
            # Test memory
            free = self.execute_ssh_command(vm_ip, "free -m")
            logger.info(f"Memory usage:\n{free}")
            
            # Test cloud-init status
            cloud_init = self.execute_ssh_command(vm_ip, "cloud-init status")
            logger.info(f"Cloud-init status: {cloud_init}")
            
            # Test SSH service status
            ssh_status = self.execute_ssh_command(vm_ip, "systemctl status ssh")
            logger.info(f"SSH service status: {ssh_status}")
            
        except Exception as e:
            pytest.fail(f"Failed to get system information: {str(e)}")
    
    def test_network_connectivity(self, vm_ip):
        """Test network connectivity from VM."""
        logger.info(f"Testing network connectivity from {vm_ip}...")
        
        try:
            # Test internet connectivity
            ping = self.execute_ssh_command(vm_ip, "ping -c 3 8.8.8.8")
            logger.info(f"Ping test result: {ping}")
            
            # Test DNS resolution
            nslookup = self.execute_ssh_command(vm_ip, "nslookup google.com")
            logger.info(f"DNS test result: {nslookup}")
            
        except Exception as e:
            pytest.fail(f"Network connectivity test failed: {str(e)}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

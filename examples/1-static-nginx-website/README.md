# Example 1: Static Nginx Website

This example shows how to use `dockvirt` to run a simple static website served by an Nginx server.

## Steps to Run

1.  **Start the VM with `dockvirt`**:
    Navigate to this directory and run `dockvirt`. The Dockerfile and application files will be automatically copied to the VM and built there:

    ```bash
    cd examples/1-static-nginx-website
    
    # Build happens inside the VM automatically.
    # Optional (not required): pre-build on host
    # docker build -t my-static-website:latest .

    # Run dockvirt - parameters are in the .dockvirt file
    dockvirt up
    
    # Developer tip: if another dockvirt is first on your PATH (e.g., Homebrew),
    # use the project venv binary explicitly to ensure the latest local CLI:
    # ../../.venv-3.13/bin/dockvirt up
    ```

    Or you can use CLI parameters:
    ```bash
    # Use the default Ubuntu 22.04
    dockvirt up \
      --name static-site \
      --domain static-site.local \
      --image my-static-website:latest \
      --port 80

    # Or use Fedora
    dockvirt up \
      --name static-site-fedora \
      --domain static-site-fedora.local \
      --image my-static-website:latest \
      --port 80 \
      --os fedora38
    ```

2.  **Add an entry to `/etc/hosts`**:
    After getting the IP address from `dockvirt`, add it to your `/etc/hosts` file:
    ```
    <ip_address> static-site.local
    ```

    If a reverse proxy (Caddy) is used inside the VM, IP-based checks may require a Host header:

    ```bash
    curl -H 'Host: static-site.local' http://<ip_address>/
    ```

    To quickly get the VM IP using the local CLI:

    ```bash
    ../../.venv-3.13/bin/dockvirt ip --name static-site
    ```

3.  **Open the site in your browser**:
    Visit `http://static-site.local` to see your site.

4.  **Destroy the VM when finished**:
    ```bash
    dockvirt down --name static-site
    ```

> Note: Do not run `dockvirt` or `make` with `sudo`. The tools request sudo only when needed and act on your real HOME.

### Networking: NAT vs Bridge (LAN)

By default, libvirt NAT (`network=default`) is used. To expose the VM directly in your LAN, create a Linux bridge (e.g., `br0`) and either add `net=bridge=br0` to `.dockvirt` or run `dockvirt up --net bridge=br0`.

Bridge creation example (Fedora/NetworkManager):

```bash
sudo nmcli con add type bridge ifname br0 con-name br0
sudo nmcli con add type bridge-slave ifname enp3s0 master br0
sudo nmcli con modify br0 ipv4.method auto ipv6.method auto
sudo nmcli con up br0
```

Run the VM on the bridge:

```bash
../../.venv-3.13/bin/dockvirt up --net bridge=br0
```

## What's happening in the background?

When you run `dockvirt up`, the tool:
1. Automatically downloads the Ubuntu 22.04 image (on first run)
2. Copies the Dockerfile and application files to the VM
3. Creates a virtual machine with Docker and Caddy
4. Builds the Docker image inside the VM
5. Starts your container with a reverse proxy
6. Configures access via the domain

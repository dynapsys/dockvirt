# Example 1: Static Nginx Website

This example shows how to use `dockvirt` to run a simple static website served by an Nginx server.

## Steps to Run

1.  **Start the VM with `dockvirt`**:
    Navigate to this directory and run `dockvirt`. The Dockerfile and application files will be automatically copied to the VM and built there:

    ```bash
    cd examples/1-static-nginx-website
    
    # First, build the Docker image
    docker build -t my-static-website:latest .
    
    # Then run dockvirt - parameters are in the .dockvirt file
    dockvirt up
    ```

    Or you can use CLI parameters:
    ```bash
    # Build the image first
    docker build -t my-static-website:latest .
    
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

3.  **Open the site in your browser**:
    Visit `http://static-site.local` to see your site.

4.  **Destroy the VM when finished**:
    ```bash
    dockvirt down --name static-site
    ```

## What's happening in the background?

When you run `dockvirt up`, the tool:
1. Automatically downloads the Ubuntu 22.04 image (on first run)
2. Copies the Dockerfile and application files to the VM
3. Creates a virtual machine with Docker and Caddy
4. Builds the Docker image inside the VM
5. Starts your container with a reverse proxy
6. Configures access via the domain

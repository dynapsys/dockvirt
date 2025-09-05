# Example 2: Python (Flask) Web Application

This example shows how to run a simple Python Flask application using `dockvirt`.

## Steps to Run

1.  **Start the VM with `dockvirt`**:
    The Dockerfile and application files will be automatically copied to the VM and built there:
    Use the `.dockvirt` file for maximum convenience:

    ```bash
    # Use the default configuration from the .dockvirt file
    dockvirt up
    
    # Or change the OS to Fedora (edit .dockvirt or use the parameter)
    dockvirt up --os fedora38
    ```

    You can also ignore the `.dockvirt` file and use full parameters:
    ```bash
    # Full command with parameters
    dockvirt up \
      --name flask-app \
      --domain flask-app.local \
      --image my-flask-app:latest \
      --port 5000 \
      --os ubuntu22.04
    ```

2.  **Add an entry to `/etc/hosts`**:
    After getting the IP address from `dockvirt`, add it to your `/etc/hosts` file:
    ```
    <ip_address> flask-app.local
    ```

3.  **Open the application in your browser**:
    Visit `http://flask-app.local` to see your application.

4.  **Destroy the VM when finished**:
    ```bash
    dockvirt down --name flask-app
    ```

## Automatic Image Downloading

On the first run, `dockvirt` will automatically download the required operating system image:
- Ubuntu 22.04: `~/.dockvirt/images/jammy-server-cloudimg-amd64.img`
- Fedora 38: `~/.dockvirt/images/Fedora-Cloud-Base-38-1.6.x86_64.qcow2`

Images are cached locally, so subsequent runs will be much faster.

## What's happening in the background?

When you run `dockvirt up`, the tool:
1. Automatically downloads the Ubuntu 22.04 or Fedora 38 image (on first run)
2. Copies the Dockerfile, app.py, requirements.txt, and other application files to the VM
3. Creates a virtual machine with Docker and Caddy
4. Builds a Docker image with the Flask application inside the VM
5. Starts the application container with a reverse proxy
6. Configures access via the domain

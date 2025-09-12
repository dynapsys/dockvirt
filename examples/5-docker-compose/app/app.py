from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dockvirt with Docker Compose</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                text-align: center;
            }
            .container {
                margin-top: 50px;
            }
            .status {
                color: #4CAF50;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Dockvirt with Docker Compose</h1>
            <p>This is a sample application running in a Docker container inside a KVM virtual machine.</p>
            <div class="status">Status: <span id="status">Running</span></div>
            <p>Try the <a href="/api/status">API endpoint</a> for more information.</p>
        </div>
    </body>
    </html>
    """

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'success',
        'service': 'Dockvirt Demo',
        'version': '1.0.0',
        'container_id': os.uname().nodename,
        'message': 'This API is running inside a Docker container managed by Docker Compose in a KVM virtual machine.'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

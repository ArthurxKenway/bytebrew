import socket
import threading
import paramiko
import yaml
import logging
import os
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.example.yml')
try:
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    logger.error(f"Config file {CONFIG_FILE} not found.")
    exit(1)

CONTROLLER_URL = os.getenv('CONTROLLER_URL', config['logging'].get('controller_url'))

# Generate or load host key
HOST_KEY_FILE = config['services']['ssh'].get('host_key', 'host.key')
if not os.path.exists(HOST_KEY_FILE):
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(HOST_KEY_FILE)
host_key = paramiko.RSAKey(filename=HOST_KEY_FILE)

class Server(paramiko.ServerInterface):
    def __init__(self, client_address):
        self.event = threading.Event()
        self.client_address = client_address

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        logger.info(f"Login attempt: {username}:{password} from {self.client_address}")
        self.log_attempt(username, password)
        return paramiko.AUTH_FAILED

    def log_attempt(self, username, password):
        if config['logging']['remote_logging'] and CONTROLLER_URL:
            try:
                payload = {
                    "type": "ssh_login",
                    "source_ip": self.client_address[0],
                    "username": username,
                    "password": password,
                    "timestamp": time.time()
                }
                threading.Thread(target=self.send_log, args=(payload,)).start()
            except Exception as e:
                logger.error(f"Failed to send log: {e}")

    def send_log(self, payload):
        try:
            requests.post(CONTROLLER_URL, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send log to controller: {e}")

    def get_allowed_auths(self, username):
        return 'password'

def handle_connection(client, addr):
    transport = paramiko.Transport(client)
    transport.add_server_key(host_key)
    server = Server(addr)
    try:
        transport.start_server(server=server)
        channel = transport.accept(20)
        if channel is None:
            return
        transport.close()
    except Exception as e:
        logger.error(f"Connection error: {e}")
    finally:
        transport.close()

def start_ssh_server():
    port = config['services']['ssh']['port']
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', port))
    sock.listen(100)
    logger.info(f"SSH Honeypot listening on port {port}")

    while True:
        client, addr = sock.accept()
        logger.info(f"Connection from {addr}")
        threading.Thread(target=handle_connection, args=(client, addr)).start()

if __name__ == "__main__":
    if config['services']['ssh']['enabled']:
        start_ssh_server()

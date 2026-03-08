import paramiko
import os
from dotenv import load_dotenv
load_dotenv()

IP = "15.207.112.85"
KEY_PATH = os.path.join("c:", os.sep, "Users", "Asus", "Documents", "Downloads", "Kisaan.pem")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(IP, username="ubuntu", key_filename=KEY_PATH, timeout=30)

cmds = [
    "tail -30 /home/ubuntu/backend.log",
    "ps aux | grep -E 'uvicorn|next|nginx' | grep -v grep",
    "curl -s -m 5 http://127.0.0.1:8000/health || echo 'BACKEND_DOWN'",
    "curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:3000 || echo 'FRONTEND_DOWN'",
]

for cmd in cmds:
    print(f"\n>>> {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    stdout.channel.recv_exit_status()
    print(stdout.read().decode()[:2000])
    err = stderr.read().decode()
    if err:
        print(f"ERR: {err[:500]}")

ssh.close()

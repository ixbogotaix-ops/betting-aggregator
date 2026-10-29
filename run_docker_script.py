import socket
import paramiko
import sys

HOST = "45.84.222.76"
USER = "root"
PASS = "Dthenpipito87!"

def run_in_docker(script_path):
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((HOST, 22))

    t = paramiko.Transport(sock)
    t.banner_timeout = 60
    t.start_client()
    t.auth_password(USER, PASS)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh._transport = t

    stdin, stdout, stderr = ssh.exec_command("docker exec -i betting_aggregator-backend-1 python -")
    stdin.write(code)
    stdin.channel.shutdown_write()

    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    ssh.close()
    return out, err

if __name__ == "__main__":
    out, err = run_in_docker(sys.argv[1])
    print("=== STDOUT ===")
    print(out)
    if err:
        print("=== STDERR ===")
        print(err)

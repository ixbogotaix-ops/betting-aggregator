import os
import sys
import time
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

HOST = "45.84.222.76"
USER = "root"
PASS = "Dthenpipito87!"
REMOTE_DIR = "/opt/betting_aggregator"
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

def upload_dir(sftp, local_dir, remote_dir):
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass

    ignored_dirs = {'venv', 'node_modules', '__pycache__', '.git', '.idea', '.vscode'}
    ignored_files = {
        'betting_db.sqlite', 'betting.db', 'check_server.py', 'debug_inspect.py',
        'br.html', 'ch.html', 'lb.html', 'op.html', 'stv.html', 'vp.html', 'vp2.html', 'vp3.html', 'vprognoze_debug.html',
        'remote_exec.py', 'get_backend_log.py', 'configure_ipv4.py', 'test_and_screenshot.py', 'restart_containers.py', 'verify_live.py'
    }

    for item in os.listdir(local_dir):
        if item in ignored_dirs or item in ignored_files or item.startswith('test_'):
            continue

        l_path = os.path.join(local_dir, item)
        r_path = f"{remote_dir}/{item}".replace('\\', '/')

        if os.path.isdir(l_path):
            upload_dir(sftp, l_path, r_path)
        else:
            print(f"Uploading: {item}", flush=True)
            sftp.put(l_path, r_path)

def main():
    import socket
    print(f"[*] Подключение к серверу {HOST} по IPv4...", flush=True)
    connected = False
    ssh = None
    for attempt in range(1, 5):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(20)
            sock.connect((HOST, 22))

            t = paramiko.Transport(sock)
            t.banner_timeout = 60
            t.start_client()
            t.auth_password(USER, PASS)

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh._transport = t
            connected = True
            print("[+] SSH успешно подключен через IPv4 сокет!", flush=True)
            break
        except Exception as e:
            print(f"[!] Попытка {attempt} не удалась: {e}. Повтор через 5 сек...", flush=True)
            time.sleep(5)
    if not connected:
        raise Exception("Не удалось подключиться к серверу по SSH после 4 попыток.")

    print("[*] Загрузка обновлений через SFTP...", flush=True)
    sftp = ssh.open_sftp()
    upload_dir(sftp, LOCAL_DIR, REMOTE_DIR)
    sftp.close()

    print("[*] Мгновенный перезапуск бэкенда и перезагрузка Nginx...", flush=True)
    stdin, stdout, stderr = ssh.exec_command(f"cd {REMOTE_DIR} && docker compose restart backend && docker exec betting_aggregator-frontend-1 nginx -s reload", get_pty=True)
    for line in stdout:
        try:
            print(line, end="", flush=True)
        except Exception:
            pass

    ssh.close()
    print("\n[+] Обновление успешно завершено! Сайт доступен по адресу: http://45.84.222.76", flush=True)

if __name__ == "__main__":
    main()

import os
import paramiko

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

    ignored_dirs = {'venv', 'node_modules', 'dist', '__pycache__', '.git', '.idea', '.vscode'}
    ignored_files = {'betting_db.sqlite', 'br.html', 'ch.html', 'lb.html', 'op.html', 'stv.html', 'vp.html', 'vp2.html', 'vp3.html', 'vprognoze_debug.html'}

    for item in os.listdir(local_dir):
        if item in ignored_dirs or item in ignored_files or item.startswith('test_'):
            continue

        l_path = os.path.join(local_dir, item)
        r_path = f"{remote_dir}/{item}".replace('\\', '/')

        if os.path.isdir(l_path):
            upload_dir(sftp, l_path, r_path)
        else:
            sftp.put(l_path, r_path)

def main():
    print(f"[*] Подключение к серверу {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=22, username=USER, password=PASS, timeout=30)

    print("[*] Загрузка обновлений через SFTP...")
    sftp = ssh.open_sftp()
    upload_dir(sftp, LOCAL_DIR, REMOTE_DIR)
    sftp.close()

    print("[*] Перезапуск контейнеров на сервере...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {REMOTE_DIR} && docker compose up -d --build", get_pty=True)
    for line in stdout:
        print(line, end="")

    ssh.close()
    print("\n[+] Обновление успешно завершено! Сайт доступен по адресу: http://45.84.222.76")

if __name__ == "__main__":
    main()

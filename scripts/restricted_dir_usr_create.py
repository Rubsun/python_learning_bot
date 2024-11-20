import os
import subprocess

def create_user_and_directory(username, base_directory):
    restricted_dir = os.path.join(base_directory, 'restricted_dir')
    command = ['sudo', 'useradd', '--no-create-home', '--shell', '/bin/bash', username]
    subprocess.run(command, check=True)

    subprocess.run(['sudo', 'setfacl', '-m', f'u:{username}:--x', base_directory], check=True)

    os.makedirs(restricted_dir, exist_ok=True)

    subprocess.run(['sudo', 'chown', username, restricted_dir], check=True)
    subprocess.run(['sudo', 'chmod', '700', restricted_dir], check=True)

    restrict_user_access(username, base_directory)

def restrict_user_access(user, base_directory):
    subprocess.run(['sudo', 'setfacl', '-m', f'u:{user}:--x', base_directory], check=True)

username = 'limiteduser'
base_directory = '/env'
create_user_and_directory(username, base_directory)
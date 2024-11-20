import subprocess

def delete_user(username):
    try:
        subprocess.run(['sudo', 'deluser', username], check=True)
        print(f'Пользователь {username} успешно удален')
    except subprocess.CalledProcessError as e:
        print(f'Ошибка при удалении пользователя {username}: {e}')

delete_user('limiteduser')
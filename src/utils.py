import logging
import json
import ast
import subprocess
import os
import asyncio
import uuid
import re
from datetime import datetime

from mypy.semanal_main import core_modules

from consumer.logger import logger, LOGGING_CONFIG
from db.model.task import Task
from src.metrics_init import measure_time

logging.config.dictConfig(LOGGING_CONFIG)


@measure_time
def clean_error_message(err: str) -> str:
    cleaned_message = re.sub(r'Traceback $most recent call last$:.*?\n', '', err, flags=re.DOTALL)

    lines = cleaned_message.splitlines()
    detailed_lines = []

    for line in lines:
        if 'File "' in line or 'line ' in line:
            continue

        if detailed_lines and re.match(r'^\s*\^+', line):
            detailed_lines[-1] += '\n' + line
        else:
            detailed_lines.append(line)

    cleaned_message = '\n'.join(filter(None, detailed_lines)).strip()

    logger.info('Cleaned error message: %s', cleaned_message)
    return cleaned_message


@measure_time
def extract_function_name(user_code: str) -> str | None:
    try:
        tree = ast.parse(user_code)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return node.name
        return None
    except SyntaxError:
        logger.info("No user's function name")
        return None


@measure_time
async def run_user_function(
    user_code: str,
    func_name: str,
    test_args: tuple,
    restricted_dir='/env/restricted_dir',
    username='limiteduser',
    timeout=3,
) -> str:
    test_code = f"""
{user_code}

result = {func_name}{test_args}
print(result)
"""
    script_name = f'script_{uuid.uuid4()}.py'
    script_path = os.path.join(restricted_dir, script_name)

    if os.path.exists(script_path):
        os.remove(script_path)

    with open(script_path, 'w') as f:
        f.write(test_code)

    subprocess.run(['sudo', 'chown', username, script_path], check=True)
    subprocess.run(['sudo', 'chmod', '500', script_path], check=True)

    proc = await asyncio.create_subprocess_exec(
        'sudo', '-u', username, 'env', 'python3', script_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        logger.info("user's code is running more than 3 seconds")
        return 'Execution timed out', f'Process was killed after {timeout} seconds.'
    except Exception as e:
        logger.error(e)

    if os.path.exists(script_path):
        os.remove(script_path)

    return stdout.decode().strip(), stderr.decode().strip()


@measure_time
async def check_user_task_solution(user_code: str, task: Task) -> str:
    func_name = extract_function_name(user_code)
    if not func_name:
        return "Ошибка: Функция не найдена в коде."

    input_data = json.loads(task.get('input_data'))
    correct_answers = json.loads(task.get('correct_answer'))

    if input_data is None or correct_answers is None:
        logger.error(
            f'[{datetime.now()}] Not exist input data or correct answers!!! '
            f'TASK ID: {task.get("id")}\n USER ANSWER: {user_code}'
        )
        return 'Технические шоколадки. Попробуйте позже!'

    test_count = 0
    for test_args, expected_output in zip(input_data, correct_answers):
        test_count += 1
        result, err = await run_user_function(user_code, func_name, tuple(test_args))
        if err:
            cleaned_message = clean_error_message(err)
            return f'<b>Ваш код выдал ошибку</b>:\n{cleaned_message}'
        elif str(result) != str(expected_output):
            return f"Решение неверное!❌\nТест №{test_count}: Аргументы: {', '.join(str(arg) for arg in test_args)}\nПравильный ответ: {expected_output}.\nВаш ответ: {result}"

    secret_input = json.loads(task.get('secret_input'))
    secret_answers = json.loads(task.get('secret_answer'))

    if secret_answers is None or secret_input is None:
        logger.error(
            f'[{datetime.now()}] Not exist secret answers or secret input!!! '
            f'TASK ID: {task.get("id")}\n USER ANSWER: {user_code}'
        )
        return 'Технические шоколадки. Попробуйте позже!'

    for test_args, expected_output_secret in zip(secret_input, secret_answers):
        test_count += 1
        result_secret, err = await run_user_function(user_code, func_name, tuple(test_args))
        if err:
            cleaned_message = clean_error_message(err)
            return f'<b>Ваш код выдал ошибку</b>:\n{cleaned_message}'
        elif str(result_secret) != str(expected_output_secret):
            return f"Решение неверное ❌\nТест №{test_count}: Попробуйте еще раз!"

    return f"Решение верное! Поздравляю! Вы прошли 100% тестов! 🎉"

import json
import ast
import subprocess
import os
import asyncio
import uuid
import re

from db.model.task import Task
from src.metrics_init import measure_time


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
        return None


@measure_time
async def run_user_function(user_code: str, func_name: str, test_args: tuple, restricted_dir='/env/restricted_dir',
                            username='limiteduser', timeout=5) -> str:
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

    # Correcting the chown command
    subprocess.run(['sudo', 'chown', username, script_path], check=True)
    subprocess.run(['sudo', 'chmod', '500', script_path], check=True)

    proc = await asyncio.create_subprocess_exec(
        'sudo', '-u', username, 'env', 'python3', script_path,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        stdout, stderr = await proc.communicate()  # Get any output before terminating
        return 'Execution timed out', f'Process was killed after {timeout} seconds.'

    if os.path.exists(script_path):
        os.remove(script_path)

    return stdout.decode().strip(), stderr.decode().strip()


@measure_time
async def check_user_task_solution(user_code: str, task: Task) -> str:
    func_name = extract_function_name(user_code)
    if not func_name:
        return "Ошибка: Функция не найдена в коде."

    input_data = json.loads(task.input_data)
    correct_answers = json.loads(task.correct_answer)

    for test_args, expected_output in zip(input_data, correct_answers):
        result, err = await run_user_function(user_code, func_name, tuple(test_args))
        if err:
            cleaned_message = clean_error_message(err)
            return f'<b>Ваш код выдал ошибку</b>:\n{cleaned_message}'
        if str(result) != str(expected_output):
            return "Решение неверное ❌"

    secret_input = json.loads(task.secret_input)
    secret_answers = json.loads(task.secret_answer)

    for test_args, expected_output_secret in zip(secret_input, secret_answers):
        result_secret, err = await run_user_function(user_code, func_name, tuple(test_args))
        if err:
            cleaned_message = clean_error_message(err)
            return f'<b>Ваш код выдал ошибку</b>:\n{cleaned_message}'
        if str(result_secret) != str(expected_output_secret):
            return "Решение неверное ❌"

    return f"Решение верное! Правильные ответы: {expected_output}, ваши ответы: {result}"


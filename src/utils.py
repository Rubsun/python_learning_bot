import ast
import json
import subprocess

from db.model.task import Task


def extract_function_name(user_code: str) -> str | None:

    try:
        tree = ast.parse(user_code)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return node.name
        return
    except SyntaxError:
        return


def run_user_function(user_code: str, func_name: str, test_args: tuple) -> str:
    test_code = f"""
{user_code}

result = {func_name}{test_args}
print(result)
"""
    try:
        result = subprocess.run(["python3", "-c", test_code], capture_output=True, text=True, timeout=2)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {str(e)}"


def check_user_task_solution(user_code: str, task: Task) -> str:
    func_name = extract_function_name(user_code)
    print(func_name)
    if not func_name:
        return "Ошибка: Функция не найдена в коде."

    input_data = json.loads(task.input_data)
    correct_answers = json.loads(task.correct_answer)
    for test_args, expected_output in zip(input_data, correct_answers):
        output = run_user_function(user_code, func_name, tuple(test_args))
        return output

        # if output != str(expected_output):
        #     return "Решение неверное ❌"

    secret_input = json.loads(task.secret_input)
    secret_answers = json.loads(task.secret_answer)
    print(secret_input, secret_answers, sep='\n')
    for test_args, expected_output in zip(secret_input, secret_answers):
        output = run_user_function(user_code, func_name, tuple(test_args))
        print(f'Ожидаемы ответ: {expected_output}, Ответ: {output}')
        return output
        # if output != str(expected_output):
        #     return "Решение неверное."

    return "Решение верное!"

async def task_to_dict(task):
    return {
        'id': str(task.id),
        'title': task.title,
        'complexity': task.complexity,
        'description': task.description,
        'correct_answer': task.correct_answer,
        'secret_input': task.secret_input,
        'input_data': task.input_data,
        'secret_answer': task.secret_answer,
    }

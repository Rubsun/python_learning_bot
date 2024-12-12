from consumer.metrics_init import measure_time


@measure_time
async def task_to_dict(task):
    return {
        "id": str(task.id),
        "title": task.title,
        "complexity": task.complexity,
        "description": task.description,
        "correct_answer": task.correct_answer,
        "input_data": task.input_data,
        "secret_input": task.secret_input,
        "secret_answer": task.secret_answer,
    }

from .base import BaseMessage


class TaskMessage(BaseMessage):
    user_id: int
    action: str


class CreateTaskMessage(BaseMessage):
    id: str
    title: str
    complexity: str
    description: str
    input_data: list
    correct_answer: list
    secret_input: list
    secret_answer: list
    action: str


class GetTaskByIdMessage(BaseMessage):
    task_id: str
    user_id: int
    action: str

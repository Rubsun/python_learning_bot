from .base import BaseMessage


class TaskMessage(BaseMessage):
    user_id: int
    action: str


class CreateTaskMessage(BaseMessage):
    title: str
    description: str
    complexity: str
    input_data: str
    correct_answer: str
    secret_answer: str
    action: str


class GetTaskByIdMessage(BaseMessage):
    task_id: str
    user_id: int
    action: str

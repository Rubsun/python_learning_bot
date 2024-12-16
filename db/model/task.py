from typing import List
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from db.model.meta import Base


class Task(Base):
    __tablename__ = 'task'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column()
    complexity: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    input_data: Mapped[List] = mapped_column(JSON)
    correct_answer: Mapped[List] = mapped_column(JSON)
    secret_input: Mapped[List] = mapped_column(JSON)
    secret_answer: Mapped[List] = mapped_column(JSON)

from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from db.model.meta import Base


class Task(Base):
    __tablename__ = 'task'
    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    complexity: Mapped[str]
    description: Mapped[str]
    input_data: Mapped[str]
    correct_answer: Mapped[str]
    secret_input: Mapped[str]
    secret_answer: Mapped[str]

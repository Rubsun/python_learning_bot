# from uuid import uuid4, UUID
#
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy import ForeignKey
#
# from db.model.meta import Base
#
# class UserTask(Base):
#     __tablename__ = 'user_task'
#     id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
#     user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
#     task_id: Mapped[int] = mapped_column(ForeignKey('task.id'))
#     solved: Mapped[bool] = mapped_column(default=False)
#
#     user = relationship("User", back_populates="tasks")
#     task = relationship("Task", back_populates="users")

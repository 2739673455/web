from typing import Optional
import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKeyConstraint, Index, String, Text, text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = 'conversation'
    __table_args__ = (
        Index('idx_conversation_user_id', 'user_id'),
        {'comment': '对话'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='对话ID')
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='用户ID')
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment='对话标题')
    create_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')

    message: Mapped[list['Message']] = relationship('Message', back_populates='conversation')


class ModelConfig(Base):
    __tablename__ = 'model_config'
    __table_args__ = (
        Index('idx_model_config_user_id', 'user_id'),
        {'comment': '用户模型配置'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='模型配置ID')
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='用户ID')
    base_url: Mapped[str] = mapped_column(String(500), nullable=False, comment='URL')
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, comment='模型名称')
    encrypted_api_key: Mapped[Optional[str]] = mapped_column(Text, comment='加密后的 API 密钥')
    create_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')


class Message(Base):
    __tablename__ = 'message'
    __table_args__ = (
        ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ondelete='CASCADE', name='message_ibfk_1'),
        Index('idx_message_conversation_id', 'conversation_id'),
        {'comment': '消息'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='消息ID')
    conversation_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='对话ID')
    sender: Mapped[str] = mapped_column(String(20), nullable=False, comment='发送者')
    content: Mapped[str] = mapped_column(LONGTEXT, nullable=False, comment='消息内容')
    timestamp: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), comment='发送时间')

    conversation: Mapped['Conversation'] = relationship('Conversation', back_populates='message')

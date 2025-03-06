from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base

class ChannelList(Base):
    __tablename__ = 'channel_lists'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String, nullable=False)
    channel_id = Column(String, unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)

    channel_data = relationship("ChannelData", back_populates="channel_list")

class ChannelData(Base):
    __tablename__ = 'channel_datas'

    id = Column(Integer, ForeignKey('channel_lists.id'), primary_key=True)
    date = Column(DateTime, nullable=False)
    local_balance = Column(Integer, nullable=False)
    local_fee = Column(Integer, nullable=False)
    local_infee = Column(Integer, nullable=False)
    remote_balance = Column(Integer, nullable=False)
    remote_fee = Column(Integer, nullable=False)
    remote_infee = Column(Integer, nullable=False)

    channel_list = relationship("ChannelList", back_populates="channel_data")
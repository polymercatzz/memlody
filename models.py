from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    gender = Column(String)
    date = Column(Date)
    email = Column(String, unique=True)

class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_name = Column(String, unique=True, nullable=False)

    pairing_questions = relationship("PairingQuestion", back_populates="category")
    speaking_questions = relationship("SpeakingQuestion", back_populates="category")
    see_questions = relationship("SeeQuestion", back_populates="category")
    todo_questions = relationship("TodoQuestion", back_populates="category")
    order_questions = relationship("OrderQuestion", back_populates="category")

class PairingQuestion(Base):
    __tablename__ = "pairing_questions"

    pairing_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stage = Column(Integer)
    all_path_img = Column(String)  # เก็บ list ของ path รูปภาพ
    path_sound = Column(String)
    answer = Column(String)
    category_id = Column(Integer, ForeignKey("categories.category_id"))

    category = relationship("Category", back_populates="pairing_questions")

class SpeakingQuestion(Base):
    __tablename__ = "speaking_questions"

    speaking_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stage = Column(Integer)
    path_sound = Column(String)
    answer = Column(String)
    category_id = Column(Integer, ForeignKey("categories.category_id"))

    category = relationship("Category", back_populates="speaking_questions")

class SeeQuestion(Base):
    __tablename__ = "see_questions"

    see_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stage = Column(Integer)
    path_img = Column(String)
    answer = Column(String)
    category_id = Column(Integer, ForeignKey("categories.category_id"))

    category = relationship("Category", back_populates="see_questions")

class TodoQuestion(Base):
    __tablename__ = "todo_questions"

    todo_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stage = Column(Integer)
    path_img = Column(String)
    choice_4 = Column(String)  # เก็บ list ของตัวเลือก
    answer = Column(String)
    category_id = Column(Integer, ForeignKey("categories.category_id"))

    category = relationship("Category", back_populates="todo_questions")

class OrderQuestion(Base):
    __tablename__ = "order_questions"

    order_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stage = Column(Integer)
    map_choice_4 = Column(String)  # เก็บ list หรือ dict สำหรับลำดับ
    category_id = Column(Integer, ForeignKey("categories.category_id"))

    category = relationship("Category", back_populates="order_questions")

# 🎯 เพิ่ม GameStageHistory สำหรับเก็บการเล่นจบหนึ่งด่าน
class GameStageHistory(Base):
    __tablename__ = "game_stage_history"

    stage_history_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    game_type = Column(String)  # เช่น 'pairing', 'speaking'
    stage = Column(Integer)  # ด่านที่เล่น
    total_questions = Column(Integer)
    correct_count = Column(Integer)
    incorrect_count = Column(Integer)
    play_time = Column(DateTime)
    duration = Column(Float)  # วินาที

    user = relationship("User")

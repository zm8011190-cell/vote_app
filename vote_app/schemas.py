#user schema
from typing import List

from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    password: str



class choose(BaseModel):
    choice: str
    question_id: str | None = None
    question_type: str | None = None
class Userquestion(BaseModel):
    header: str
    question_text: str
    option1: str
    option2: str


class Question(BaseModel):
    id: int
    question_text: str
    option1: str
    option2: str

    class Config:
        orm_mode = True


class QuestionWithImage(BaseModel):
    header: str
    question_text: str
    option1: str
    option2: str
    imageurls: List[str]
    statistics: dict | None = None

    class Config:
        orm_mode = True




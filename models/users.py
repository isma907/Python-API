from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    lastname: str
    birthday: str
    dni: str
    username: str
    password: str

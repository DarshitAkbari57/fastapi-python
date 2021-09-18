from typing import List
import databases
import sqlalchemy
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
import os
import urllib

#DATABASE_URL = "sqlite:///./test.db"

host_server = os.environ.get('host_server', 'localhost')
db_server_port = urllib.parse.quote_plus(str(os.environ.get('db_server_port', '5432')))
database_name = os.environ.get('database_name', 'postgres')
db_username = urllib.parse.quote_plus(str(os.environ.get('db_username', 'postgres')))
db_password = urllib.parse.quote_plus(str(os.environ.get('db_password', 'postgres')))
# ssl_mode = urllib.parse.quote_plus(str(os.environ.get('ssl_mode','prefer')))
# DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}?sslmode={}'.format(db_username, db_password, host_server, db_server_port, database_name, ssl_mode)
DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}'.format(db_username, db_password, host_server, db_server_port, database_name)

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "User",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("firstname", sqlalchemy.String),
    sqlalchemy.Column("lastname", sqlalchemy.String),
    sqlalchemy.Column("phonenumber", sqlalchemy.String),
)

engine = sqlalchemy.create_engine(
    #DATABASE_URL, connect_args={"check_same_thread": False}
    DATABASE_URL, pool_size=3, max_overflow=0
)
metadata.create_all(engine)



class User(BaseModel):
    id: int=None
    username: str
    password: str
    firstname: str
    lastname: str
    phonenumber: str=None

app = FastAPI(title="REST API using FastAPI PostgreSQL Async EndPoints")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(GZipMiddleware)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
async def getData():
    print("test")
    return "hello-"

@app.post("/users/", response_model=User, status_code = status.HTTP_201_CREATED)
async def create_user(user:User):
    print("username 1  : ",user)
    # print("username 1  : ",type(user.password))
    # print("username 1  : ",type(user.firstname))
    # print("username 1  : ",type(user.lastname))
    # print("username 1  : ",type(user.phonenumber))
    query = users.insert().values(username=user.username,password=user.password,firstname=user.firstname,lastname=user.lastname,phonenumber=user.phonenumber)
    last_record_id = await database.execute(query)
    return {**user.dict(), "id": last_record_id}

@app.put("/users/{userId}/", response_model=User, status_code = status.HTTP_200_OK)
async def update_user(userId: int, payload: User):
    query = users.update().where(users.c.id == userId).values(username=payload.username,password=payload.password,firstname=payload.firstname,lastname=payload.lastname,phonenumber=payload.phonenumber)
    await database.execute(query)
    return {**payload.dict(), "id": userId}

@app.get("/users/", response_model=List[User], status_code = status.HTTP_200_OK)
async def read_users(skip: int = 0, take: int = 20):
    query = users.select().offset(skip).limit(take)
    return await database.fetch_all(query)

@app.get("/users/{userId}/", response_model=User, status_code = status.HTTP_200_OK)
async def read_users(userId: int):
    query = users.select().where(users.c.id == userId)
    return await database.fetch_one(query)

@app.delete("/users/{userId}/", status_code = status.HTTP_200_OK)
async def delete_user(userId: int):
    query = users.delete().where(users.c.id == userId)
    await database.execute(query)
    return {"message": "Note with id: {} deleted successfully!".format(userId)}

import os
import ast
from urllib.parse import urlparse

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import (
    RedirectResponse,
    Response,
)
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

import firebase_admin
import firebase_admin.auth
import firebase_admin._auth_utils

import database


class PostData(BaseModel):
    owner: str
    title: str
    main_data: dict
    template: list


class UserData(BaseModel):
    user_id: str


class CreateUser(BaseModel):
    uid: str
    email: str
    password: str


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


cred_json = ast.literal_eval(os.getenv('FIREBASE_CRED'))
cred = firebase_admin.credentials.Certificate(cred_json)
firebase_admin.initialize_app(cred)


@app.middleware("http")
async def middleware(request: Request, call_next):
    if request.method == "HEAD":
        response = Response()
    elif "herokuapp" in urlparse(str(request.url)).netloc:
        domain = os.getenv("DOMAIN")
        if domain:
            url = urlparse(str(request.url))._replace(netloc=domain).geturl()
            response = RedirectResponse(url)
        else:
            response = await call_next(request)
    else:
        response = await call_next(request)
    return response


@app.get("/")
async def get_root(request: Request):
    return {"message": "hello, world"}


@app.get("/table/{id}")
async def get_table(id):
    table = database.get_table(id)
    if not table:
        raise HTTPException(status_code=404, detail='Not Found')
    return table


@app.get("/user/{user_id}")
async def get_user(user_id):
    user = database.get_user(user_id)
    try:
        firebase_admin.auth.get_user(user_id)
    except firebase_admin._auth_utils.UserNotFoundError:
        if user:
            database.delete_user(user_id)
        raise HTTPException(status_code=404, detail='Not Found')
    return user


@app.post("/table/{id}")
async def update_table(id, obj: PostData):
    try:
        owner = firebase_admin.auth.verify_id_token(obj.owner)['uid']
    except Exception as e:
        print(e)
        raise HTTPException(status_code=403, detail='Forbidden')
    table = database.update_table(id, owner, obj.title, obj.main_data, obj.template)
    if table:
        return table
    else:
        raise HTTPException(status_code=403, detail='Forbidden')


@app.post("/deltable/{id}")
async def delete_table(id, user: UserData):
    try:
        user_id = firebase_admin.auth.verify_id_token(user.user_id)['uid']
    except Exception as e:
        print(e)
        raise HTTPException(status_code=403, detail='Forbidden')
    table = database.delete_table(id, user_id)
    if table:
        return table
    else:
        raise HTTPException(status_code=403, detail='Forbidden')


@app.post("/deluser")
async def delete_user(user: UserData):
    try:
        user_id = firebase_admin.auth.verify_id_token(user.user_id)['uid']
    except Exception as e:
        print(e)
        raise HTTPException(status_code=403, detail='forbidden')
    table = database.delete_user(user_id)
    if table:
        return table
    else:
        raise HTTPException(status_code=403, detail='forbidden')


@app.post("/create_user")
async def create_user(model: CreateUser):
    try:
        firebase_admin.auth.create_user(
            uid=model.uid,
            email=model.email,
            password=model.password
        )
        res = ''
    except firebase_admin._auth_utils.UidAlreadyExistsError:
        res = 'UidAlreadyExists'
    except firebase_admin._auth_utils.EmailAlreadyExistsError:
        res = 'EmailAlreadyExists'
    except Exception as e:
        if str(e) == 'Error while calling Auth service (INVALID_EMAIL).':
            res = 'InvalidEmail'
        elif str(e) == 'Invalid password string. Password must be a string at least 6 characters long.':
            res = 'WeakPassword'
        else:
            res = str(e)
    return {'res': res}

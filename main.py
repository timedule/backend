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
    template: dict


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

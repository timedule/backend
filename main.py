import os
from urllib.parse import urlparse

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import (
    RedirectResponse,
    Response,
)
from fastapi.middleware.cors import CORSMiddleware

import database

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

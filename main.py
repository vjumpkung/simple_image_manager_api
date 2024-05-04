import os
import random
import re
import uuid
import json
from typing import List

import uvicorn
from fastapi import FastAPI, File, Header, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import config.load_config as CONFIG
from database.connection import Images, engine
from sqlmodel import Session, select, insert

app = FastAPI(title=CONFIG.API_NAME, summary=CONFIG.API_DESCRIPTION)

templates = Jinja2Templates(directory="templates")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/public", StaticFiles(directory="public"), name="public")


class ImagesResponseDto(BaseModel):
    image_id: str
    img_url: str
    type: str


@app.get("/")
def main_page(request: Request, accesstoken: str = None):
    if accesstoken == CONFIG.SECRET:
        return templates.TemplateResponse(
            "upload_images.html",
            {
                "accesstoken": CONFIG.SECRET,
                "request": request,
                "image_types": CONFIG.CHOICES,
            },
        )
    else:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)


@app.get("/manage_images/")
def manageImages(request: Request, accesstoken: str = None):

    with Session(engine) as session:
        images = session.exec(select(Images)).all()

    images_res = []

    for image in images:
        images_res.append(
            {
                "image_id": image.image_id,
                "img_url": "/public/" + image.file_name,
                "type": image.type,
            }
        )

    if accesstoken == CONFIG.SECRET:
        return templates.TemplateResponse(
            "manage_images.html",
            {"accesstoken": CONFIG.SECRET, "request": request, "images": images_res},
        )
    else:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)


@app.post("/upload_images/{type}/", status_code=201)
def upload_images(
    files: List[UploadFile],
    type: str,
    request: Request,
    accesstoken: str = Header(None),
) -> List[ImagesResponseDto]:

    if accesstoken != CONFIG.SECRET:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)

    res = []

    # save files to public folder
    for file in files:

        # get file extension

        fileName, fileExension = os.path.splitext(file.filename)

        hash = random.sample(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890", 5
        )

        fileNameWithHash = (
            fileName.replace(" ", "_") + "-" + "".join(hash[0:5]) + fileExension
        )

        with open(f"public/{fileNameWithHash}", "wb") as f:
            f.write(file.file.read())

        UUID = str(uuid.uuid4())

        with Session(engine) as session:
            session.add(Images(image_id=UUID, type=type, file_name=fileNameWithHash))
            session.commit()

        # get request url
        base_url = request.base_url.__str__()

        res.append(
            {
                "image_id": UUID,
                "img_url": request.url_for("public", path=fileNameWithHash)._url,
                "type": type,
            }
        )

    # return image urls
    return res


@app.get("/get_all_images/")
def getAllImage(request: Request) -> List[ImagesResponseDto]:

    # get all images from database
    with Session(engine) as session:
        images = session.exec(select(Images)).all()

    img_url = []

    # get request url
    base_url = request.base_url.__str__()

    # extract the base url
    for image in images:
        img_url.append(
            {
                "image_id": image.image_id,
                "img_url": request.url_for("public", path=image.file_name)._url,
                "type": image.type,
            }
        )

    return img_url


@app.get("/get_images/{type}/")
def getImageByType(type: str, request: Request) -> List[ImagesResponseDto]:
    # get all images from database
    with Session(engine) as session:
        images = session.exec(select(Images).where(Images.type == type)).all()

    img_url = []

    # get request url
    base_url = request.base_url.__str__()

    # extract the base url
    for image in images:
        img_url.append(
            {
                "image_id": image.image_id,
                "img_url": request.url_for("public", path=image.file_name)._url,
                "type": image.type,
            }
        )

    return img_url


@app.delete("/delete_image/{image_id}/", status_code=204)
def deleteImage(image_id: str, accesstoken: str = Header(None)) -> None:
    if accesstoken != CONFIG.SECRET:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)

    with Session(engine) as session:
        image = session.exec(select(Images).where(Images.image_id == image_id)).first()

    os.remove(f"public/{image.file_name}")

    with Session(engine) as session:
        session.delete(image)
        session.commit()

    return None


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        port=int(CONFIG.PORT),
        reload=CONFIG.RELOAD,
        host=CONFIG.HOST,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )

import uvicorn
from fastapi.middleware.cors import CORSMiddleware

import uuid
import os
import random
import re

from fastapi import FastAPI, File, UploadFile, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List

from database.connection import sqliteConnection, cursor

from pydantic import BaseModel

import config.load_config as CONFIG

app = FastAPI(title=CONFIG.API_NAME, summary=CONFIG.API_DESCRIPTION)


templates = Jinja2Templates(directory="templates")

origins = [
    "*",
]

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

        # save file details to database
        cursor.execute(
            f"""
            INSERT INTO images (image_id, type, file_name)
            VALUES ('{UUID}', '{type}', '{fileNameWithHash}');
            """
        )

        sqliteConnection.commit()

        referer = request.headers.get("referer")
        # extract the base url
        base_url = re.match(r"(http[s]?://[^/]+)", referer).group(0)

        res.append(
            {
                "image_id": UUID,
                "img_url": base_url + "/public/" + fileNameWithHash,
                "type": type,
            }
        )

    # return image urls
    return res


@app.get("/")
def main(request: Request, accesstoken: str = None):

    if accesstoken == CONFIG.SECRET:
        return templates.TemplateResponse(
            "upload_images.html", {"accesstoken": CONFIG.SECRET, "request": request}
        )
    else:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)


@app.get("/manage_images/")
def manageImages(request: Request, accesstoken: str = None):
    if accesstoken == CONFIG.SECRET:
        return templates.TemplateResponse(
            "manage_images.html", {"accesstoken": CONFIG.SECRET, "request": request}
        )
    else:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)


@app.get("/get_all_images/")
def getAllImage(request: Request) -> List[ImagesResponseDto]:

    # get all images from database
    cursor.execute("SELECT * FROM images;")

    images = cursor.fetchall()

    sqliteConnection.commit()

    img_url = []

    referer = request.headers.get("referer")
    # extract the base url
    base_url = re.match(r"(http[s]?://[^/]+)", referer).group(0)

    for image in images:
        img_url.append(
            {
                "image_id": image[0],
                "img_url": base_url + "/public/" + image[2],
                "type": image[1],
            }
        )

    return img_url


@app.get("/get_images/{type}")
def getImageByType(type: str, request: Request) -> List[ImagesResponseDto]:
    # get all images from database
    cursor.execute(f"SELECT * FROM images WHERE type = '{type}';")

    images = cursor.fetchall()

    sqliteConnection.commit()

    img_url = []

    referer = request.headers.get("referer")
    # extract the base url
    base_url = re.match(r"(http[s]?://[^/]+)", referer).group(0)

    for image in images:
        img_url.append(
            {
                "image_id": image[0],
                "img_url": base_url + "/public/" + image[2],
                "type": image[1],
            }
        )

    return img_url


@app.delete("/delete_image/{image_id}/", status_code=204)
def deleteImage(image_id: str, accesstoken: str = Header(None)) -> None:
    if accesstoken != CONFIG.SECRET:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)

    cursor.execute(f"SELECT * FROM images WHERE image_id = '{image_id}';")
    image = cursor.fetchone()
    os.remove(f"public/{image[2]}")
    cursor.execute(f"DELETE FROM images WHERE image_id = '{image_id}';")
    sqliteConnection.commit()
    return None


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        port=int(CONFIG.PORT),
        reload=CONFIG.RELOAD,
        host=CONFIG.HOST,
        forwarded_allow_ips="*",
        proxy_headers=True,
    )

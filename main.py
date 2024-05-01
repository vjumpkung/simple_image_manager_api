import uvicorn
from fastapi.middleware.cors import CORSMiddleware

import uuid

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List

from database.connection import sqliteConnection, cursor

import config.load_config as CONFIG

app = FastAPI(title=CONFIG.API_NAME, summary=CONFIG.API_DESCRIPTION)


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


@app.post("/upload_images/{type}/")
async def upload_images(files: List[UploadFile], type: str, request: Request):

    # save files to public folder
    for file in files:

        filename = file.filename.replace(" ", "_")

        with open(f"public/{filename}", "wb") as f:
            f.write(file.file.read())

    # save file details to database
    for file in files:
        cursor.execute(
            f"""
            INSERT INTO images (image_id, type, file_name)
            VALUES ('{str(uuid.uuid4())}', '{type}', '{filename}');
            """
        )

    cursor.execute("SELECT * FROM images;")

    images = cursor.fetchall()

    sqliteConnection.commit()

    img_url = []

    for image in images:
        img_url.append(
            {
                "image_id": image[0],
                "img_url": request.url_for("public", path=image[2])._url,
                "type": image[1],
            }
        )

    sqliteConnection.commit()

    # return image urls
    return img_url


@app.get("/")
async def main():
    with open("upload_images.html", "r") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/get_all_image")
def tea(request: Request):

    # get all images from database
    cursor.execute("SELECT * FROM images;")

    images = cursor.fetchall()

    sqliteConnection.commit()

    img_url = []

    for image in images:
        img_url.append(
            {
                "image_id": image[0],
                "img_url": request.url_for("public", path=image[2])._url,
                "type": image[1],
            }
        )

    return img_url


if __name__ == "__main__":
    uvicorn.run("main:app", port=int(CONFIG.PORT), reload=CONFIG.RELOAD)

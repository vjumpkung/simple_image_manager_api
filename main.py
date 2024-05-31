import os
import random
import uuid
from typing import List

import uvicorn
from fastapi import FastAPI, Request, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

import config.load_config as CONFIG
from database.connection import Images, engine, Users, ApiKeys
from sqlmodel import Session, select

from passlib.context import CryptContext
from jose import JWTError, jwt

app = FastAPI(title=CONFIG.API_NAME, summary=CONFIG.API_DESCRIPTION)

templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


class AuthRequestDto(BaseModel):
    username: str
    password: str


class AuthResponseDto(BaseModel):
    accesstoken: str


class APIKeysResponseDto(BaseModel):
    api_key: str


class StatusResponseDto(BaseModel):
    status: str


@app.get("/")
def login_page(request: Request):
    try:
        jwt_token = request.cookies.get("access_token")

        if jwt_token == None:
            raise JWTError

        payload = jwt.decode(jwt_token, CONFIG.SECRET, algorithms=["HS256"])
        return RedirectResponse(url="/upload_images/")
    except:
        return templates.TemplateResponse(
            "login_page.html", {"request": request, "app_name": CONFIG.API_NAME}
        )


@app.get("/register_page/")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register_page.html", {"request": request, "app_name": CONFIG.API_NAME}
    )


@app.get("/upload_images/")
def main_page(request: Request):

    try:
        jwt_token = request.cookies.get("access_token")
        payload = jwt.decode(jwt_token, CONFIG.SECRET, algorithms=["HS256"])
    except:
        return RedirectResponse(url="/")

    with Session(engine) as session:
        api_keys = session.exec(
            select(ApiKeys).where(ApiKeys.user_id == payload["user_id"])
        ).first()

    return templates.TemplateResponse(
        "upload_images.html",
        {
            "username": payload["username"],
            "request": request,
            "image_types": CONFIG.CHOICES,
            "app_name": CONFIG.API_NAME,
            "api_key": (
                api_keys.api_key_id if api_keys else "No API Key Please Generate One!"
            ),
        },
    )


@app.get("/manage_images/")
def manageImages(request: Request):

    try:
        jwt_token = request.cookies.get("access_token")
        payload = jwt.decode(jwt_token, CONFIG.SECRET, algorithms=["HS256"])
    except:
        return RedirectResponse(url="/")

    with Session(engine) as session:
        images = session.exec(
            select(Images).where(Images.user_id == payload["user_id"])
        ).all()

    images_res = []

    for image in images:
        images_res.append(
            {
                "image_id": image.image_id,
                "img_url": "/public/" + image.file_name,
                "type": image.type,
            }
        )

    return templates.TemplateResponse(
        "manage_images.html",
        {"request": request, "images": images_res, "app_name": CONFIG.API_NAME},
    )


@app.post("/login", status_code=200)
def login(authRequestDto: AuthRequestDto, response: Response) -> AuthResponseDto:
    
    if authRequestDto.username == "" or authRequestDto.password == "":
        return JSONResponse(content={"message": "username and password cannot be blank"}, status_code=401)
    
    with Session(engine) as session:
        user = session.exec(
            select(Users).where(Users.username == authRequestDto.username)
        ).first()

    if user and pwd_context.verify(authRequestDto.password, user.password):

        accessToken = jwt.encode(
            {"user_id": user.user_id, "username": user.username},
            CONFIG.SECRET,
            algorithm="HS256",
        )

        response.set_cookie(key="access_token", value=accessToken, expires=604800)

        return AuthResponseDto(accesstoken=accessToken)
    else:
        return JSONResponse(content={"message": "check username or password"}, status_code=401)


@app.get("/logout", status_code=200)
def logout(response: Response, request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    return response


@app.post("/register", status_code=201)
def register(authResponseDto: AuthRequestDto, request: Request) -> StatusResponseDto:

    if (authResponseDto.username == "" or authResponseDto.password == ""):
        return JSONResponse(content={"message": "username or password cannot be blank"}, status_code=400)

    with Session(engine) as session:
        user = session.exec(
            select(Users).where(Users.username == authResponseDto.username)
        ).first()

    if user:
        return JSONResponse(content={"message": "User already exists"}, status_code=400)

    hashed_password = pwd_context.hash(authResponseDto.password)
    UUID = str(uuid.uuid4())
    with Session(engine) as session:
        session.add(
            Users(
                user_id=UUID,
                username=authResponseDto.username,
                password=hashed_password,
            )
        )
        session.commit()
    return StatusResponseDto(status="User created")


@app.post("/upload_images/{type}/", status_code=201)
def upload_images(
    files: List[UploadFile], type: str, request: Request
) -> List[ImagesResponseDto]:

    try:
        jwt_token = request.cookies.get("access_token")
        payload = jwt.decode(jwt_token, CONFIG.SECRET, algorithms=["HS256"])
    except JWTError:
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

        UUID = str(uuid.uuid4())

        with Session(engine) as session:
            session.add(
                Images(
                    image_id=UUID,
                    type=type,
                    file_name=fileNameWithHash,
                    user_id=payload["user_id"],
                )
            )
            session.commit()

        with open(f"public/{fileNameWithHash}", "wb") as f:
            f.write(file.file.read())

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
def getAllImage(apiKey: str, request: Request) -> List[ImagesResponseDto]:

    with Session(engine) as session:
        access = session.exec(
            select(ApiKeys).where(ApiKeys.api_key_id == apiKey)
        ).first()

    # get all images from database
    with Session(engine) as session:
        images = session.exec(
            select(Images).where(Images.user_id == access.user_id)
        ).all()

    img_url = []

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


@app.get("/get_api_key/")
def getApiKeys(request: Request) -> ApiKeys:
    try:
        jwt_token = request.cookies.get("access_token")
        payload = jwt.decode(jwt_token, CONFIG.SECRET, algorithms=["HS256"])
    except JWTError:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)

    with Session(engine) as session:
        api_keys = session.exec(
            select(ApiKeys).where(ApiKeys.user_id == payload["user_id"])
        ).first()

    return api_keys


@app.post("/generate_api_key/", status_code=201)
def generateApiKey(request: Request) -> APIKeysResponseDto:
    try:
        jwt_token = request.cookies.get("access_token")
        payload = jwt.decode(jwt_token, CONFIG.SECRET, algorithms=["HS256"])
    except JWTError:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)

    with Session(engine) as session:
        apiKey = session.exec(
            select(ApiKeys).where(ApiKeys.user_id == payload["user_id"])
        ).first()

    if apiKey:
        session.delete(apiKey)
        session.commit()

    UUID = "".join(
        [random.choice("abcdefghijklmnopqrstuvwxyz1234567890") for i in range(30)]
    )

    with Session(engine) as session:
        session.add(ApiKeys(api_key_id=UUID, user_id=payload["user_id"]))
        session.commit()

    return APIKeysResponseDto(api_key=UUID)


@app.get("/get_images/{type}/")
def getImageByType(type: str, request: Request, apiKey: str) -> List[ImagesResponseDto]:

    with Session(engine) as session:
        access = session.exec(
            select(ApiKeys).where(ApiKeys.api_key_id == apiKey)
        ).first()

    # get all images from database
    with Session(engine) as session:
        images = session.exec(
            select(Images).where(
                Images.type == type and Images.user_id == access.user_id
            )
        ).all()

    img_url = []

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
def deleteImage(image_id: str, request: Request) -> None:
    try:
        jwt_token = request.cookies.get("access_token")
        payload = jwt.decode(jwt_token, CONFIG.SECRET, algorithms=["HS256"])
    except JWTError:
        return JSONResponse(content={"message": "Unauthorized"}, status_code=401)

    with Session(engine) as session:
        image = session.exec(
            select(Images).where(
                Images.image_id == image_id and Images.user_id == payload["user_id"]
            )
        ).first()

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

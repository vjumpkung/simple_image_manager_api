# create sqlite database
from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.fastapi import RegisterTortoise
from tortoise.contrib.pydantic import pydantic_model_creator
import config.load_config as CONFIG
from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncGenerator

# create database.db file if not exists

with open("database.db", "a") as f:
    pass


class Users(Model):
    user_id = fields.UUIDField(primary_key=True)
    username = fields.TextField()
    password = fields.TextField()


class Images(Model):
    image_id = fields.UUIDField(primary_key=True)
    type = fields.TextField()
    file_name = fields.TextField()
    user_id = fields.ForeignKeyField("models.Users", related_name="user_id_1")


class ApiKeys(Model):
    api_key_id = fields.TextField(primary_key=True)
    user_id = fields.ForeignKeyField("models.Users", related_name="user_id_2")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # app startup
    async with RegisterTortoise(
        app,
        db_url=CONFIG.DATABASE_URI,
        modules={"models": ["main"]},
        generate_schemas=True,
        add_exception_handlers=True,
    ):
        # db connected
        yield
        # app teardown
    # db connections closed

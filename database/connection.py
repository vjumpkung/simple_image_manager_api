# create sqlite database
import sqlite3

# create database.db file if not exists

with open("database.db", "a") as f:
    pass


def create_table(db):
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
          image_id TEXT PRIMARY KEY,
          type TEXT NOT NULL,
          file_name TEXT NOT NULL
        );
        """
    )
    db.commit()


def connect_db():
    db = sqlite3.connect("database.db", check_same_thread=False)
    create_table(db)
    return db


db = connect_db()
cursor = db.cursor()

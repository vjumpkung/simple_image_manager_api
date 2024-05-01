# create sqlite database

import sqlite3

# create database.db file if not exists

with open("database.db", "a") as f:
    pass

sqliteConnection = sqlite3.connect("database.db", check_same_thread=False)

# create table if not exists

cursor = sqliteConnection.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS images (
      image_id TEXT PRIMARY KEY,
      type TEXT NOT NULL,
      file_name TEXT NOT NULL
    );
    """
)

sqliteConnection.commit()

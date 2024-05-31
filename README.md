# Simple Image Manager

A simple image manager which using FastAPI, SQLite

# Limitation

- Not suitable for production use because sqlite is not supported async.

## Demo

https://simple-image-uploader.vjumpkung.dynv6.net/

## Features

### Login and Register Page

![](/images/login.png)
![](/images/register.png)

### Support multiple images and can select type for find by type later (for grouping images).
![](/images/upload_img.png)


### For manage images (delete only)

![](/images/manage_img.png)


see more features by going swagger docs (/docs)

## Setup

1. clone repository
2. create new python environment `python -m venv venv`
3. `pip install -r requirement.txt`
4. setup .env by copying .env.example and rename it.
5. setup choice by copying choices.json.example and rename to choices.json

```json
[
  {
    "choice": "Choice A", <-- for display
    "value": "Value_A" <-- for storing in database
  },
  {
    "choice": "Choice B",
    "value": "Value_B"
  },
  {
    "choice": "Choice C",
    "value": "Value_C"
  }
]
```

6. run `python main.py`
7. access website with `http://localhost:PORT/`

## To-Do List

- [ ] Password Reset 
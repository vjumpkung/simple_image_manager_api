# Simple Image Manager

A simple image manager which using FastAPI, SQLite

## Features

![](/images/upload_img.png)

Support multiple images and can select type for find by type later (for grouping images).

![](/images/manage_img.png)

For manage images (delete only)

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
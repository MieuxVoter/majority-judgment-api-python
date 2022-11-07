import typing as t
from fastapi import FastAPI

app = FastAPI()


@app.get("/liveness")
def read_root():
    return "OK"


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

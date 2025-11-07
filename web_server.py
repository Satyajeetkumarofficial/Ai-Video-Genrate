# web_server.py
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "info": "AI Text2Video Bot running (worker process separate)"}

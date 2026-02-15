from fastapi import FastAPI

app = FastAPI(title="KisaanAI")

@app.get("/")
def read_root():
    return {"Hello": "World"}

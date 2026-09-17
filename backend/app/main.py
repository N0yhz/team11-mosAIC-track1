from fastapi import FastAPI
from app.api.routes.scoring import router as scoring_router

app = FastAPI()

app.include_router(scoring_router)
@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/health")
def health():
    return {"status": "ok"}
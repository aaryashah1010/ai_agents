from fastapi import FastAPI
from app.routes.email_routes import router as email_router

app = FastAPI(title="AI ERP Assistant")

app.include_router(email_router)


@app.get("/")
def home():
    return {"message": "AI ERP Assistant Running"}
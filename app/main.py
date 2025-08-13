from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import models
from app.routers import users, charges, payments

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router)
app.include_router(charges.router)
app.include_router(payments.router)
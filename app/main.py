from fastapi import FastAPI
from app.core.database import engine
from app.models import models
from app.routers import users, charges, payments

# Criação das tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

# Instância da aplicação FastAPI
app = FastAPI(
    title="Gateway",
    version="1.0",
    description="API de gateway de pagamentos com usuários, cobranças e transações"
)

# Inclusão das rotas
app.include_router(users.router)
app.include_router(charges.router)
app.include_router(payments.router)

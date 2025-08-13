from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import timedelta
from app.auth import auth
from app.core import database
from app.schemas import schemas
from app.crud import crud
router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# Endpoint de cadastro de usuário
@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user_cpf = crud.get_user_by_cpf(db, cpf=user.cpf)
    if db_user_cpf:
        raise HTTPException(status_code=400, detail="CPF já registrado")
    
    db_user_email = crud.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="E-mail já registrado")
    
    return crud.create_user(db=db, user=user)

# Endpoint de login, que retorna um token de autenticação 
@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(database.get_db)
):
    # O login deve permitir autenticação por CPF e senha ou e-mail e senha.
    user = crud.get_user_by_email(db, email=form_data.username) or crud.get_user_by_cpf(db, cpf=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais incorretas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
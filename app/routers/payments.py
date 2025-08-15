from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated

from app.auth import auth
from app.crud import crud
from app.core import database
from app.schemas import schemas
from app.models import models
from app.api import external

router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)

@router.post("/by-balance", response_model=schemas.Transaction)
def payment_by_balance(
    payment_data: schemas.TransactionPaymentByBalance,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Session = Depends(database.get_db)
):
    """
    Realiza um pagamento de cobrança usando o saldo do usuário.
    """
    charge = crud.get_charge_by_id(db, charge_id=payment_data.charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")

    if current_user.id == charge.recipient_id:
        raise HTTPException(status_code=400, detail="Não é possível pagar uma cobrança para si mesmo.")
        
    return crud.make_payment_by_balance(db=db, charge_id=payment_data.charge_id, user_id=current_user.id)

@router.post("/by-card", response_model=schemas.Transaction)
async def payment_by_card(
    payment_data: schemas.TransactionPaymentByCard,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Session = Depends(database.get_db)
):
    """
    Realiza um pagamento de cobrança usando cartão de crédito, consultando o autorizador externo.
    """
    is_authorized = await external.authorize_payment()
    if not is_authorized:
        raise HTTPException(status_code=400, detail="Pagamento não autorizado pelo serviço externo")

    return crud.make_payment_by_card(db=db, charge_id=payment_data.charge_id, user_id=current_user.id)

@router.post("/deposit", response_model=schemas.Transaction)
async def deposit(
    deposit_data: schemas.TransactionDeposit,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: Session = Depends(database.get_db)
):
    """
    Permite que um usuário faça um depósito em sua conta via cartão de crédito.
    """
    is_authorized = await external.authorize_payment()
    if not is_authorized:
        raise HTTPException(status_code=400, detail="Depósito não autorizado pelo serviço externo")
    
    return crud.make_deposit_by_card(db=db, user_id=current_user.id, amount=deposit_data.amount)
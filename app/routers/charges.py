from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from app.auth import auth
from app.crud import crud
from app.core import database
from app.schemas import schemas
from app.models import models

router = APIRouter(
    prefix="/charges",
    tags=["charges"]
)

@router.post("/", response_model=schemas.Charge)
def create_charge(
    charge: schemas.ChargeCreate,
    db: Session = Depends(database.get_db),
    current_user: Annotated[models.User, Depends(auth.get_current_user)] = None
):
    """
    Cria uma nova cobrança para um destinatário.
    Acesso restrito a usuários autenticados.
    """
    if charge.value <= 0:
        raise HTTPException(status_code=400, detail="O valor da cobrança deve ser positivo.")

    recipient = db.query(models.User).filter(models.User.cpf == charge.recipient_cpf).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatário não encontrado."
        )

    if recipient.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível criar cobrança para si mesmo."
        )

    return crud.create_charge(
        db=db,
        charge=charge,
        originator_id=current_user.id
    )

@router.post("/{charge_id}/cancel")
def cancel_charge(
    charge_id: int,
    db: Session = Depends(database.get_db),
    current_user: Annotated[models.User, Depends(auth.get_current_user)] = None
):
    """
    Cancela uma cobrança pendente ou estorna pagamento realizado via saldo.
    """
    charge = crud.get_charge_by_id(db, charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada.")

    # Apenas o originador pode cancelar a cobrança
    if charge.originator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Não autorizado a cancelar esta cobrança.")

    result = crud.cancel_charge(db, charge_id)
    return result

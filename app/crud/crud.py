from sqlalchemy.orm import Session
from app.schemas import schemas
from app.models import models
from passlib.context import CryptContext
from fastapi.exceptions import HTTPException
from decimal import Decimal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

# Usuários
def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_cpf(db: Session, cpf: str):
    return db.query(models.User).filter(models.User.cpf == cpf).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        cpf=user.cpf,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Cobranças
def create_charge(db: Session, charge: schemas.ChargeCreate, originator_id: int):
    recipient = get_user_by_cpf(db, cpf=charge.recipient_cpf)
    if not recipient:
        raise HTTPException(status_code=404, detail="Destinatário não encontrado")

    db_charge = models.Charge(
        value=charge.value,
        description=charge.description,
        originator_id=originator_id,
        recipient_id=recipient.id
    )
    db.add(db_charge)
    db.commit()
    db.refresh(db_charge)
    return db_charge

def get_charge_by_id(db: Session, charge_id: int):
    return db.query(models.Charge).filter(models.Charge.id == charge_id).first()

# Transações
def make_payment_by_balance(db: Session, charge_id: int, user_id: int):
    charge = get_charge_by_id(db, charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    if charge.status != "Pendente":
        raise HTTPException(status_code=400, detail="A cobrança não está pendente para pagamento")

    payer = get_user_by_id(db, user_id)
    if not payer:
        raise HTTPException(status_code=404, detail="Usuário pagador não encontrado")

    if payer.balance < charge.value:
        raise HTTPException(status_code=400, detail="Saldo insuficiente para realizar o pagamento")

    recipient = get_user_by_id(db, charge.recipient_id)
    payer.balance -= charge.value
    recipient.balance += charge.value
    charge.status = "Paga"

    transaction = models.Transaction(
        type='pagamento_saldo',
        amount=charge.value,
        status='aprovada',
        user_id=user_id,
        charge_id=charge_id
    )
    db.add(transaction)
    db.commit()
    db.refresh(payer)
    db.refresh(recipient)
    db.refresh(charge)
    db.refresh(transaction)
    return transaction

def make_payment_by_card(db: Session, charge_id: int, user_id: int):
    charge = get_charge_by_id(db, charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    charge.status = "Paga"
    transaction = models.Transaction(
        type='pagamento_cartao',
        amount=charge.value,
        status='aprovada',
        user_id=user_id,
        charge_id=charge_id
    )
    db.add(transaction)
    db.commit()
    db.refresh(charge)
    db.refresh(transaction)
    return transaction

def make_deposit_by_card(db: Session, user_id: int, amount: Decimal):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user.balance += amount
    transaction = models.Transaction(
        type='deposito',
        amount=amount,
        status='aprovada',
        user_id=user_id
    )
    db.add(transaction)
    db.commit()
    db.refresh(user)
    db.refresh(transaction)
    return transaction
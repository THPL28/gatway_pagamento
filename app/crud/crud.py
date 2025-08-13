from sqlalchemy.orm import Session
from app.schemas import schemas
from app.models import models
from passlib.context import CryptContext
from fastapi.exceptions import HTTPException

# Configuração para hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ====================
# Funções auxiliares
# ====================
def get_password_hash(password: str):
    return pwd_context.hash(password)

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# ====================
# Funções de Usuário
# ====================
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

# ====================
# Funções de Cobrança
# ====================
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

def get_charges_sent_by_user(db: Session, user_id: int, status: str = None):
    query = db.query(models.Charge).filter(models.Charge.originator_id == user_id)
    if status:
        query = query.filter(models.Charge.status == status)
    return query.all()

def get_charges_received_by_user(db: Session, user_id: int, status: str = None):
    query = db.query(models.Charge).filter(models.Charge.recipient_id == user_id)
    if status:
        query = query.filter(models.Charge.status == status)
    return query.all()

# ====================
# Funções de Transação
# ====================
def make_payment_by_balance(db: Session, charge_id: int, user_id: int):
    charge = db.query(models.Charge).filter(models.Charge.id == charge_id).first()
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    
    if charge.status != "Pendente":
        raise HTTPException(status_code=400, detail="A cobrança não está pendente para pagamento")

    payer = db.query(models.User).filter(models.User.id == user_id).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Usuário pagador não encontrado")

    if payer.balance < charge.value:
        raise HTTPException(status_code=400, detail="Saldo insuficiente para realizar o pagamento")
    
    recipient = db.query(models.User).filter(models.User.id == charge.recipient_id).first()
    
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

def make_deposit_by_card(db: Session, user_id: int, amount: float):
    user = db.query(models.User).filter(models.User.id == user_id).first()
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

def make_payment_by_card(db: Session, charge_id: int, user_id: int):
    charge = db.query(models.Charge).filter(models.Charge.id == charge_id).first()
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

# ====================
# Funções de Cancelamento
# ====================
def get_charge_by_id(db: Session, charge_id: int):
    return db.query(models.Charge).filter(models.Charge.id == charge_id).first()

def cancel_charge(db: Session, charge_id: int):
    charge = get_charge_by_id(db, charge_id=charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")
    
    if charge.status == "Pendente":
        charge.status = "Cancelada"
        db.commit()
        db.refresh(charge)
        return {"message": "Cobrança pendente cancelada com sucesso."}

    if charge.status == "Paga":
        transaction = db.query(models.Transaction).filter(
            models.Transaction.charge_id == charge_id, 
            models.Transaction.status == "aprovada"
        ).first()

        if transaction and transaction.type == "pagamento_saldo":
            payer = get_user_by_id(db, user_id=transaction.user_id)
            recipient = get_user_by_id(db, user_id=charge.recipient_id)
            
            if payer and recipient:
                payer.balance += charge.value
                recipient.balance -= charge.value
                charge.status = "Cancelada"
                
                db.commit()
                db.refresh(payer)
                db.refresh(recipient)
                db.refresh(charge)
                return {"message": "Cobrança paga com saldo estornada e cancelada com sucesso."}
            
            raise HTTPException(status_code=400, detail="Usuário pagador ou destinatário não encontrado para estorno.")
    
    raise HTTPException(status_code=400, detail="Não foi possível cancelar a cobrança.")
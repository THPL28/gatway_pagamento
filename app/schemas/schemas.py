from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
import re

# Funções auxiliares para CPF
def _only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def _validate_cpf(digits: str) -> bool:
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    def dv(seq):
        s = sum(int(x) * y for x, y in zip(seq, range(len(seq)+1, 1, -1)))
        r = (s * 10) % 11
        return 0 if r == 10 else r
    return dv(digits[:9]) == int(digits[9]) and dv(digits[:10]) == int(digits[10])

# Usuário
class UserCreate(BaseModel):
    name: str
    cpf: str
    email: EmailStr
    password: str

    @field_validator("cpf")
    @classmethod
    def normalize_and_check_cpf(cls, v):
        d = _only_digits(v)
        if not _validate_cpf(d):
            raise ValueError("CPF inválido")
        return d

class User(BaseModel):
    id: int
    name: str
    cpf: str
    email: EmailStr
    balance: Decimal

    class Config:
        from_attributes = True

# Cobrança
class ChargeBase(BaseModel):
    value: Decimal
    description: Optional[str] = None
    recipient_cpf: str

    @field_validator("recipient_cpf")
    @classmethod
    def normalize_and_check_cpf(cls, v):
        d = _only_digits(v)
        if not _validate_cpf(d):
            raise ValueError("CPF do destinatário inválido")
        return d

class ChargeCreate(ChargeBase):
    pass

class Charge(ChargeBase):
    id: int
    status: str
    originator_id: int
    recipient_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Transação
class TransactionBase(BaseModel):
    type: str
    amount: Decimal
    status: str
    user_id: int
    charge_id: Optional[int] = None

class TransactionPaymentByBalance(BaseModel):
    charge_id: int

class TransactionPaymentByCard(BaseModel):
    charge_id: int
    card_number: str
    expiration_date: str
    cvv: str

class TransactionDeposit(BaseModel):
    amount: Decimal

class Transaction(TransactionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Autenticação
class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    cpf: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

    @field_validator("cpf")
    @classmethod
    def normalize_and_check_cpf(cls, v):
        if v is None:
            return v
        d = _only_digits(v)
        if not _validate_cpf(d):
            raise ValueError("CPF inválido")
        return d

    @model_validator(mode="after")
    def ensure_one_identifier(self):
        if not (self.cpf or self.email):
            raise ValueError("Informe CPF ou e-mail para login")
        return self
    
class TokenData(BaseModel):
    username: Optional[str] = None

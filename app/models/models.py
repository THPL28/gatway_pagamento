from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    cpf = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=0.0)

    charges_originating = relationship("Charge", foreign_keys="[Charge.originator_id]", back_populates="originator")
    charges_destined = relationship("Charge", foreign_keys="[Charge.recipient_id]", back_populates="recipient")
    transactions = relationship("Transaction", back_populates="user")

class Charge(Base):
    __tablename__ = "charges"

    id = Column(Integer, primary_key=True, index=True)
    value = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="Pendente") # Pendente, Paga, Cancelada [cite: 32]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    originator_id = Column(Integer, ForeignKey("users.id"))
    recipient_id = Column(Integer, ForeignKey("users.id"))

    originator = relationship("User", foreign_keys=[originator_id], back_populates="charges_originating")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="charges_destined")
    transaction = relationship("Transaction", back_populates="charge", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False) # Ex: 'pagamento_saldo', 'pagamento_cartao', 'deposito'
    amount = Column(Float, nullable=False)
    status = Column(String, default="Pendente") # Ex: 'aprovada', 'rejeitada'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))
    charge_id = Column(Integer, ForeignKey("charges.id"), nullable=True)

    user = relationship("User", back_populates="transactions")
    charge = relationship("Charge", back_populates="transaction")
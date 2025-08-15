from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
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
    balance = Column(Numeric(12, 2), default=0.0)

    charges_originating = relationship("Charge", foreign_keys="[Charge.originator_id]", back_populates="originator")
    charges_destined = relationship("Charge", foreign_keys="[Charge.recipient_id]", back_populates="recipient")
    transactions = relationship("Transaction", back_populates="user")

class Charge(Base):
    __tablename__ = "charges"

    id = Column(Integer, primary_key=True, index=True)
    value = Column(Numeric(12, 2), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="Pendente")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    originator_id = Column(Integer, ForeignKey("users.id"))
    recipient_id = Column(Integer, ForeignKey("users.id"))

    originator = relationship("User", foreign_keys=[originator_id], back_populates="charges_originating")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="charges_destined")
    transaction = relationship("Transaction", back_populates="charge", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="Pendente")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    charge_id = Column(Integer, ForeignKey("charges.id"), nullable=True)

    user = relationship("User", back_populates="transactions")
    charge = relationship("Charge", back_populates="transaction")

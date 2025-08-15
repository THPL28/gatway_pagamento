import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models import User, Charge, Transaction

# Banco de dados de teste SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Substituindo dependência do DB
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def create_users(setup_database):
    # Usuários para teste
    user1 = {"name": "User One", "cpf": "12345678909", "email": "user1@example.com", "password": "pass123"}
    user2 = {"name": "User Two", "cpf": "98765432100", "email": "user2@example.com", "password": "pass123"}

    client.post("/users/", json=user1)
    client.post("/users/", json=user2)

    # Login para obter tokens
    resp1 = client.post("/users/token", data={"username": user1["email"], "password": "pass123"})
    resp2 = client.post("/users/token", data={"username": user2["email"], "password": "pass123"})

    token1 = resp1.json()["access_token"]
    token2 = resp2.json()["access_token"]

    return token1, token2

def test_create_charge(create_users):
    token1, token2 = create_users
    response = client.post(
        "/charges/",
        json={"value": 100, "description": "Cobrança teste", "recipient_cpf": "98765432100"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 100
    assert data["originator_id"] is not None
    assert data["recipient_id"] is not None

def test_payment_by_balance(create_users):
    token2 = create_users[1]
    # Primeiro, creditar saldo suficiente
    client.post("/payments/deposit", json={"amount": 500}, headers={"Authorization": f"Bearer {token2}"})
    
    # Pegar cobrança criada anteriormente
    charges = client.get("/charges/", headers={"Authorization": f"Bearer {token2}"}).json()
    charge_id = charges[0]["id"]

    response = client.post(
        "/payments/by-balance",
        json={"charge_id": charge_id},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "pagamento_saldo"
    assert data["status"] == "aprovada"

def test_payment_by_card(create_users):
    token2 = create_users[1]
    # Criar nova cobrança
    client.post(
        "/charges/",
        json={"value": 200, "description": "Cartão teste", "recipient_cpf": "12345678909"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    charges = client.get("/charges/", headers={"Authorization": f"Bearer {token2}"}).json()
    charge_id = charges[-1]["id"]

    response = client.post(
        "/payments/by-card",
        json={"charge_id": charge_id, "card_number": "4111111111111111", "expiration_date": "12/30", "cvv": "123"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "pagamento_cartao"
    assert data["status"] == "aprovada"

def test_deposit(create_users):
    token1 = create_users[0]
    response = client.post(
        "/payments/deposit",
        json={"amount": 1000},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "deposito"
    assert data["status"] == "aprovada"
    assert data["amount"] == 1000

def test_cancel_charge(create_users):
    token1 = create_users[0]
    # Criar cobrança para cancelar
    response = client.post(
        "/charges/",
        json={"value": 50, "description": "Cancelamento teste", "recipient_cpf": "98765432100"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    charge_id = response.json()["id"]

    response = client.post(
        f"/charges/{charge_id}/cancel",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    assert "message" in response.json()

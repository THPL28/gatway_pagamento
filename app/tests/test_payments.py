import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from app.main import app
from app.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
def create_users_and_charge(setup_database):
    user1 = {"name": "User 1", "cpf": "39053344705", "email": "user1@example.com", "password": "password123"}
    user2 = {"name": "User 2", "cpf": "12345678909", "email": "user2@example.com", "password": "password123"}

    client.post("/users/", json=user1)
    client.post("/users/", json=user2)

    response = client.post("/users/token", data={"username": user1["email"], "password": user1["password"]})
    token = response.json()["access_token"]

    response = client.post(
        "/charges/",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": 100, "description": "Teste Charge", "recipient_cpf": user2["cpf"]}
    )
    charge_id = response.json()["id"]
    return token, charge_id

def test_deposit(create_users_and_charge):
    token, _ = create_users_and_charge
    with patch("app.api.external.authorize_payment", return_value=True):
        response = client.post(
            "/payments/deposit",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": 200}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 200
        assert data["status"] == "aprovada"
        assert data["type"] == "deposito"

def test_payment_by_balance(create_users_and_charge):
    token, charge_id = create_users_and_charge
    response = client.post(
        "/payments/by-balance",
        headers={"Authorization": f"Bearer {token}"},
        json={"charge_id": charge_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 100
    assert data["status"] == "aprovada"
    assert data["type"] == "pagamento_saldo"

def test_payment_by_balance_insufficient(create_users_and_charge):
    token, _ = create_users_and_charge
    # Criar nova cobrança maior que o saldo do usuário
    response = client.post(
        "/charges/",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": 1000, "description": "Cobrança Alta", "recipient_cpf": "12345678909"}
    )
    charge_id = response.json()["id"]
    # Tentar pagar com saldo insuficiente
    response = client.post(
        "/payments/by-balance",
        headers={"Authorization": f"Bearer {token}"},
        json={"charge_id": charge_id}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Saldo insuficiente para realizar o pagamento"

def test_payment_by_card(create_users_and_charge):
    token, _ = create_users_and_charge
    response = client.post(
        "/charges/",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": 50, "description": "Charge Cartão", "recipient_cpf": "12345678909"}
    )
    new_charge_id = response.json()["id"]
    with patch("app.api.external.authorize_payment", return_value=True):
        response = client.post(
            "/payments/by-card",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "charge_id": new_charge_id,
                "card_number": "4111111111111111",
                "expiration_date": "12/30",
                "cvv": "123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 50
        assert data["status"] == "aprovada"
        assert data["type"] == "pagamento_cartao"

def test_cancel_charge(create_users_and_charge):
    token, _ = create_users_and_charge
    # Criar cobrança pendente
    response = client.post(
        "/charges/",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": 30, "description": "Charge Cancelar", "recipient_cpf": "12345678909"}
    )
    charge_id = response.json()["id"]

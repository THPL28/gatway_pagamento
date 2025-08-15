import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models import User, Charge

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
def create_users(setup_database):
    # Usuários de teste
    user1 = {"name": "User 1", "cpf": "39053344705", "email": "user1@example.com", "password": "password123"}
    user2 = {"name": "User 2", "cpf": "12345678909", "email": "user2@example.com", "password": "password123"}
    
    client.post("/users/", json=user1)
    client.post("/users/", json=user2)
    return user1, user2

def test_create_charge(create_users):
    user1, user2 = create_users
    
    # Login para obter token do user1
    response = client.post(
        "/users/token",
        data={"username": user1["email"], "password": user1["password"]}
    )
    token = response.json()["access_token"]
    
    # Criar cobrança
    response = client.post(
        "/charges/",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": 100, "description": "Teste Charge", "recipient_cpf": user2["cpf"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 100
    assert data["recipient_id"] is not None

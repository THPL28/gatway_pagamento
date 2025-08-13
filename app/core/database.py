import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

# URL padrão (SQLite local para desenvolvimento)
DEFAULT_SQLITE_URL = "sqlite:///./test.db"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

# Mostra no log qual banco está sendo usado
print(f"[DB] Usando banco de dados: {DATABASE_URL}")

# Configura argumentos de conexão
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
except ImportError as e:
    print(f"Driver necessário para {DATABASE_URL} não instalado: {e}")
    sys.exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency injection para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

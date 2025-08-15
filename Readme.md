
# 💳 Gateway de Pagamentos API

<p align="center">
  <img src="assets/banner_gateway_.png" alt="Gateway de Pagamentos API" width="800"/>
</p>

> **Uma API de gateway de pagamentos** simples e escalável, construída com **FastAPI**, que permite:
> - Criar usuários com saldo inicial 💰  
> - Gerenciar cobranças pendentes e pagas 📄  
> - Processar pagamentos via saldo ou cartão de crédito simulado 💳  

## ✨ Funcionalidades

✅ **Autenticação JWT** — Segurança com tokens de acesso  
✅ **Gerenciamento de Usuários** — Cadastro, saldo inicial e autenticação  
✅ **Gestão de Cobranças** — Criar e listar cobranças  
✅ **Pagamentos** — Via saldo ou cartão de crédito simulado  
✅ **Persistência** — Banco de dados **PostgreSQL**  
✅ **Pronto para Docker** — Fácil configuração e deploy  

## 🛠 Stack Utilizada

| Tecnologia  | Descrição |
|-------------|-----------|
| **Python 3.9+** | Linguagem principal |
| **FastAPI** | Framework web de alta performance |
| **SQLAlchemy** | ORM para interação com PostgreSQL |
| **PostgreSQL** | Banco de dados relacional |
| **Pydantic** | Validação de dados |
| **Docker & Docker Compose** | Ambientes isolados |

## 📊 Fluxo de Funcionamento

<p align="center">
  <img src="assets/banner_gateway.png" alt="Fluxo de Pagamentos" width="700"/>
</p>

## 🚀 Como Rodar o Projeto

### 📋 Pré-requisitos
- Docker  
- Docker Compose  

### 🔧 Passos para instalação

1️⃣ **Clonar o repositório**
```bash
git clone https://github.com/seu_usuario/seu_repositorio.git
cd seu_repositorio
```

2️⃣ **Criar o arquivo `.env`**
```env
DATABASE_URL=postgresql://admin:nimble_dev@db:5432/nimble_db
SECRET_KEY=sua-chave-secreta-forte
ALGORITHM=HS256
```

3️⃣ **Subir o ambiente**
```bash
docker-compose up --build -d
```

4️⃣ **Verificar containers**
```bash
docker-compose ps
```

## 📂 Estrutura do Projeto

```
.
├── .github/
│   ├── workflows/          # CI/CD
│   │    └── cy.yml
├── app/
│   ├── api/                # API externa
│   │   └── external.py
│   ├── auth/               # Autenticação
│   ├── core/               # Configurações globais
│   │   └── database.py
│   ├── crud/               # Create Read Update Delete
│   │   └── database.py
│   ├── models/             # Modelos SQLAlchemy
│   │   └── models.py
│   ├── routers/            # Endpoints
│   │   ├── users.py
│   │   ├── charges.py
│   │   └── payments.py
│   │  schemas/             # Validação Pydantic  
│   │   └── schemas.py
│   ├── tests/              # Testes automatizados
│   │  ├── test_charges.py
│   │  ├── test_payments.py
│   │  ├── test_transactions.py
│   │  └── test_users.py
│   ├── assets/             # Imagens e recursos
│   │    └── img.png
│   └── main.py              # Entrada principal
├── .env
├── docker-compose.yml
└── Dockerfile


```
📖 **Uso da API**
📍 Acesse a documentação localmente

Swagger UI: http://localhost:8000/docs

Redoc: http://localhost:8000/redoc

🌐 Teste a API Online

Você também pode testar a API sem precisar rodar localmente, acessando:
https://gatway-pagamento.koyeb.app/docs

🧪 **Rodando os Testes Automatizados**

Este projeto possui testes unitários para validar o comportamento dos principais recursos da API.

1️⃣ Instale as dependências
```bash
pip install -r requirements.txt
```

2️⃣ **Execute os testes com pytest**
```bash
pytest --cov=app --cov-report=term-missing
```

3️⃣ Testes disponíveis

``tests/test_users.py`` → Testes para criação, autenticação e listagem de usuários.

``tests/test_charges.py`` → Testes para criação e listagem de cobranças.

``tests/test_payments.py`` → Testes para processamento de pagamentos.

``tests/test_transactions.py`` → Testes para histórico e registro de transações.

💡 Dica: É possível executar apenas um teste específico:

```
pytest tests/test_users.py
```

- **E-mail:anderson.cruz@nimblebaas.com.br** 


---

import httpx
from fastapi import HTTPException, status

AUTHORIZER_URL = "https://zsy6tx7aql.execute-api.sa-east-1.amazonaws.com/authorizer"

async def authorize_payment():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(AUTHORIZER_URL, timeout=10)
            response.raise_for_status() # Lança um erro para status 4xx/5xx

            data = response.json()
            if data.get("message") == "Autorizado":
                return True
            else:
                return False
    except httpx.HTTPStatusError as e:
        # Lidar com erros de resposta HTTP
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Erro na comunicação com o autorizador externo: {e.response.text}"
        )
    except httpx.RequestError as e:
        # Lidar com erros de requisição
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Falha ao conectar com o autorizador externo: {e}"
        )
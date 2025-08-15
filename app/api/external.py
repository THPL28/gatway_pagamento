import httpx
from fastapi import HTTPException, status

AUTHORIZER_URL = "https://zsy6tx7aql.execute-api.sa-east-1.amazonaws.com/authorizer"

async def authorize_payment():
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.get(AUTHORIZER_URL)
            response.raise_for_status()  # Lança um erro para status 4xx/5xx

            try:
                data = response.json()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Resposta inválida do autorizador externo"
                )

            return data.get("message") == "Autorizado"

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Erro na comunicação com o autorizador externo: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Falha ao conectar com o autorizador externo: {e}"
        )

import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ---------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GROUP_ID = os.getenv("GROUP_ID")
DATASET_ID = os.getenv("DATASET_ID")

PBI_TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# ---------------------------------------------
# CORS (para que Power BI pueda consumir API)
# ---------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------
def obtener_token():
    """Autenticación con Azure AD para Power BI."""
    data = {
        "client_id": CLIENT_ID,
        "scope": "https://analysis.windows.net/powerbi/api/.default",
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
    }

    r = requests.post(PBI_TOKEN_URL, data=data)

    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error al obtener token: {r.text}")

    return r.json()["access_token"]


def ejecutar_dax_conteo(componente: str) -> int:
    """Ejecuta un DAX para contar registros filtrados por Componente."""

    token = obtener_token()

    url = (
        f"https://api.powerbi.com/v1.0/myorg/groups/"
        f"{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    dax_query = {
        "queries": [
            {
                "query": f"""
                EVALUATE
                ROW(
                    "TotalRegistros",
                    COUNTROWS(
                        FILTER(
                            DATOS,
                            DATOS[Componente] = "{componente}"
                        )
                    )
                )
                """
            }
        ]
    }

    r = requests.post(url, headers=headers, json=dax_query)

    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error ejecutando DAX: {r.text}")

    data = r.json()

    # Extraer correctamente el conteo desde la estructura JSON de Power BI
    try:
        total = data["results"][0]["tables"][0]["rows"][0]["TotalRegistros"]
        return int(total)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interpretando respuesta DAX: {e} | {data}"
        )


# ---------------------------------------------
# ENDPOINTS
# ---------------------------------------------
@app.get("/")
def root():
    return {
        "mensaje": "API lista",
        "estado": "OK",
        "endpoints": [
            "/contar_registros?componente=XXXX"
        ]
    }


@app.get("/contar_registros")
def contar_registros(componente: str):
    """Devuelve la cantidad de registros encontrados en el dataset filtrados por 'Componente'."""
    try:
        total = ejecutar_dax_conteo(componente)
        return {
            "componente": componente,
            "total_registros": total
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------
# MAIN LOCAL (Render NO usa esto)
# ---------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

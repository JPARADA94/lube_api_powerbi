from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import os

app = FastAPI()

# -----------------------------------------------------------
# 1. HABILITAR CORS PARA PERMITIR PETICIONES DESDE WIX
# -----------------------------------------------------------
origins = [
    "*",   # Puedes restringir después, por ahora dejamos abierto
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------
# 2. CONFIGURACIÓN POWER BI
# -----------------------------------------------------------
TENANT_ID   = os.getenv("TENANT_ID")
CLIENT_ID   = os.getenv("CLIENT_ID")
CLIENT_SECRET = "i_a8Q~uePWggn1~~SMHvCUfEsfWDGlN~27Sxfb_i"
GROUP_ID    = os.getenv("GROUP_ID")
DATASET_ID  = os.getenv("DATASET_ID")

TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
PBI_QUERY_URL = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"

# -----------------------------------------------------------
# 3. OBTENER TOKEN
# -----------------------------------------------------------
def obtener_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }

    r = requests.post(TOKEN_URL, data=data)
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error obteniendo token: {r.text}")

    return r.json()["access_token"]

# -----------------------------------------------------------
# 4. ENDPOINT PARA LISTAR FILAS COMPLETAS
# -----------------------------------------------------------
@app.get("/filas")
def obtener_filas(componente: str):

    if not componente:
        raise HTTPException(status_code=400, detail="Debe enviar ?componente=XXXX")

    token = obtener_token()

    # DAX para obtener TODAS las filas del componente
    dax = {
        "queries": [{
            "query": f"""
                EVALUATE
                FILTER(
                    DATOS,
                    DATOS[COMPONENTE] = "{componente}"
                )
            """
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.post(PBI_QUERY_URL, headers=headers, data=json.dumps(dax))

    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error ejecutando DAX: {r.text}")

    data = r.json()

    try:
        filas = data["results"][0]["tables"][0]["rows"]
    except:
        filas = []

    return {
        "componente": componente,
        "total_filas": len(filas),
        "filas": filas
    }

@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente con CORS habilitado"}






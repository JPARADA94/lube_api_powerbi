from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# ---------------------------
# 1. ENDPOINT DE PRUEBA /
# ---------------------------
@app.get("/")
def home():
    return {
        "mensaje": "API lista",
        "power_bi": "Conexión segura preparándose",
        "endpoints": ["/contar_registros?componente=XXXX"]
    }


# ---------------------------
# 2. MODELO DE RESPUESTA
# ---------------------------
class ConteoRespuesta(BaseModel):
    componente: str
    total_registros: int


# ---------------------------
# 3. OBTENER TOKEN DE POWER BI
# ---------------------------
def obtener_token():
    tenant = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }

    r = requests.post(url, data=body)
    if r.status_code != 200:
        raise HTTPException(500, f"Error obteniendo token: {r.text}")

    return r.json()["access_token"]


# ---------------------------
# 4. CONSULTAR DATOS DE POWER BI
# ---------------------------
def obtener_datos_real():
    token = obtener_token()

    group_id = os.getenv("GROUP_ID")
    dataset_id = os.getenv("DATASET_ID")

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/tables/DATOS/rows"

    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise HTTPException(500, f"Error consultando dataset: {r.text}")

    return r.json()["value"]  # Lista de filas


# ---------------------------
# 5. ENDPOINT PRINCIPAL
# ---------------------------
@app.get("/contar_registros", response_model=ConteoRespuesta)
def contar_registros(componente: str):
    """
    Busca cuántas filas tienen el componente especificado.
    """

    # Obtener filas REALES del dataset Power BI
    filas = obtener_datos_real()

    coincidencias = [
        f for f in filas
        if str(f.get("Componente", "")).lower() == componente.lower()
    ]

    if not coincidencias:
        raise HTTPException(404, f"El componente '{componente}' no existe.")

    return ConteoRespuesta(
        componente=componente,
        total_registros=len(coincidencias)
    )




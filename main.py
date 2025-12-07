from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# HABILITAR CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======= CONFIGURACIÓN POWER BI =======
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
POWER_BI_GROUP_ID = os.getenv("POWER_BI_GROUP_ID")
POWER_BI_DATASET_ID = os.getenv("POWER_BI_DATASET_ID")
POWER_BI_TABLE_NAME = os.getenv("POWER_BI_TABLE_NAME")  # Ej: "DATOS"


# ======= OBTENER TOKEN DE POWER BI =======
def obtener_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }

    response = requests.post(url, data=payload)
    response.raise_for_status()

    return response.json()["access_token"]


# ======= ENDPOINT RAÍZ =======
@app.get("/")
def home():
    return {
        "mensaje": "API lista",
        "estado": "OK",
        "endpoints": [
            "/contar_registros?componente=XXXX"
        ]
    }


# ======= ENDPOINT PARA CONSULTAR POWER BI (CON DEBUG) =======
@app.get("/contar_registros")
def contar_registros(componente: str = Query(...)):
    """
    Devuelve la respuesta EXACTA que envía Power BI.
    Luego interpretamos dónde está TotalRegistros realmente.
    """

    try:
        token = obtener_token()

        url_dax = (
            f"https://api.powerbi.com/v1.0/myorg/groups/"
            f"{POWER_BI_GROUP_ID}/datasets/{POWER_BI_DATASET_ID}/executeQueries"
        )

        dax_query = {
            "queries": [{
                "query":
                    f"EVALUATE ROW("
                    f"'TotalRegistros', CALCULATE(COUNTROWS('{POWER_BI_TABLE_NAME}'), "
                    f"'{POWER_BI_TABLE_NAME}'[Componente] = \"{componente}\")"
                    f")"
            }]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url_dax, json=dax_query, headers=headers)
        response.raise_for_status()

        data = response.json()

        # ======= MODO DEBUG: MOSTRAR TODO =======
        return {
            "debug": "MOSTRANDO RESPUESTA COMPLETA DE POWER BI",
            "componente_consultado": componente,
            "respuesta_powerbi": data
        }

    except Exception as e:
        return {"detail": str(e)}


# ========= FIN DEL ARCHIVO =========





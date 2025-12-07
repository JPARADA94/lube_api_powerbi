from fastapi import FastAPI
import requests
import json
import os

app = FastAPI()

# ---------- CONFIG -----------------
TENANT_ID = "d954438c-7f11-4a1a-b7ee-f77d6c48ec0a"
CLIENT_ID = "70348d88-7eff-4fd4-99ff-dec8cee6afec"
CLIENT_SECRET = "i_a8Q~uePWggn1~~SMHvCUfEsfWDGlN~27Sxfb_i"

GROUP_ID = "bd2f044c-eb69-4ebc-b1ed-ebdf71c33b77"
DATASET_ID = "1e30ac8a-b779-40ed-a18c-883383e44014"

# Tabla y columna EXACTAS del modelo
TABLE_NAME = "DATOS"
COLUMN_NAME = "COMPONENTE"
# -----------------------------------

# 🔐 Obtener token de Azure AD
def obtener_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }

    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]

@app.get("/")
def home():
    return {"mensaje": "API conectada correctamente"}

@app.get("/contar_registros")
def contar_registros(componente: str):

    try:
        token = obtener_token()

        # DAX dinámico
        dax_query = f"""
        EVALUATE
        ROW(
            "TotalRegistros",
            COUNTROWS(
                FILTER(
                    '{TABLE_NAME}',
                    '{TABLE_NAME}'[{COLUMN_NAME}] = "{componente}"
                )
            )
        )
        """

        url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        payload = {
            "queries": [{"query": dax_query}],
            "serializerSettings": {"incudeNulls": True}
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        resultado = response.json()

        # Extraer valor devuelto por el DAX
        total = resultado["results"][0]["tables"][0]["rows"][0]["TotalRegistros"]

        return {
            "componente": componente,
            "total_registros": total
        }

    except Exception as e:
        return {"error": str(e)}



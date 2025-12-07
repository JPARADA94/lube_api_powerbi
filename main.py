from fastapi import FastAPI
import requests
import json
import os

app = FastAPI()

# ---------- CONFIG -----------------
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

GROUP_ID = "bd2f044c-eb69-4ebc-b1ed-ebdf71c33b77"
DATASET_ID = "1e30ac8a-b779-40ed-a18c-883383e44014"

TABLE_NAME = "DATOS"
COLUMN_NAME = "COMPONENTE"
# -----------------------------------

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
    return {"mensaje": "API funcionando correctamente"}

@app.get("/contar")
def contar(componente: str):

    try:
        token = obtener_token()

        # Consulta DAX → Cuenta cuántas veces se repite el valor
        dax = f"""
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

        payload = {"queries": [{"query": dax}]}

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        data = response.json()

        # Extraer resultado del JSON
        filas = data["results"][0]["tables"][0]["rows"]

        if not filas:
            total = 0
        else:
            total = filas[0].get("TotalRegistros", 0)

        return {
            "componente": componente,
            "total_registros": total
        }

    except Exception as e:
        return {"error": str(e)}




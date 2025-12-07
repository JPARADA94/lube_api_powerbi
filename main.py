from fastapi import FastAPI, HTTPException
import requests
import json
import os

app = FastAPI()

# -----------------------------
# 🔐 CONFIGURACIÓN POWER BI
# -----------------------------
TENANT_ID    = "d954438c-7f11-4a1a-b7ee-f77d6c48ec0a"
CLIENT_ID    = "70348d88-7eff-4fd4-99ff-dec8cee6afec"
CLIENT_SECRET = "i_a8Q~uePWggn1~~SMHvCUfEsfWDGlN~27Sxfb_i"

GROUP_ID     = "bd2f044c-eb69-4ebc-b1ed-ebdf71c33b77"
DATASET_ID   = "1e30ac8a-b779-40ed-a18c-883383e44014"

TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
EXECUTE_URL = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"


# -----------------------------
# 🔐 OBTENER TOKEN
# -----------------------------
def obtener_token():
    datos = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }

    respuesta = requests.post(TOKEN_URL, data=datos)

    if respuesta.status_code != 200:
        raise HTTPException(500, f"Error obteniendo token: {respuesta.text}")

    return respuesta.json()["access_token"]


# -----------------------------
# 🔍 CONSULTAR CANTIDAD DE REGISTROS
# -----------------------------
def contar_componente(valor_componente: str):
    token = obtener_token()

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
                                DATOS[COMPONENTE] = "{valor_componente}"
                            )
                        )
                    )
                """
            }
        ]
    }

    r = requests.post(EXECUTE_URL, headers=headers, data=json.dumps(dax_query))

    if r.status_code != 200:
        raise HTTPException(500, f"Power BI error: {r.text}")

    data = r.json()

    # -----------------------------
    # 📌 FIX IMPORTANTE
    # Power BI devuelve rows = [[{ "TotalRegistros": X }]]
    # -----------------------------
    try:
        rows = data["results"][0]["tables"][0]["rows"]

        if not rows or not rows[0] or not isinstance(rows[0][0], dict):
            raise Exception("Formato desconocido")

        total = rows[0][0].get("TotalRegistros", 0)

    except Exception as e:
        raise HTTPException(500, f"Error interpretando respuesta DAX: {data}")

    return total


# -----------------------------
# 🌐 ENDPOINTS
# -----------------------------
@app.get("/")
def home():
    return {
        "mensaje": "API funcionando correctamente en Render",
        "endpoint_ejemplo": "/contar?componente=EC123-M"
    }


@app.get("/contar")
def contar_endpoint(componente: str):
    total = contar_componente(componente)
    return {
        "componente": componente,
        "total_registros": total
    }



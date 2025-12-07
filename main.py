from fastapi import FastAPI, Query
import requests
import os

app = FastAPI()

# ====== CONFIGURACIÓN =======
POWER_BI_TENANT_ID = os.getenv("TENANT_ID")
POWER_BI_CLIENT_ID = os.getenv("CLIENT_ID")
POWER_BI_SECRET = os.getenv("CLIENT_SECRET")
POWER_BI_GROUP_ID = os.getenv("GROUP_ID")
POWER_BI_DATASET_ID = os.getenv("DATASET_ID")
POWER_BI_TABLE_NAME = "DATOS"

TOKEN_URL = f"https://login.microsoftonline.com/{POWER_BI_TENANT_ID}/oauth2/v2.0/token"

# =========================================
# Obtener token OAuth2
# =========================================
def obtener_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": POWER_BI_CLIENT_ID,
        "client_secret": POWER_BI_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default",
    }

    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


# =========================================
# Inicio de la API
# =========================================
@app.get("/")
def home():
    return {
        "mensaje": "API lista",
        "estado": "OK",
        "endpoints": ["/contar_registros?componente=XXXX"]
    }


# =========================================
# Endpoint principal: contar registros por componente
# =========================================
@app.get("/contar_registros")
def contar_registros(componente: str = Query(...)):
    try:
        token = obtener_token()

        url_dax = f"https://api.powerbi.com/v1.0/myorg/groups/{POWER_BI_GROUP_ID}/datasets/{POWER_BI_DATASET_ID}/executeQueries"

        dax = {
            "queries": [{
                "query": f"EVALUATE ROW(\"TotalRegistros\", CALCULATE(COUNTROWS('{POWER_BI_TABLE_NAME}'), '{POWER_BI_TABLE_NAME}'[Componente] = \"{componente}\"))"
            }]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url_dax, json=dax, headers=headers)
        response.raise_for_status()

        data = response.json()

        # Extraer el valor de la respuesta de Power BI
        resultado = data["results"][0]["tables"][0]["rows"][0]["TotalRegistros"]

        return {
            "componente": componente,
            "TotalRegistros": resultado
        }

    except Exception as e:
        return {"detail": str(e)}



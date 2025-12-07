from fastapi import FastAPI, HTTPException
import requests
import json

# =========================================================
# CONFIGURACIONES - RELLENA CON TUS DATOS
# =========================================================

TENANT_ID     = "d954438c-7f11-4a1a-b7ee-f77d6c48ec0a"
CLIENT_ID     = "70348d88-7eff-4fd4-99ff-dec8cee6afec"
CLIENT_SECRET = "i_a8Q~uePWggn1~~SMHvCUfEsfWDGlN~27Sxfb_i"

GROUP_ID      = "bd2f044c-eb69-4ebc-b1ed-ebdf71c33b77"
DATASET_ID    = "1e30ac8a-b779-40ed-a18c-883383e44014"

TABLE_NAME    = "DATOS"
COLUMN_NAME   = "COMPONENTE"

TOKEN_URL     = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
EXECUTE_URL   = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(title="API Lube PowerBI", version="2.0")


# =========================================================
# FUNCIÓN PARA OBTENER TOKEN
# =========================================================
def obtener_token():
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }

    r = requests.post(TOKEN_URL, data=data)

    if r.status_code != 200:
        raise HTTPException(500, f"Error obteniendo token: {r.text}")

    return r.json()["access_token"]


# =========================================================
# ENDPOINT PRINCIPAL DE PRUEBA
# =========================================================
@app.get("/")
def home():
    return {
        "mensaje": "API funcionando correctamente",
        "endpoints": [
            "/contar?componente=XXXX",
            "/filas?componente=XXXX"
        ]
    }


# =========================================================
# ENDPOINT 1: CONTAR REGISTROS
# =========================================================
@app.get("/contar")
def contar_registros(componente: str):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    dax = f"""
    EVALUATE
    ROW(
        "TotalRegistros",
        CALCULATE(
            COUNTROWS('{TABLE_NAME}'),
            '{TABLE_NAME}'[{COLUMN_NAME}] = "{componente}"
        )
    )
    """

    body = {"queries": [{"query": dax}]}

    r = requests.post(EXECUTE_URL, headers=headers, json=body)

    if r.status_code != 200:
        raise HTTPException(500, f"Error desde Power BI: {r.text}")

    data = r.json()

    try:
        rows = data["results"][0]["tables"][0]["rows"]
        fila = rows[0]

        # Power BI puede devolver: "TotalRegistros" o "[TotalRegistros]"
        if "TotalRegistros" in fila:
            total = fila["TotalRegistros"]
        elif "[TotalRegistros]" in fila:
            total = fila["[TotalRegistros]"]
        else:
            raise Exception(f"Clave inesperada: {fila}")

    except Exception as e:
        raise HTTPException(500, f"Error interpretando respuesta DAX: {data}")

    return {
        "componente": componente,
        "total_registros": total
    }


# =========================================================
# ENDPOINT 2: OBTENER TODAS LAS FILAS DEL COMPONENTE
# =========================================================
@app.get("/filas")
def obtener_filas(componente: str):

    token = obtener_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    dax = f"""
    EVALUATE
    FILTER(
        {TABLE_NAME},
        {TABLE_NAME}[{COLUMN_NAME}] = "{componente}"
    )
    """

    body = {"queries": [{"query": dax}]}

    r = requests.post(EXECUTE_URL, headers=headers, json=body)

    if r.status_code != 200:
        raise HTTPException(500, f"Error desde Power BI: {r.text}")

    data = r.json()

    try:
        filas = data["results"][0]["tables"][0]["rows"]
    except:
        raise HTTPException(500, f"Error interpretando respuesta: {data}")

    return {
        "componente": componente,
        "total_filas": len(filas),
        "filas": filas
    }








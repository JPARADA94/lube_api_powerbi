from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

# =========================================================
# CONFIGURACIONES - RELLENA CON TUS DATOS CORRECTOS
# =========================================================

TENANT_ID   = "d954438c-7f11-4a1a-b7ee-f77d6c48ec0a"
CLIENT_ID   = "70348d88-7eff-4fd4-99ff-dec8cee6afec"
CLIENT_SECRET = "i_a8Q~uePWggn1~~SMHvCUfEsfWDGlN~27Sxfb_i" 

GROUP_ID    = "bd2f044c-eb69-4ebc-b1ed-ebdf71c33b77"
DATASET_ID  = "1e30ac8a-b779-40ed-a18c-883383e44014"

TABLE_NAME  = "DATOS"          # Nombre EXACTO de la tabla
COLUMN_NAME = "COMPONENTE"     # Nombre EXACTO de la columna

# =========================================================
# INICIALIZAR API
# =========================================================

app = FastAPI(title="API Conteo Power BI", version="1.0")


# =========================================================
# FUNCIONES DE AUTENTICACIÓN
# =========================================================

def obtener_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }

    resp = requests.post(url, data=data)
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error obteniendo token: {resp.text}")

    return resp.json()["access_token"]


# =========================================================
# ENDPOINT DE PRUEBA
# =========================================================

@app.get("/")
def root():
    return {
        "mensaje": "API funcionando correctamente en Render",
        "endpoints": [
            "/contar?componente=XXXX"
        ]
    }


# =========================================================
# ENDPOINT PRINCIPAL: CONTAR REGISTROS
# =========================================================

@app.get("/contar")
def contar_registros(componente: str):

    token = obtener_token()

    # Construcción del DAX
    dax_query = f"""
    EVALUATE
    ROW(
        "TotalRegistros",
        CALCULATE(
            COUNTROWS('{TABLE_NAME}'),
            '{TABLE_NAME}'[{COLUMN_NAME}] = "{componente}"
        )
    )
    """

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {"queries": [{"query": dax_query}]}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error desde Power BI: {response.text}")

    data = response.json()

    try:
        rows = data["results"][0]["tables"][0]["rows"]
        fila = rows[0]  # El resultado está dentro de una fila dentro de una lista

        # Power BI puede devolver:
        #   "TotalRegistros"
        #   "[TotalRegistros]"
        if "TotalRegistros" in fila:
            total = fila["TotalRegistros"]
        elif "[TotalRegistros]" in fila:
            total = fila["[TotalRegistros]"]
        else:
            raise Exception(f"Formato inesperado en respuesta: {fila}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interpretando respuesta DAX: {str(e)}")

    return {
        "componente": componente,
        "total_registros": total
    }
@app.get("/filas")
def obtener_filas(componente: str):

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
                    FILTER(
                        {TABLE_NAME},
                        {TABLE_NAME}[{COLUMN_NAME}] = "{componente}"
                    )
                """
            }
        ]
    }

    r = requests.post(EXECUTE_URL, headers=headers, json=dax_query)

    if r.status_code != 200:
        raise HTTPException(500, f"Error desde Power BI: {r.text}")

    data = r.json()

    try:
        rows = data["results"][0]["tables"][0]["rows"]
    except:
        raise HTTPException(500, f"Error interpretando respuesta: {data}")

    # Devolver todas las filas completas
    return {
        "componente": componente,
        "total_filas": len(rows),
        "filas": rows
    }







from fastapi import FastAPI
from pydantic import BaseModel
import requests

TENANT_ID = "d954438c-7f11-4a1a-b7ee-f77d6c48ec0a"
CLIENT_ID = "70348d88-7eff-4fd4-99ff-dec8cee6afec"
CLIENT_SECRET = "i_a8Q~uePWggn1~~SMHvCUfEsfWDGlN~27Sxfb_i"
GROUP_ID = "bd2f044c-eb69-4ebc-b1ed-ebdf71c33b77"
DATASET_ID = "1e30ac8a-b779-40ed-a18c-883383e44014"

app = FastAPI()

class ComponenteRequest(BaseModel):
    componente: str

def obtener_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }
    r = requests.post(url, data=data)
    r.raise_for_status()
    return r.json()["access_token"]

@app.post("/verificar-componente")
def verificar_componente(req: ComponenteRequest):
    token = obtener_token()

    query = {
        "queries": [
            {
                "query": f"""
                EVALUATE
                SUMMARIZE(
                    FILTER(DATOS, DATOS[Componente] = "{req.componente}"),
                    DATOS[Componente],
                    "TotalRegistros", COUNTROWS(DATOS)
                )
                """
            }
        ]
    }

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    r = requests.post(url, json=query, headers=headers)
    r.raise_for_status()
    rows = r.json()["results"][0]["tables"][0]["rows"]

    if len(rows) == 0:
        return {"existe": False, "componente": req.componente, "total_registros": 0}
    else:
        return {"existe": True, "componente": req.componente, "total_registros": rows[0]["TotalRegistros"]}

@app.post("/obtener-datos")
def obtener_datos(req: ComponenteRequest):
    token = obtener_token()

    query = {
        "queries": [
            {
                "query": f"""
                EVALUATE
                TOPN(
                    20,
                    FILTER(DATOS, DATOS[Componente] = "{req.componente}"),
                    DATOS[Fecha], DESC
                )
                """
            }
        ]
    }

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    r = requests.post(url, json=query, headers=headers)
    r.raise_for_status()
    rows = r.json()["results"][0]["tables"][0]["rows"]

    return {"componente": req.componente, "filas": rows}


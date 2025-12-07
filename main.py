from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests

app = FastAPI()

# ---------------------------
# MODELO DE RESPUESTA
# ---------------------------
class ConteoRespuesta(BaseModel):
    componente: str
    total_registros: int


# ---------------------------
# ENDPOINT RAÍZ DE PRUEBA
# ---------------------------
@app.get("/")
def home():
    return {
        "mensaje": "API lista y conectada a Power BI (executeQueries)",
        "endpoints": [
            "/contar_registros?componente=XXXX"
        ]
    }


# ---------------------------
# OBTENER TOKEN DE AZURE AD
# ---------------------------
def obtener_token():
    tenant = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if not all([tenant, client_id, client_secret]):
        raise HTTPException(
            status_code=500,
            detail="Faltan variables de entorno TENANT_ID, CLIENT_ID o CLIENT_SECRET"
        )

    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }

    r = requests.post(url, data=body)
    if r.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo token: {r.text}"
        )

    return r.json()["access_token"]


# ---------------------------
# FUNCIÓN QUE EJECUTA DAX EN POWER BI
# ---------------------------
def ejecutar_dax_conteo(componente: str) -> int:
    """
    Ejecuta una consulta DAX sobre la tabla DATOS para contar
    cuántas filas tienen ese componente.
    """

    token = obtener_token()
    group_id = os.getenv("GROUP_ID")
    dataset_id = os.getenv("DATASET_ID")

    if not all([group_id, dataset_id]):
        raise HTTPException(
            status_code=500,
            detail="Faltan variables de entorno GROUP_ID o DATASET_ID"
        )

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/executeQueries"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 👇 DAX: cuenta filas en la tabla DATOS filtrando por [Componente]
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
                            DATOS[Componente] = "{componente}"
                        )
                    )
                )
                """
            }
        ]
    }

    r = requests.post(url, headers=headers, json=dax_query)

    if r.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando DAX: {r.text}"
        )

    data = r.json()

    try:
        rows = data["results"][0]["tables"][0]["rows"]
        if not rows:
            return 0
        # La columna de la fila ROW se llama "TotalRegistros"
        total = rows[0]["TotalRegistros"]
        return int(total)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interpretando respuesta DAX: {e} | {data}"
        )


# ---------------------------
# ENDPOINT /contar_registros
# ---------------------------
@app.get("/contar_registros", response_model=ConteoRespuesta)
def contar_registros(componente: str):
    """
    Devuelve cuántas filas tiene el componente en la tabla DATOS.
    Usa executeQueries (DAX) sobre el dataset de Power BI.
    """

    total = ejecutar_dax_conteo(componente)

    if total == 0:
        # Si quieres que devuelva 0 en vez de 404, cambia esto
        raise HTTPException(
            status_code=404,
            detail=f"No hay registros para el componente '{componente}'."
        )

    return ConteoRespuesta(
        componente=componente,
        total_registros=total
    )





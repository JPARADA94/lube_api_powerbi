from fastapi import FastAPI, HTTPException
import requests
import json

app = FastAPI()

# -----------------------------------------
# CONFIGURACIÓN DE POWER BI (NO CAMBIAR)
# -----------------------------------------
GROUP_ID = "bd2f044c-eb69-4ebc-b1ed-ebdf71c33b77"
DATASET_ID = "1e30ac8a-b779-40ed-a18c-883383e44014"
TABLE_NAME = "DATOS"   # Nombre EXACTO de la tabla en tu dataset

# Token generado desde Power BI (Embed Token o Service Principal)
# >>> IMPORTANTE: Reemplazar por tu token válido <<<
TOKEN = "TU_TOKEN_AQUI"


# -----------------------------------------
# ENDPOINT DE PRUEBA
# -----------------------------------------
@app.get("/")
def home():
    return {
        "mensaje": "API funcionando correctamente en Render",
        "endpoints": [
            "/contar?componente=XXXX"
        ]
    }


# -----------------------------------------
# ENDPOINT PARA CONTAR REGISTROS
# -----------------------------------------
@app.get("/contar")
def contar(componente: str):

    if not componente:
        raise HTTPException(status_code=400, detail="Falta el parámetro 'componente'")

    # 🔥 Convertimos a MAYÚSCULAS y eliminamos espacios
    componente = componente.strip().upper()

    # -----------------------------------------
    # DAX ROBUSTO (YO ME ENCARGO DE TODO ESTO)
    # -----------------------------------------
    dax_query = f"""
    EVALUATE
    VAR ComponenteBuscado = TRIM(UPPER("{componente}"))
    RETURN
    ROW(
        "TotalRegistros",
        COUNTROWS(
            FILTER(
                {TABLE_NAME},
                TRIM(UPPER({TABLE_NAME}[COMPONENTE])) = ComponenteBuscado
            )
        )
    )
    """

    # -----------------------------------------
    # POST A POWER BI API
    # -----------------------------------------
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }

    body = {
        "queries": [{"query": dax_query}],
        "serializerSettings": {"includeNulls": True}
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))

    # Verificar si Power BI responde con error
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    pb_response = response.json()

    try:
        total = pb_response["results"][0]["tables"][0]["rows"][0]["TotalRegistros"]
    except:
        raise HTTPException(status_code=500, detail="Error interpretando los datos devueltos por Power BI")

    # -----------------------------------------
    # RESPUESTA FINAL
    # -----------------------------------------
    return {
        "componente": componente,
        "total_registros": total
    }

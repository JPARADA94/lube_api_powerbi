from fastapi import FastAPI

app = FastAPI()

# --- Simulación de tu tabla "DATOS" en Power BI ---
# Reemplazaremos esto luego por una consulta real a Power BI
DATOS = [
    {"Componente": "MOTOR_A"},
    {"Componente": "MOTOR_A"},
    {"Componente": "MOTOR_A"},
    {"Componente": "KC110-M"},
    {"Componente": "KC110-M"},
    {"Componente": "115093 MOTOR"},
    {"Componente": "115093 MOTOR"},
    {"Componente": "115093 MOTOR"},
    {"Componente": "115093 MOTOR"},
]

@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente en Render"}

@app.get("/contar")
def contar(componente: str):
    # Filtro exacto
    coincidencias = [fila for fila in DATOS if fila["Componente"] == componente]

    return {
        "componente": componente,
        "total_registros": len(coincidencias)
    }




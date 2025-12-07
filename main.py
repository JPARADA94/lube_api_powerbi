from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"mensaje": "API funcionando correctamente en Render"}

@app.get("/saludo")
def saludo(nombre: str = "Javier"):
    return {"saludo": f"Hola {nombre}, la API está viva!"}






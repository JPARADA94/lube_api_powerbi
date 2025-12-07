def ejecutar_dax_conteo(componente: str) -> int:

    token = obtener_token()
    group_id = os.getenv("GROUP_ID")
    dataset_id = os.getenv("DATASET_ID")

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/executeQueries"

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
        raise HTTPException(status_code=500, detail=f"Error ejecutando DAX: {r.text}")

    data = r.json()

    try:
        total = data["results"][0]["tables"][0]["rows"][0]["TotalRegistros"]
        return int(total)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interpretando respuesta DAX: {e} | {data}"
        )







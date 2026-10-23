import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.fastapi_app:app", reload=True)

import uvicorn
from app.main import app

if __name__ == "__main__":
    # Starts the FastAPI Uvicorn server on port 8000 with auto-reload
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
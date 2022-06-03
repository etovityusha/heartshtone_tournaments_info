import uvicorn
from fastapi import FastAPI

from api.tournaments.endpoints import router as tournaments_router

app = FastAPI()

app.include_router(tournaments_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7100, log_level="info", proxy_headers=True)
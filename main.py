import uvicorn
from src.config import config
import os

if __name__ == "__main__":
    # Default to True for reload unless UVICORN_RELOAD is set to 'false'
    reload_flag = os.getenv("UVICORN_RELOAD", "true").lower() != "false"
    uvicorn.run("src:app", host="0.0.0.0", port=config["port"], reload=reload_flag)
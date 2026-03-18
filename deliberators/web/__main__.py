"""Entry point: uv run python -m deliberators.web."""

import uvicorn

from deliberators.web.server import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

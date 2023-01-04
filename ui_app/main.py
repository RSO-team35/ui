from typing import List
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from .dashapp import create_dash_app


description = "Fast and responsive UI"

app = FastAPI(title="UI", description=description, docs_url="/openapi")

dash_app = create_dash_app(requests_pathname_prefix="/dash/")
app.mount("/dash", WSGIMiddleware(dash_app.server))

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    response = RedirectResponse("/dash/")
    return response

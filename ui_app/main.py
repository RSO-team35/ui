from typing import List
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from .dashapp import create_dash_app


description = "todo"


app = FastAPI(title="UI", description=description)

app.mount("/static", StaticFiles(directory="static"), name="static")

dash_app = create_dash_app(requests_pathname_prefix="/dash/")
app.mount("/dash", WSGIMiddleware(dash_app.server))

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})


# sources - delete later
# fastapi docs: https://fastapi.tiangolo.com/advanced/templates/
# templating and starlette docs: https://www.starlette.io/templates/
#
# article: https://eugeneyan.com/writing/how-to-set-up-html-app-with-fastapi-jinja-forms-templates/
# ^github repo: https://github.com/eugeneyan/fastapi-html
#
# article: https://christophergs.com/tutorials/ultimate-fastapi-tutorial-pt-6-jinja-templates/ 
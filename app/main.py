from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import BASE_DIR, seed_database
from .routers import customers, dashboard, transactions


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_database()
    yield


app = FastAPI(title="FakeBank", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(transactions.router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"active": "dashboard"})


@app.get("/customers", response_class=HTMLResponse)
def customers_page(request: Request):
    return templates.TemplateResponse(request=request, name="customers.html", context={"active": "customers"})


@app.get("/transactions", response_class=HTMLResponse)
def transactions_page(request: Request):
    return templates.TemplateResponse(request=request, name="transactions.html", context={"active": "transactions"})


@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request):
    return templates.TemplateResponse(request=request, name="alerts.html", context={"active": "alerts"})

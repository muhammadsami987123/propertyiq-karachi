"""PropertyIQ backend entrypoint: FastAPI app, middleware, and router wiring."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import admin, analytics, calculator, comparison, geo, locations, search
from app.config import STATIC_DIR, TEMPLATES_DIR, settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("propertyiq")

app = FastAPI(
    title="PropertyIQ API",
    description="Karachi real-estate intelligence platform backend.",
    version="1.0.0",
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Never leak a raw stack trace to API consumers."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# Static assets and templates (owned/populated by the frontend agent).
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# API routers.
app.include_router(locations.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(comparison.router, prefix="/api")
app.include_router(calculator.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(geo.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# --- Page routes (server-rendered shells; data is fetched client-side from /api) ---


@app.get("/", response_class=HTMLResponse, tags=["pages"])
def page_home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/explore", response_class=HTMLResponse, tags=["pages"])
def page_explore(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "explore.html", {})


@app.get("/compare", response_class=HTMLResponse, tags=["pages"])
def page_compare(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "compare.html", {})


@app.get("/investment", response_class=HTMLResponse, tags=["pages"])
def page_investment(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "investment.html", {})


@app.get("/methodology", response_class=HTMLResponse, tags=["pages"])
def page_methodology(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "methodology.html", {})


@app.get("/about", response_class=HTMLResponse, tags=["pages"])
def page_about(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "about.html", {})


@app.get("/admin", response_class=HTMLResponse, tags=["pages"])
def page_admin(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "admin.html", {})


@app.get("/karachi/{slug}", response_class=HTMLResponse, tags=["pages"])
def page_location(request: Request, slug: str) -> HTMLResponse:
    return templates.TemplateResponse(request, "location.html", {"slug": slug})

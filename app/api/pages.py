"""HTML pages for login / register (vanilla frontend)."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
PAGES_DIRECTORY = WEB_ROOT / "pages"

pages_router = APIRouter(tags=["pages"])


def _page_file(page_file_name: str) -> FileResponse:
    return FileResponse(PAGES_DIRECTORY / page_file_name)


@pages_router.get("/")
def redirect_root_to_login() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=302)


@pages_router.get("/login")
def open_login_page() -> FileResponse:
    return _page_file("login.html")


@pages_router.get("/register")
def open_register_page() -> FileResponse:
    return _page_file("register.html")


@pages_router.get("/home")
def open_home_page() -> FileResponse:
    return _page_file("home.html")


@pages_router.get("/tickets")
def open_my_tickets_page() -> FileResponse:
    """Client home: list of own tickets."""
    return _page_file("my_tickets.html")


@pages_router.get("/tickets/new")
def open_new_ticket_page() -> FileResponse:
    return _page_file("new_ticket.html")

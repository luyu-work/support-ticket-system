"""
Local launcher for the Support Ticket System API.

Usage (from project folder, with venv active):
    python start_project.py
"""

import uvicorn


def run_local_development_server() -> None:
    """Start uvicorn with auto-reload for local work."""
    uvicorn.run(
        "app.main:ticket_system_application",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run_local_development_server()

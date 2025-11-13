"""
Dashboard Routes for CryptoSatX
Serves the modern interactive dashboard
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_home():
    """
    Serve the main dashboard homepage
    Redirects to /dashboard for better UX
    """
    dashboard_path = os.path.join(os.path.dirname(__file__), "../../static/dashboard/index.html")

    try:
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html>
                <head><title>CryptoSatX - Dashboard Not Found</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>Dashboard Not Found</h1>
                    <p>The dashboard files are not available. Please check the installation.</p>
                    <p><a href="/docs">Go to API Documentation</a></p>
                </body>
            </html>
            """,
            status_code=404
        )


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """
    Serve the interactive dashboard
    Modern UI for monitoring signals, analytics, and performance
    """
    dashboard_path = os.path.join(os.path.dirname(__file__), "../../static/dashboard/index.html")

    try:
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html>
                <head><title>CryptoSatX - Dashboard Not Found</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>Dashboard Not Found</h1>
                    <p>The dashboard files are not available. Please check the installation.</p>
                    <p><a href="/docs">Go to API Documentation</a></p>
                </body>
            </html>
            """,
            status_code=404
        )

import os
import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="llm_convergence",
    show_built_with_reflex=False,
    env=rx.Env.PROD if os.getenv("REFLEX_ENV", "prod").lower() == "prod" else rx.Env.DEV,
    frontend_port=int(os.getenv("REFLEX_FRONTEND_PORT", "3000")),
    backend_port=int(os.getenv("REFLEX_BACKEND_PORT", "8000")),
    plugins=[SitemapPlugin()],
)

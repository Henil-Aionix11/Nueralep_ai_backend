"""Main application entry point."""

import uvicorn

from app.web.settings import settings


def main() -> None:
    """
    Run the FastAPI application.

    Uses application factory pattern with pre-initialized services.
    Services are loaded during startup in lifespan_setup for better performance.
    """
    uvicorn.run(
        "app.web.application:get_app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers_count,
        log_level=settings.log_level.value.lower(),
        factory=True,
        http="h11",
        timeout_keep_alive=90,
        server_header=False,
    )


if __name__ == "__main__":
    main()

from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

# index.html must be checked on every load, or browsers (phones especially) keep showing
# the previous release after an update. Files in assets/ have a content hash in their
# name, so they never change and can be cached for good.
NO_CACHE = {"Cache-Control": "no-cache"}
FOREVER = {"Cache-Control": "public, max-age=31536000, immutable"}


def mount_spa(app: FastAPI, dist: Path) -> None:
    """Serves the built frontend, falling back to index.html for client-side routes."""
    dist = dist.resolve()
    index = dist / "index.html"

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        if not index.is_file():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"Frontend not built: {index} is missing. Run `npm run build` in frontend/.",
            )
        candidate = (dist / path).resolve()
        # resolve() + is_relative_to blocks ../ traversal out of the dist folder.
        if path and candidate.is_relative_to(dist) and candidate.is_file():
            hashed = path.startswith("assets/")
            return FileResponse(candidate, headers=FOREVER if hashed else NO_CACHE)
        return FileResponse(index, headers=NO_CACHE)

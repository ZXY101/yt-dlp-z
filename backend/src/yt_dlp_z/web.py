from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse


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
            return FileResponse(candidate)
        return FileResponse(index)

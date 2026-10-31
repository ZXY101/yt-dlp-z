import asyncio


async def communicate(
    process: asyncio.subprocess.Process, stdin: bytes | None = None
) -> tuple[bytes, bytes]:
    """process.communicate() that never leaves the process behind. Callers wrap it in
    asyncio.timeout(); a timeout or the app stopping cancels it, which kills the process."""
    try:
        return await process.communicate(stdin)
    except asyncio.CancelledError:
        process.kill()
        await process.wait()
        raise

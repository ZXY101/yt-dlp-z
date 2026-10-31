from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.db.models.proxy import Proxy
from yt_dlp_z.schemas.proxies import ProxyCreate, ProxyOut, ProxySettings, ProxyUpdate
from yt_dlp_z.services.proxies import store
from yt_dlp_z.services.proxies.check import check_proxy

router = APIRouter(prefix="/api/proxies", tags=["proxies"], dependencies=[Depends(require_auth)])


def _out(proxy: Proxy) -> ProxyOut:
    out = ProxyOut.model_validate(proxy)
    return out.model_copy(update={"url": store.masked_url(proxy.url)})


async def _find(db: Db, proxy_id: int) -> Proxy:
    proxy = await store.get_proxy(db, proxy_id)
    if proxy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proxy not found")
    return proxy


async def _save(db: Db, proxy: Proxy, body: ProxyCreate | ProxyUpdate) -> ProxyOut:
    try:
        return _out(await store.save_proxy(db, proxy, body))
    except store.DuplicateProxyError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


# Before the /{proxy_id} routes, so "settings" isn't read as an id.
@router.get("/settings")
async def get_proxy_settings(db: Db) -> ProxySettings:
    return await store.get_proxy_settings(db)


@router.put("/settings")
async def update_proxy_settings(body: ProxySettings, db: Db) -> ProxySettings:
    await store.set_proxy_settings(db, body)
    return body


@router.get("")
async def list_proxies(db: Db) -> list[ProxyOut]:
    return [_out(proxy) for proxy in await store.list_proxies(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_proxy(body: ProxyCreate, db: Db) -> ProxyOut:
    return await _save(db, Proxy(), body)


@router.put("/{proxy_id}")
async def update_proxy(proxy_id: int, body: ProxyUpdate, db: Db) -> ProxyOut:
    return await _save(db, await _find(db, proxy_id), body)


@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proxy(proxy_id: int, db: Db) -> None:
    """Jobs that ran through it keep its id; running ones keep using it until they end."""
    await store.delete_proxy(db, await _find(db, proxy_id))


@router.post("/{proxy_id}/check")
async def check(proxy_id: int, state: State, db: Db) -> ProxyOut:
    """Opens a page through the proxy: does it work, and which IP do sites see."""
    proxy = await _find(db, proxy_id)
    return _out(await check_proxy(db, state.settings.proxy_check_command, proxy))

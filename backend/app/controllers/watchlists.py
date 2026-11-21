from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_current_user, get_watchlist_service
from app.schemas.watchlists import Watchlist, WatchlistCreate, WatchlistItem, WatchlistItemCreate
from app.services.watchlists import WatchlistService

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("", response_model=list[Watchlist])
async def list_watchlists(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> list[Watchlist]:
    return await service.list(user_id, limit, offset)


@router.post("", response_model=Watchlist, status_code=201)
async def create_watchlist(
    payload: WatchlistCreate,
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> Watchlist:
    return await service.create(user_id, payload)


@router.get("/{watchlist_id}", response_model=Watchlist)
async def get_watchlist(
    watchlist_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> Watchlist:
    return await service.get(user_id, watchlist_id)


@router.delete("/{watchlist_id}", status_code=204)
async def delete_watchlist(
    watchlist_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> Response:
    await service.delete(user_id, watchlist_id)
    return Response(status_code=204)


@router.post("/{watchlist_id}/items", response_model=WatchlistItem, status_code=201)
async def add_watchlist_item(
    watchlist_id: UUID,
    payload: WatchlistItemCreate,
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistItem:
    return await service.add(user_id, watchlist_id, payload)


@router.delete("/{watchlist_id}/items/{item_id}", status_code=204)
async def remove_watchlist_item(
    watchlist_id: UUID,
    item_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> Response:
    await service.remove(user_id, watchlist_id, item_id)
    return Response(status_code=204)

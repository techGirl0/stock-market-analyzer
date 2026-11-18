from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.dependencies import get_current_user, get_watchlist_service
from app.schemas.watchlists import Watchlist, WatchlistCreate, WatchlistItem, WatchlistItemCreate
from app.services.watchlists import WatchlistService

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("", response_model=list[Watchlist])
def list_watchlists(
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> list[Watchlist]:
    return service.list(user_id)


@router.post("", response_model=Watchlist, status_code=201)
def create_watchlist(
    payload: WatchlistCreate,
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> Watchlist:
    return service.create(user_id, payload.name)


@router.post("/{watchlist_id}/items", response_model=WatchlistItem, status_code=201)
def add_watchlist_item(
    watchlist_id: UUID,
    payload: WatchlistItemCreate,
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistItem:
    return service.add(user_id, watchlist_id, payload.symbol)


@router.delete("/{watchlist_id}/items/{item_id}", status_code=204)
def remove_watchlist_item(
    watchlist_id: UUID,
    item_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> Response:
    service.remove(user_id, watchlist_id, item_id)
    return Response(status_code=204)

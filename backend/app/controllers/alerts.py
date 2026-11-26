from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import get_alert_service, get_current_user
from app.schemas.alerts import Alert, AlertCreate, DeliveryRead
from app.services.alerts import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[Alert])
async def list_alerts(
    user_id: UUID = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return await service.list(user_id)


@router.post("", response_model=Alert, status_code=201)
async def create_alert(
    payload: AlertCreate,
    user_id: UUID = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return await service.create(user_id, payload.symbol, payload.operator, payload.threshold)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    await service.delete(user_id, alert_id)


@router.get("/notifications", response_model=list[DeliveryRead])
async def list_notifications(
    user_id: UUID = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return await service.notifications(user_id)


@router.post("/notifications/{delivery_id}/read", response_model=DeliveryRead)
async def mark_notification_read(
    delivery_id: UUID,
    user_id: UUID = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    return await service.mark_read(user_id, delivery_id)

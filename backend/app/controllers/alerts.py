from uuid import UUID
from fastapi import APIRouter, Depends, Response
from app.dependencies import get_current_user, get_alert_service
from app.schemas.alerts import Alert, AlertCreate
from app.services.alerts import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=list[Alert])
def list_alerts(user_id: UUID = Depends(get_current_user), service: AlertService = Depends(get_alert_service)):
    return service.list(user_id)

@router.post("", response_model=Alert, status_code=201)
async def create_alert(payload: AlertCreate, user_id: UUID = Depends(get_current_user), service: AlertService = Depends(get_alert_service)):
    return await service.create(user_id, payload.symbol, payload.operator, payload.threshold)

@router.delete("/{alert_id}", status_code=204)
def delete_alert(alert_id: UUID, user_id: UUID = Depends(get_current_user), service: AlertService = Depends(get_alert_service)):
    service.delete(user_id, alert_id)
    return Response(status_code=204)

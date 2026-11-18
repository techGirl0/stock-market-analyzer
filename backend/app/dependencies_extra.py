from app.dependencies import get_database, get_market_connector
from app.services.portfolio import PortfolioService
from app.services.alerts import AlertService

def get_portfolio_service():
    return PortfolioService(get_database(), get_market_connector())

def get_alert_service():
    return AlertService(get_database(), get_market_connector())

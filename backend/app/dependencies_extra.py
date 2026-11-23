from app.dependencies import get_database, get_market_connector
from app.dependencies_analysis import get_llm_connector
from app.services.portfolio import PortfolioService
from app.services.alerts import AlertService
from app.services.news import NewsService


def get_portfolio_service():
    return PortfolioService(get_database(), get_market_connector())


def get_alert_service():
    return AlertService(get_database(), get_market_connector())


def get_news_service() -> NewsService:
    return NewsService(get_market_connector(), get_llm_connector())

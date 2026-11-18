from app.dependencies import get_market_connector
from app.services.analysis import AnalysisService

def get_analysis_service() -> AnalysisService:
    return AnalysisService(get_market_connector())

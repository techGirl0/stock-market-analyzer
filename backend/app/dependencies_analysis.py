from app.dependencies import get_market_connector
from app.services.analysis import AnalysisService
from app.connectors.llm import DisabledLLMConnector, GroqLLMConnector
from app.core.config import get_settings
from app.core.errors import BackendError


def get_llm_connector():
    settings = get_settings()
    if settings.llm_provider.lower() == "groq":
        if not settings.groq_api_key:
            raise BackendError("llm_unavailable", "GROQ_API_KEY is not configured.", 503)
        return GroqLLMConnector(settings.groq_api_key, settings.groq_model)
    return DisabledLLMConnector()


def get_analysis_service() -> AnalysisService:
    return AnalysisService(get_market_connector(), get_llm_connector())

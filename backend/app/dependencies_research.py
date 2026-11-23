from app.connectors.llm import DisabledLLMConnector, GroqLLMConnector, LLMConnector
from app.core.config import get_settings
from app.core.errors import BackendError
from app.dependencies import get_market_connector
from app.services.research import ResearchService


def get_research_service() -> ResearchService:
    settings = get_settings()
    connector: LLMConnector
    if settings.llm_provider.lower() == "groq":
        if not settings.groq_api_key:
            raise BackendError("llm_unavailable", "GROQ_API_KEY is not configured.", 503)
        connector = GroqLLMConnector(settings.groq_api_key, settings.groq_model)
    else:
        connector = DisabledLLMConnector()
    return ResearchService(get_market_connector(), connector)

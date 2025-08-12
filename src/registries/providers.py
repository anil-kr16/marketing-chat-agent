from __future__ import annotations

from typing import Dict, Any

from src.providers.llm.openai_provider import OpenAIProvider
# from src.providers.llm.gemini_provider import GeminiProvider  # future
from src.providers.email.smtp_provider import SMTPProvider
# from src.providers.email.ses_provider import SESProvider  # future


PROVIDERS: Dict[str, Any] = {
    "openai": OpenAIProvider(),
    "smtp": SMTPProvider(),
}


from __future__ import annotations

from typing import Dict, Type

from src.agents.micro.text_only_agent import TextOnlyAgent
from src.agents.micro.image_only_agent import ImageOnlyAgent
from src.agents.micro.hashtag_only_agent import HashtagOnlyAgent
from src.agents.campaign.full_marketing_agent import FullMarketingAgent
from src.agents.core.base_agent import BaseAgent


AGENTS: Dict[str, Type[BaseAgent]] = {
    "FullMarketingAgent": FullMarketingAgent,
    "TextOnlyAgent": TextOnlyAgent,
    "ImageOnlyAgent": ImageOnlyAgent,
    "HashtagOnlyAgent": HashtagOnlyAgent,
}


from __future__ import annotations

from typing import Callable, Dict

from src.nodes.intent.parse_intent_node import parse_intent_node
from src.nodes.intent.creative_generation_node import creative_generation_node
from src.nodes.generation.text.text_generation_node import text_generation_node
from src.nodes.generation.image.image_generation_node import image_generation_node
from src.nodes.generation.cta_hashtag.cta_hashtag_node import cta_hashtag_node
from src.nodes.compose.response_generator_node import response_generator_node
from src.nodes.delivery.decider.sender_node import sender_node
from src.nodes.delivery.email.send_email_node import send_email_node


NodeCallable = Callable[..., dict]

NODES: Dict[str, NodeCallable] = {
    "ParseIntentNode": parse_intent_node,
    "CreativeGenerationNode": creative_generation_node,
    "TextGenerationNode": text_generation_node,
    "ImageGenerationNode": image_generation_node,
    "CTAHashtagNode": cta_hashtag_node,
    "ResponseGeneratorNode": response_generator_node,
    "SenderNode": sender_node,
    "SendEmailNode": send_email_node,
}


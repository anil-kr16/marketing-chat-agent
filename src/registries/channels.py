from __future__ import annotations

from typing import Callable, Dict

from src.nodes.delivery.email.send_email_node import send_email_node
from src.nodes.delivery.instagram.send_instagram_node import send_instagram_node
from src.nodes.delivery.facebook.send_facebook_node import send_facebook_node


ChannelCallable = Callable[..., dict]

CHANNELS: Dict[str, ChannelCallable] = {
    "email": send_email_node,
    "instagram": send_instagram_node,
    "facebook": send_facebook_node,
    # "twitter": send_twitter_node,      # TODO: implement
    # "linkedin": send_linkedin_node,    # TODO: implement
}


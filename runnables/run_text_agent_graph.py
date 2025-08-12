from __future__ import annotations

"""Run the Text Agent graph end-to-end from the CLI.

Usage:
  python -m runnables.run_text_agent_graph "<your brief>"
"""

import sys
from typing import List

from langchain.schema import HumanMessage
from src.agents.text_agent.utils.ui import (
    print_banner,
    format_message,
    print_summary_header,
    print_kv,
)

from src.utils.state import MessagesState
from src.graphs.campaign.text_campaign_graph import get_full_marketing_graph


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Please provide a campaign brief as a single argument.")
        return 1

    brief = argv[1]
    print_banner("🧩 Text Agent Graph Runner")
    format_message("user", brief)
    graph = get_full_marketing_graph()

    state: MessagesState = {"messages": [HumanMessage(content=brief)]}
    result = graph.invoke(state)

    print_summary_header()
    if result.get("final_response"):
        format_message("agent", "Approved: yes (final_response present)")
        email = result["final_response"].get("email", {})
        print_kv("Email subject", email.get("subject", "<none>"))
    else:
        format_message("agent", "Approved: no")
        review = result.get("meta", {}).get("text_review", {})
        print_kv("Reviewer comments", review.get("comments", "<none>"))

    delivery = result.get("delivery", {})
    if delivery.get("results", {}).get("email"):
        print_kv("Email delivery", delivery["results"]["email"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


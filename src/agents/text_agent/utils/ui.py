"""
Lightweight UI helpers for the Text Agent runnables.

We intentionally mirror the UX style of run.py without importing from it.
"""

from __future__ import annotations

import time


def print_colored(text: str, color_code: str) -> None:
    print(f"\033[{color_code}m{text}\033[0m")


def print_typing_effect(text: str, delay: float = 0.02) -> None:
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def print_banner(title: str = "📝 Text Agent Runner") -> None:
    print("\n" + "=" * 64)
    print_colored(title, "36")
    print_colored("Type Ctrl+C to exit", "33")
    print("=" * 64 + "\n")


def format_message(role: str, message: str, typing: bool = False) -> None:
    if role == "user":
        print("\n" + "─" * 64)
        print_colored("👤 You", "32")
        print("" + "─" * 64)
    else:
        print("\n" + "─" * 64)
        print_colored("🤖 Agent", "36")
        print("" + "─" * 64)
    if typing:
        print_typing_effect(message)
    else:
        print(message)
    print()


def print_summary_header() -> None:
    print("\n" + "=" * 64)
    print_colored("📄 Summary", "35")
    print("=" * 64)


def print_kv(label: str, value: str) -> None:
    print_colored(f"{label}:", "90")
    print(value)


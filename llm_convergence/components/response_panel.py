import reflex as rx
from typing import Dict, Any
from datetime import datetime, timezone


def response_panel_from_dict(response_dict: Dict[str, Any], is_critique: bool = False) -> rx.Component:
    """
    Display a single LLM response or critique from dictionary.

    Args:
        response_dict: The response dictionary to display
        is_critique: Whether this is a critique (affects styling)
    """
    if not response_dict:
        return rx.fragment()

    # Extract values from dict
    provider = response_dict.get("provider", "anthropic")
    content = response_dict.get("content", "")
    timestamp_str = response_dict.get("timestamp", datetime.now(timezone.utc).isoformat())
    declares_convergence = response_dict.get("declares_convergence", False)

    # Determine provider display
    provider_name = "Claude" if provider == "anthropic" else "GPT"
    provider_color = "blue" if provider == "anthropic" else "green"
    panel_type = "Critique" if is_critique else "Response"

    # Format timestamp
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        time_display = timestamp.strftime("%H:%M:%S")
    except (ValueError, AttributeError):
        time_display = "N/A"

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    provider_name,
                    color=provider_color,
                    size="2",
                ),
                rx.badge(
                    panel_type,
                    color="gray",
                    variant="soft",
                    size="2",
                ),
                rx.cond(
                    declares_convergence,
                    rx.badge(
                        "Convergence Declared",
                        color="orange",
                        size="2",
                    ),
                ),
                rx.spacer(),
                rx.text(
                    time_display,
                    size="1",
                    color="gray",
                ),
                width="100%",
                align="center",
            ),
            rx.divider(),
            rx.markdown(
                content,
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )

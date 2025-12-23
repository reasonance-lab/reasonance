import reflex as rx
from typing import Dict
from ..state import AppState


def provider_badge(provider: str, small: bool = False) -> rx.Component:
    """Create a styled badge for the provider."""
    padding = "0.1rem 0.35rem" if small else "0.15rem 0.4rem"
    if provider == "claude":
        return rx.box(
            rx.text("Claude", size="1", weight="bold"),
            background="linear-gradient(135deg, #d97706 0%, #b45309 100%)",
            padding=padding,
            border_radius="4px",
            color="white",
        )
    else:
        return rx.box(
            rx.text("GPT", size="1", weight="bold"),
            background="linear-gradient(135deg, #10a37f 0%, #1a7f5c 100%)",
            padding=padding,
            border_radius="4px",
            color="white",
        )


def response_box(content: rx.Var[str], is_critique: bool = False) -> rx.Component:
    """Adaptive scrollable response box with markdown rendering.

    Uses max-height to allow content to determine natural height,
    while still constraining very long responses with scroll.
    """
    # Max heights - content will expand up to this, then scroll
    max_height = "clamp(200px, 50vh, 600px)" if not is_critique else "clamp(150px, 40vh, 450px)"
    min_height = "80px" if not is_critique else "60px"

    return rx.scroll_area(
        rx.markdown(
            content,
            style={
                "font_size": "13px",
                "line_height": "1.5",
                "& h1": {"font_size": "1.1rem", "margin": "0.4rem 0 0.2rem 0", "font_weight": "600"},
                "& h2": {"font_size": "1rem", "margin": "0.35rem 0 0.15rem 0", "font_weight": "600"},
                "& h3": {"font_size": "0.9rem", "margin": "0.3rem 0 0.1rem 0", "font_weight": "600"},
                "& h4, & h5, & h6": {"font_size": "0.85rem", "margin": "0.25rem 0 0.1rem 0", "font_weight": "500"},
                "& p": {"margin_bottom": "0.4rem"},
                "& ul, & ol": {"padding_left": "1.25rem", "margin_bottom": "0.4rem"},
                "& li": {"margin_bottom": "0.15rem"},
                "& table": {"font_size": "12px", "width": "100%"},
                "& code": {"font_size": "12px", "padding": "0.1rem 0.3rem", "background": "var(--gray-a3)", "border_radius": "4px"},
                "& pre": {"padding": "0.5rem", "background": "var(--gray-a3)", "border_radius": "6px", "overflow_x": "auto", "margin": "0.3rem 0"},
            },
        ),
        type="auto",
        scrollbars="vertical",
        style={
            "min_height": min_height,
            "max_height": max_height,
            "height": "auto",  # Let content determine natural height
            "padding": "0.5rem",
            "background": "var(--gray-a2)" if not is_critique else "var(--gray-a3)",
            "border_radius": "8px",
            "border": "1px solid var(--gray-a4)",
        },
    )


def peer_review_round_content(round_data: Dict[str, str]) -> rx.Component:
    """Display content for a single peer review round - author/reviewer layout."""
    is_first_round = round_data["round_number"] == "1"

    return rx.vstack(
        # Claude's Response/Revision (Author)
        rx.box(
            rx.vstack(
                rx.hstack(
                    provider_badge("claude", small=True),
                    rx.cond(
                        round_data["round_number"] == "1",
                        rx.text("Response", size="1", color="gray"),
                        rx.text("Revision", size="1", color="gray"),
                    ),
                    spacing="1",
                    align="center",
                ),
                rx.cond(
                    round_data["claude_response"] != "",
                    response_box(round_data["claude_response"]),
                    rx.hstack(
                        rx.spinner(size="1"),
                        rx.text("Generating...", size="1", color="gray"),
                        spacing="1",
                        padding="1rem",
                    ),
                ),
                spacing="1",
                width="100%",
            ),
            width="100%",
        ),

        # Manual review input (shown when Auto is OFF and waiting for user)
        rx.cond(
            AppState.show_manual_review_input,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("message-square-plus", size=14, color="var(--accent-9)"),
                        rx.text("Additional context for review", size="1", weight="medium", color="gray"),
                        rx.text("(optional)", size="1", color="gray", style={"opacity": "0.6"}),
                        spacing="1",
                        align="center",
                    ),
                    rx.text_area(
                        value=AppState.review_additional_prompt,
                        on_change=AppState.set_review_additional_prompt,
                        placeholder="Add specific instructions or focus areas for the reviewer...",
                        rows="2",
                        width="100%",
                        style={
                            "border_radius": "8px",
                            "font_size": "13px",
                        },
                    ),
                    rx.hstack(
                        rx.button(
                            rx.hstack(
                                rx.icon("send", size=14),
                                rx.text("Review now"),
                                spacing="1",
                            ),
                            on_click=AppState.trigger_manual_review,
                            size="2",
                        ),
                        rx.text(
                            "GPT will review Claude's response with your additional context",
                            size="1",
                            color="gray",
                            style={"opacity": "0.7"},
                        ),
                        spacing="2",
                        align="center",
                    ),
                    spacing="2",
                    width="100%",
                ),
                padding="0.75rem",
                background="var(--accent-a2)",
                border_radius="8px",
                border="1px solid var(--accent-a4)",
                margin_top="0.5rem",
                width="100%",
            ),
        ),

        # GPT's Review (Reviewer)
        rx.box(
            rx.vstack(
                rx.hstack(
                    provider_badge("gpt", small=True),
                    rx.cond(
                        round_data["round_number"] == "1",
                        rx.text("Review", size="1", color="gray"),
                        rx.text("Re-review", size="1", color="gray"),
                    ),
                    rx.icon("clipboard-check", size=12, color="var(--accent-9)"),
                    spacing="1",
                    align="center",
                ),
                rx.cond(
                    round_data["openai_critique"] != "",
                    response_box(round_data["openai_critique"], True),
                    rx.cond(
                        AppState.show_manual_review_input,
                        # Show waiting message when in manual mode
                        rx.text("Waiting for review trigger...", size="1", color="gray", padding="1rem"),
                        rx.cond(
                            round_data["claude_response"] != "",
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Reviewing...", size="1", color="gray"),
                                spacing="1",
                                padding="1rem",
                            ),
                            rx.text("Waiting for response...", size="1", color="gray", padding="1rem"),
                        ),
                    ),
                ),
                spacing="1",
                width="100%",
            ),
            width="100%",
            margin_top="0.5rem",
        ),

        spacing="2",
        width="100%",
    )


def convergence_round_content(round_data: Dict[str, str]) -> rx.Component:
    """Display content for a single convergence round - compact 2x2 grid layout."""
    return rx.vstack(
        # Responses row - responsive with flex-wrap
        rx.hstack(
            # Claude Response
            rx.box(
                rx.vstack(
                    rx.hstack(
                        provider_badge("claude", small=True),
                        rx.text("Response", size="1", color="gray"),
                        spacing="1",
                        align="center",
                    ),
                    rx.cond(
                        round_data["claude_response"] != "",
                        response_box(round_data["claude_response"]),
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Generating...", size="1", color="gray"),
                            spacing="1",
                            padding="1rem",
                        ),
                    ),
                    spacing="1",
                    width="100%",
                ),
                flex="1",
                min_width="300px",
            ),
            # GPT Response
            rx.box(
                rx.vstack(
                    rx.hstack(
                        provider_badge("gpt", small=True),
                        rx.text("Response", size="1", color="gray"),
                        spacing="1",
                        align="center",
                    ),
                    rx.cond(
                        round_data["openai_response"] != "",
                        response_box(round_data["openai_response"]),
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Generating...", size="1", color="gray"),
                            spacing="1",
                            padding="1rem",
                        ),
                    ),
                    spacing="1",
                    width="100%",
                ),
                flex="1",
                min_width="300px",
            ),
            spacing="3",
            width="100%",
            align="start",
            flex_wrap="wrap",
        ),

        # Critiques row (only for rounds > 1)
        rx.cond(
            round_data["round_number"] != "1",
            rx.vstack(
                rx.hstack(
                    rx.icon("message-square-more", size=12, color="var(--accent-9)"),
                    rx.text("Critiques", size="1", weight="medium", color="gray"),
                    spacing="1",
                    align="center",
                ),
                rx.hstack(
                    # Claude critiques GPT
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                provider_badge("claude", small=True),
                                rx.icon("arrow-right", size=10, color="gray"),
                                provider_badge("gpt", small=True),
                                spacing="1",
                                align="center",
                            ),
                            rx.cond(
                                round_data["claude_critique"] != "",
                                response_box(round_data["claude_critique"], True),
                                rx.text("—", size="1", color="gray"),
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        flex="1",
                        min_width="300px",
                    ),
                    # GPT critiques Claude
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                provider_badge("gpt", small=True),
                                rx.icon("arrow-right", size=10, color="gray"),
                                provider_badge("claude", small=True),
                                spacing="1",
                                align="center",
                            ),
                            rx.cond(
                                round_data["openai_critique"] != "",
                                response_box(round_data["openai_critique"], True),
                                rx.text("—", size="1", color="gray"),
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        flex="1",
                        min_width="300px",
                    ),
                    spacing="3",
                    width="100%",
                    align="start",
                    flex_wrap="wrap",
                ),
                spacing="1",
                width="100%",
                margin_top="0.5rem",
            ),
        ),

        spacing="2",
        width="100%",
    )


def round_tab(round_data: Dict[str, str]) -> rx.Component:
    """Individual round tab trigger with key for React reconciliation."""
    round_num = round_data["round_number"]
    return rx.tabs.trigger(
        rx.hstack(
            rx.text(f"R{round_num}", size="1", weight="medium"),
            spacing="1",
            align="center",
        ),
        value=round_num,
        key=round_num,
        style={
            "padding": "0.25rem 0.5rem",
            "border_radius": "4px",
            "cursor": "pointer",
        },
    )


def round_tab_content(round_data: Dict[str, str]) -> rx.Component:
    """Individual round tab content with key for React reconciliation."""
    return rx.tabs.content(
        rx.cond(
            AppState.conversation_is_peer_review,
            peer_review_round_content(round_data),
            convergence_round_content(round_data),
        ),
        value=round_data["round_number"],
        key=round_data["round_number"],
        padding_top="0.5rem",
    )


def conversation_display_from_state(conversation_data: rx.Var[Dict]) -> rx.Component:
    """Display conversation with tabbed rounds for maximum visibility."""
    return rx.cond(
        AppState.has_conversation,
        rx.vstack(
            # Compact prompt display
            rx.hstack(
                rx.hstack(
                    rx.icon("user", size=12, color="var(--accent-9)"),
                    rx.text("Prompt:", size="1", weight="medium", color="gray"),
                    spacing="1",
                    align="center",
                ),
                rx.scroll_area(
                    rx.text(
                        AppState.user_prompt_display,
                        size="2",
                        line_height="1.4",
                    ),
                    type="auto",
                    scrollbars="vertical",
                    style={"max_height": "60px"},
                ),
                spacing="2",
                width="100%",
                align="start",
                padding="0.5rem 0.75rem",
                background="var(--accent-a2)",
                border_radius="8px",
                border="1px solid var(--accent-a3)",
            ),

            # Tabbed rounds display
            rx.tabs.root(
                rx.hstack(
                    rx.tabs.list(
                        rx.foreach(
                            AppState.rounds_display,
                            round_tab,
                        ),
                        size="1",
                    ),
                    rx.spacer(),
                    # Mode badge - high contrast for dark backgrounds
                    rx.cond(
                        AppState.conversation_is_peer_review,
                        rx.box(
                            rx.text("Peer Review", size="1", weight="medium"),
                            background="linear-gradient(135deg, #a855f7 0%, #7c3aed 100%)",
                            color="white",
                            padding="0.15rem 0.5rem",
                            border_radius="4px",
                        ),
                        rx.box(
                            rx.text("Convergence", size="1", weight="medium"),
                            background="linear-gradient(135deg, #22d3ee 0%, #06b6d4 100%)",
                            color="#0f172a",
                            padding="0.15rem 0.5rem",
                            border_radius="4px",
                        ),
                    ),
                    rx.text(
                        f"{AppState.current_round_number} rounds",
                        size="1",
                        color="gray",
                    ),
                    width="100%",
                    align="center",
                    spacing="2",
                ),
                rx.foreach(
                    AppState.rounds_display,
                    round_tab_content,
                ),
                value=AppState.selected_round,
                on_change=AppState.set_selected_round,
                width="100%",
            ),

            width="100%",
            spacing="2",
            padding="0.75rem",
            background="var(--gray-a1)",
            border_radius="10px",
            border="1px solid var(--gray-a3)",
        ),
        # Empty state - very compact
        rx.hstack(
            rx.icon("message-circle-off", size=20, color="gray", opacity=0.5),
            rx.text("Enter a prompt to begin", color="gray", size="2"),
            spacing="2",
            align="center",
            justify="center",
            padding="2rem",
            width="100%",
        ),
    )

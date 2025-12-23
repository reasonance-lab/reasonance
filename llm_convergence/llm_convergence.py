"""LLM Convergence Dialogue Application."""

import reflex as rx
from .state import AppState
from .components.prompt_input import prompt_input
from .components.round_display import conversation_display_from_state
from .components.controls import controls
from .components.settings_dialog import settings_dialog


def header() -> rx.Component:
    """Compact cozy header - minimal vertical space."""
    return rx.hstack(
        rx.hstack(
            rx.text(rx.icon("sparkles"), font_size="2.5rem"),
            rx.heading(
                "Reasonance",
                size="7",
                weight="bold",
                style={
                    "background": "linear-gradient(135deg, var(--accent-9) 0%, var(--accent-11) 100%)",
                    "-webkit-background-clip": "text",
                    "-webkit-text-fill-color": "transparent",
                    "background-clip": "text",
                },
            ),
            spacing="2",
            align="center",
        ),
        rx.tooltip(
            rx.icon("info", size=14, color="gray", cursor="help"),
            content="Claude and GPT collaborate through critique rounds until convergence",
        ),
        rx.spacer(),
        rx.hstack(
            rx.text("claude-opus-4-5", size="1", color="gray", font_family="monospace"),
            rx.text("•", color="gray", size="1"),
            rx.text(AppState.openai_model, size="1", color="gray", font_family="monospace"),
            spacing="1",
        ),
        rx.link(
            rx.icon("github", size=16, color="gray"),
            href="https://github.com/reasonance-lab/LLMConv",
            is_external=True,
        ),
        width="100%",
        align="center",
        spacing="3",
        padding="0.75rem 0",
        border_bottom="1px solid var(--gray-a3)",
        margin_bottom="0.75rem",
    )


def index() -> rx.Component:
    """Main page layout - compact cozy design with maximum visibility."""
    return rx.box(
        rx.box(
            rx.vstack(
                # Compact header
                header(),

                # Show prompt input when NO conversation
                rx.cond(
                    ~AppState.has_conversation,
                    prompt_input(),
                ),

                # Show controls + conversation when HAS conversation
                rx.cond(
                    AppState.has_conversation,
                    rx.vstack(
                        controls(),
                        conversation_display_from_state(AppState.conversation_data),
                        width="100%",
                        spacing="2",
                    ),
                ),

                width="100%",
                spacing="2",
                padding_y="0.5rem",
            ),
            width="100%",
            padding_x="1.5rem",
        ),
        # Settings dialog (rendered but only visible when open)
        settings_dialog(),
        width="100%",
        min_height="100vh",
        background="var(--gray-1)",
    )


# Create the app with cozy dark theme
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        radius="large",
        accent_color="amber",
        gray_color="slate",
        scaling="100%",
    ),
    stylesheets=[
        # Custom styles for extra coziness
    ],
)

app.add_page(index, title="LLM Convergence Dialogue")

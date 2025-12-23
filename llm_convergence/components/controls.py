import reflex as rx
from ..state import AppState


def controls() -> rx.Component:
    """Compact single-line control bar."""
    return rx.hstack(
        # Status badge
        rx.badge(
            AppState.status_display,
            size="1",
            variant="soft",
            radius="full",
        ),

        # Round counter
        rx.hstack(
            rx.icon("repeat", size=12, color="gray"),
            rx.text(
                f"{AppState.current_round_number}/{AppState.max_rounds}",
                size="1",
                color="gray",
                weight="medium",
            ),
            spacing="1",
            align="center",
        ),

        rx.divider(orientation="vertical", size="1"),

        # Continue button
        rx.button(
            rx.cond(
                AppState.is_loading,
                rx.hstack(
                    rx.spinner(size="1"),
                    rx.text("Loading...", size="1"),
                    spacing="1",
                ),
                rx.hstack(
                    rx.icon("arrow-right", size=14),
                    rx.text("Continue"),
                    spacing="1",
                ),
            ),
            on_click=AppState.continue_conversation,
            disabled=AppState.is_loading | ~AppState.can_continue,
            loading=AppState.is_loading,
            size="1",
            style={"border_radius": "6px"},
        ),

        # Auto-convergence toggle
        rx.hstack(
            rx.switch(
                checked=AppState.auto_convergence,
                on_change=AppState.toggle_auto_convergence,
                size="1",
            ),
            rx.text("Auto", size="1", color="gray"),
            spacing="1",
            align="center",
        ),

        rx.spacer(),

        # Loading status indicator - prominent badge
        rx.cond(
            AppState.is_loading,
            rx.badge(
                rx.hstack(
                    rx.spinner(size="1"),
                    rx.text(AppState.loading_status, size="1"),
                    spacing="1",
                    align="center",
                ),
                color="amber",
                size="2",
                variant="soft",
            ),
        ),

        # Status message (compact) - show when not loading
        rx.cond(
            ~AppState.is_loading & ~AppState.can_continue & AppState.has_conversation,
            rx.hstack(
                rx.icon(
                    rx.cond(
                        AppState.current_round_number >= AppState.max_rounds,
                        "flag",
                        "check-circle",
                    ),
                    size=12,
                    color="green",
                ),
                rx.text(
                    rx.cond(
                        AppState.current_round_number >= AppState.max_rounds,
                        "Max rounds reached",
                        "Converged",
                    ),
                    size="1",
                    color="green",
                ),
                spacing="1",
                align="center",
            ),
        ),

        # Reset button
        rx.button(
            rx.icon("refresh-cw", size=12),
            rx.text("Reset"),
            on_click=AppState.reset_conversation,
            variant="ghost",
            color="red",
            size="1",
        ),

        rx.divider(orientation="vertical", size="1"),

        # Export conversation button (only show when there's a conversation)
        rx.cond(
            AppState.has_conversation,
            rx.button(
                rx.icon("download", size=12),
                rx.text("Export"),
                on_click=AppState.download_conversation,
                variant="ghost",
                size="1",
            ),
        ),

        # Settings button
        rx.button(
            rx.icon("settings", size=12),
            rx.text("Prompts"),
            on_click=AppState.open_settings_dialog,
            variant="ghost",
            size="1",
        ),

        width="100%",
        align="center",
        spacing="3",
        padding="0.5rem 0.75rem",
        background="var(--gray-a1)",
        border_radius="10px",
        border="1px solid var(--gray-a3)",
    )

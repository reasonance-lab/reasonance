import reflex as rx
from ..state import AppState


def prompt_input() -> rx.Component:
    """Compact layout with visible model settings."""
    return rx.vstack(
        # Top row: Prompt + Start button
        rx.hstack(
            # Prompt input
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("message-square", size=14, color="var(--accent-9)"),
                        rx.text("Prompt", weight="medium", size="2"),
                        spacing="1",
                        align="center",
                    ),
                    rx.text_area(
                        value=AppState.user_prompt,
                        on_change=AppState.set_prompt,
                        placeholder="What should Claude and GPT discuss?",
                        rows="3",
                        width="100%",
                        disabled=AppState.is_loading,
                        style={
                            "border_radius": "8px",
                            "padding": "0.75rem",
                            "font_size": "14px",
                            "line_height": "1.5",
                            "resize": "vertical",
                        },
                    ),
                    # Example prompts
                    rx.hstack(
                        rx.text("Examples:", size="1", color="gray"),
                        rx.button(
                            "Architecture",
                            on_click=AppState.set_prompt("What are the key benefits of modular architecture in software design?"),
                            variant="ghost",
                            size="1",
                            cursor="pointer",
                        ),
                        rx.button(
                            "Async vs Parallel",
                            on_click=AppState.set_prompt("Explain the difference between asynchronous and parallel programming"),
                            variant="ghost",
                            size="1",
                            cursor="pointer",
                        ),
                        rx.button(
                            "AI Ethics",
                            on_click=AppState.set_prompt("What are the ethical implications of AI in healthcare?"),
                            variant="ghost",
                            size="1",
                            cursor="pointer",
                        ),
                        wrap="wrap",
                        spacing="1",
                        align="center",
                    ),
                    spacing="2",
                    width="100%",
                ),
                flex="1",
                padding="0.75rem",
                background="var(--gray-a1)",
                border_radius="12px",
                border="1px solid var(--gray-a3)",
            ),

            # Start button with loading status
            rx.button(
                rx.cond(
                    AppState.is_loading,
                    rx.vstack(
                        rx.spinner(size="2"),
                        rx.text(AppState.loading_status, size="1"),
                        spacing="1",
                        align="center",
                    ),
                    rx.vstack(
                        rx.icon("play", size=24),
                        rx.text("Start", size="2", weight="bold"),
                        spacing="1",
                        align="center",
                    ),
                ),
                on_click=AppState.start_conversation,
                disabled=AppState.is_loading | ~AppState.can_start_conversation,
                loading=AppState.is_loading,
                size="3",
                style={
                    "border_radius": "12px",
                    "padding": "1.5rem 2rem",
                    "min_height": "100px",
                },
            ),

            spacing="3",
            width="100%",
            align="stretch",
        ),

        # Bottom row: Mode selector and Model settings
        rx.box(
            rx.hstack(
                # Mode selector
                rx.hstack(
                    rx.icon("git-branch", size=16, color="var(--accent-9)"),
                    rx.text("Mode", weight="medium", size="2"),
                    rx.segmented_control.root(
                        rx.segmented_control.item("Convergence", value="convergence"),
                        rx.segmented_control.item("Peer Review", value="peer_review"),
                        default_value="convergence",
                        value=AppState.conversation_mode,
                        on_change=lambda val: AppState.set_conversation_mode(val),
                        size="1",
                    ),
                    spacing="2",
                    align="center",
                ),

                # Auto toggle - controls automatic review/critique flow
                rx.hstack(
                    rx.switch(
                        checked=AppState.auto_convergence,
                        on_change=AppState.toggle_auto_convergence,
                        size="1",
                    ),
                    rx.text("Auto", size="1", color="gray"),
                    rx.tooltip(
                        rx.icon("info", size=12, color="gray", cursor="help"),
                        content="When OFF, you can add context before each review step",
                    ),
                    spacing="1",
                    align="center",
                ),

                rx.divider(orientation="vertical", size="1"),

                rx.hstack(
                    rx.icon("settings-2", size=16, color="var(--accent-9)"),
                    rx.text("Models", weight="medium", size="2"),
                    spacing="2",
                    align="center",
                ),

                rx.divider(orientation="vertical", size="1"),

                # GPT Settings
                rx.hstack(
                    rx.box(
                        rx.text("GPT", size="1", weight="bold"),
                        background="linear-gradient(135deg, #10a37f 0%, #1a7f5c 100%)",
                        padding="0.2rem 0.5rem",
                        border_radius="4px",
                        color="white",
                    ),
                    rx.select(
                        ["gpt-5.2", "gpt-5.2-pro"],
                        value=AppState.openai_model,
                        on_change=AppState.set_openai_model,
                        size="2",
                    ),
                    rx.cond(
                        AppState.show_effort_selector,
                        rx.hstack(
                            rx.text("Effort:", size="2", color="gray"),
                            rx.select(
                                ["high", "xhigh"],
                                value=AppState.openai_effort,
                                on_change=AppState.set_openai_effort,
                                size="2",
                            ),
                            spacing="2",
                            align="center",
                        ),
                    ),
                    rx.cond(
                        AppState.show_pro_confirmation,
                        rx.hstack(
                            rx.icon("triangle-alert", size=14, color="amber"),
                            rx.checkbox(
                                checked=AppState.gpt_pro_confirmed,
                                on_change=AppState.toggle_gpt_pro_confirmation,
                                size="2",
                            ),
                            rx.text("Confirm", size="1", color="amber"),
                            spacing="1",
                            align="center",
                        ),
                    ),
                    spacing="2",
                    align="center",
                ),

                rx.divider(orientation="vertical", size="1"),

                # Claude Settings
                rx.hstack(
                    rx.box(
                        rx.text("Claude", size="1", weight="bold"),
                        background="linear-gradient(135deg, #d97706 0%, #b45309 100%)",
                        padding="0.2rem 0.5rem",
                        border_radius="4px",
                        color="white",
                    ),
                    rx.text("opus-4-5", size="2", font_family="monospace", color="gray"),
                    rx.hstack(
                        rx.text("Thinking:", size="2", color="gray"),
                        rx.switch(
                            checked=AppState.anthropic_thinking_enabled,
                            on_change=AppState.toggle_anthropic_thinking,
                            size="2",
                        ),
                        rx.cond(
                            AppState.anthropic_thinking_enabled,
                            rx.badge("16k tokens", size="1", variant="soft"),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    spacing="2",
                    align="center",
                ),

                rx.divider(orientation="vertical", size="1"),

                # Settings button
                rx.button(
                    rx.icon("settings", size=14),
                    rx.text("Prompts", size="1"),
                    on_click=AppState.open_settings_dialog,
                    variant="ghost",
                    size="1",
                ),

                spacing="4",
                align="center",
                width="100%",
                flex_wrap="wrap",
            ),
            padding="0.75rem 1rem",
            background="var(--gray-a2)",
            border_radius="10px",
            border="1px solid var(--gray-a3)",
            width="100%",
        ),

        # Error message
        rx.cond(
            AppState.error_message != "",
            rx.callout(
                AppState.error_message,
                icon="triangle-alert",
                color="red",
                size="1",
            ),
        ),

        spacing="3",
        width="100%",
    )

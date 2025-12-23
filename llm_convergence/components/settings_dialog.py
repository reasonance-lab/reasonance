import reflex as rx
from ..state import AppState


def api_keys_tab() -> rx.Component:
    """Tab content for API keys configuration."""
    return rx.vstack(
        rx.text(
            "Enter your API keys below. Environment variables (.env) take precedence.",
            size="2",
            color="gray",
        ),
        rx.text_area(
            value=AppState.api_keys_text,
            on_change=AppState.set_api_keys_text,
            rows="2",
            width="100%",
            placeholder="OPENAI_API_KEY=sk-...\nANTHROPIC_API_KEY=sk-ant-...",
            style={
                "font_size": "13px",
                "font_family": "monospace",
                "border_radius": "6px",
            },
        ),
        rx.text(
            "Keys are stored in session memory only and not persisted.",
            size="1",
            color="gray",
        ),
        spacing="2",
        width="100%",
        padding="0.5rem",
    )


def prompt_textarea(
    label: str,
    value: rx.Var[str],
    on_change: callable,
    description: str = ""
) -> rx.Component:
    """Create a labeled textarea for editing a prompt."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(label, size="2", weight="medium"),
                rx.tooltip(
                    rx.icon("info", size=12, color="gray", cursor="help"),
                    content=description,
                ) if description else rx.fragment(),
                spacing="1",
                align="center",
            ),
            rx.text_area(
                value=value,
                on_change=on_change,
                rows="4",
                width="100%",
                style={
                    "font_size": "13px",
                    "font_family": "monospace",
                    "border_radius": "6px",
                },
            ),
            spacing="1",
            width="100%",
        ),
        width="100%",
    )


def convergence_prompts_tab() -> rx.Component:
    """Tab content for convergence mode prompts."""
    return rx.vstack(
        rx.text("Initial Response Prompts", size="3", weight="bold", color="gray"),
        rx.hstack(
            rx.box(
                prompt_textarea(
                    "Claude System Prompt",
                    AppState.conv_claude_system,
                    AppState.set_conv_claude_system,
                    "System prompt for Claude's initial response"
                ),
                flex="1",
            ),
            rx.box(
                prompt_textarea(
                    "GPT System Prompt",
                    AppState.conv_gpt_system,
                    AppState.set_conv_gpt_system,
                    "Developer message for GPT's initial response"
                ),
                flex="1",
            ),
            spacing="3",
            width="100%",
        ),
        rx.divider(),
        rx.text("Critique Prompts", size="3", weight="bold", color="gray"),
        rx.hstack(
            rx.box(
                rx.vstack(
                    prompt_textarea(
                        "Claude Critique System",
                        AppState.conv_claude_critique_system,
                        AppState.set_conv_claude_critique_system,
                        "System prompt for Claude's critique"
                    ),
                    prompt_textarea(
                        "Claude Critique Instruction",
                        AppState.conv_claude_critique_instruction,
                        AppState.set_conv_claude_critique_instruction,
                        "Instruction template for Claude's critique"
                    ),
                    spacing="2",
                    width="100%",
                ),
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    prompt_textarea(
                        "GPT Critique System",
                        AppState.conv_gpt_critique_system,
                        AppState.set_conv_gpt_critique_system,
                        "Developer message for GPT's critique"
                    ),
                    prompt_textarea(
                        "GPT Critique Instruction",
                        AppState.conv_gpt_critique_instruction,
                        AppState.set_conv_gpt_critique_instruction,
                        "Instruction template for GPT's critique"
                    ),
                    spacing="2",
                    width="100%",
                ),
                flex="1",
            ),
            spacing="3",
            width="100%",
        ),
        spacing="3",
        width="100%",
        padding="0.5rem",
    )


def peer_review_prompts_tab() -> rx.Component:
    """Tab content for peer review mode prompts."""
    return rx.vstack(
        rx.text("Claude (Author) Prompts", size="3", weight="bold", color="gray"),
        rx.hstack(
            rx.box(
                prompt_textarea(
                    "Initial Response System",
                    AppState.pr_claude_system,
                    AppState.set_pr_claude_system,
                    "System prompt for Claude's initial response"
                ),
                flex="1",
            ),
            rx.box(
                prompt_textarea(
                    "Revision System",
                    AppState.pr_claude_revision_system,
                    AppState.set_pr_claude_revision_system,
                    "System prompt for Claude's revision"
                ),
                flex="1",
            ),
            spacing="3",
            width="100%",
        ),
        prompt_textarea(
            "Revision Instruction",
            AppState.pr_claude_revision_instruction,
            AppState.set_pr_claude_revision_instruction,
            "Instruction template for Claude's revision"
        ),
        rx.divider(),
        rx.text("GPT (Reviewer) Prompts", size="3", weight="bold", color="gray"),
        rx.hstack(
            rx.box(
                prompt_textarea(
                    "Review System",
                    AppState.pr_gpt_review_system,
                    AppState.set_pr_gpt_review_system,
                    "Developer message for GPT's initial review"
                ),
                flex="1",
            ),
            rx.box(
                prompt_textarea(
                    "Re-review System",
                    AppState.pr_gpt_rereview_system,
                    AppState.set_pr_gpt_rereview_system,
                    "Developer message for GPT's re-review"
                ),
                flex="1",
            ),
            spacing="3",
            width="100%",
        ),
        prompt_textarea(
            "Review Instruction",
            AppState.pr_gpt_review_instruction,
            AppState.set_pr_gpt_review_instruction,
            "Instruction template for GPT's structured review"
        ),
        prompt_textarea(
            "Re-review Instruction",
            AppState.pr_gpt_rereview_instruction,
            AppState.set_pr_gpt_rereview_instruction,
            "Instruction template for GPT's re-review"
        ),
        spacing="3",
        width="100%",
        padding="0.5rem",
    )


def settings_dialog() -> rx.Component:
    """Settings dialog for customizing prompts."""
    return rx.dialog.root(
        rx.dialog.trigger(rx.fragment()),  # Trigger is handled externally
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("settings", size=20, color="var(--accent-9)"),
                    rx.text("Prompt Settings"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.dialog.description(
                rx.text(
                    "Customize the system prompts and instructions used for each mode.",
                    size="2",
                    color="gray",
                ),
            ),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("API Keys", value="api_keys"),
                    rx.tabs.trigger("Convergence", value="convergence"),
                    rx.tabs.trigger("Peer Review", value="peer_review"),
                ),
                rx.tabs.content(
                    api_keys_tab(),
                    value="api_keys",
                ),
                rx.tabs.content(
                    rx.scroll_area(
                        convergence_prompts_tab(),
                        type="auto",
                        scrollbars="vertical",
                        style={"max_height": "50vh"},
                    ),
                    value="convergence",
                ),
                rx.tabs.content(
                    rx.scroll_area(
                        peer_review_prompts_tab(),
                        type="auto",
                        scrollbars="vertical",
                        style={"max_height": "50vh"},
                    ),
                    value="peer_review",
                ),
                default_value="api_keys",
                width="100%",
            ),
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("rotate-ccw", size=14),
                        rx.text("Reset Defaults"),
                        spacing="1",
                    ),
                    on_click=AppState.reset_prompts_to_defaults,
                    variant="outline",
                    color_scheme="gray",
                    size="2",
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon("download", size=14),
                        rx.text("Export Settings"),
                        spacing="1",
                    ),
                    on_click=AppState.download_settings,
                    variant="soft",
                    size="2",
                ),
                rx.dialog.close(
                    rx.button(
                        "Close",
                        size="2",
                    ),
                ),
                width="100%",
                padding_top="1rem",
            ),
            style={
                "max_width": "900px",
                "width": "90vw",
            },
        ),
        open=AppState.settings_dialog_open,
        on_open_change=AppState.set_settings_dialog_open,
    )

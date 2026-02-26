"""Bloomberg-style command input widget."""

from __future__ import annotations

from textual.containers import Container
from textual.message import Message
from textual.widgets import Input


class CommandInput(Container):
    """Bloomberg-style slash command input bar."""

    DEFAULT_CSS = """
    CommandInput {
        dock: bottom;
        height: 3;
        background: #000000;
        padding: 0 1;
    }
    """

    class CommandSubmitted(Message):
        """Emitted when a command is submitted."""

        def __init__(self, command: str) -> None:
            self.command = command
            super().__init__()

    def compose(self):
        yield Input(
            placeholder="/search, /buy, /sell, /positions, /help",
            id="cmd-input",
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if value:
            self.post_message(self.CommandSubmitted(value))
        event.input.clear()

    def focus_input(self) -> None:
        try:
            inp = self.query_one("#cmd-input", Input)
            inp.focus()
        except Exception:
            pass

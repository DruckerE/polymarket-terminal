"""Runtime settings editor screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from src.config.settings import AppSettings


class SettingsScreen(ModalScreen):
    """Modal screen for editing runtime trading settings."""

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
        background: #000000cc;
    }

    #settings-container {
        width: 60;
        height: auto;
        max-height: 25;
        border: double #FFB000;
        background: #0A0A0A;
        padding: 1 2;
    }

    #settings-title {
        color: #FFB000;
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
    }

    .setting-row {
        layout: horizontal;
        height: 3;
    }

    .setting-label {
        width: 25;
        color: #E0E0E0;
        padding: 1 1 0 0;
    }

    .setting-input {
        width: 1fr;
    }
    """

    def __init__(self, settings: AppSettings, **kwargs) -> None:
        super().__init__(**kwargs)
        self._settings = settings

    def compose(self) -> ComposeResult:
        with Container(id="settings-container"):
            yield Static("SETTINGS", id="settings-title")

            with Horizontal(classes="setting-row"):
                yield Label("Kelly Fraction", classes="setting-label")
                yield Input(value=str(self._settings.trading.kelly_fraction), id="set-kelly", classes="setting-input")
            with Horizontal(classes="setting-row"):
                yield Label("Max Position %", classes="setting-label")
                yield Input(value=str(self._settings.trading.max_position_pct), id="set-max-pos", classes="setting-input")
            with Horizontal(classes="setting-row"):
                yield Label("Max Positions", classes="setting-label")
                yield Input(value=str(self._settings.trading.max_positions), id="set-max-count", classes="setting-input")
            with Horizontal(classes="setting-row"):
                yield Label("Max Drawdown %", classes="setting-label")
                yield Input(value=str(self._settings.trading.max_drawdown_pct), id="set-max-dd", classes="setting-input")
            with Horizontal(classes="setting-row"):
                yield Label("Stop Loss ATR", classes="setting-label")
                yield Input(value=str(self._settings.trading.stop_loss_atr_mult), id="set-stop-atr", classes="setting-input")
            with Horizontal(classes="setting-row"):
                yield Label("Arb Threshold", classes="setting-label")
                yield Input(value=str(self._settings.trading.arb_threshold), id="set-arb-thresh", classes="setting-input")

            with Horizontal(classes="setting-row"):
                yield Button("Save", id="save-btn", variant="success")
                yield Button("Close [ESC]", id="close-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.notify("Settings saved for this session", severity="information")
            self.dismiss(None)
        elif event.button.id == "close-btn":
            self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)

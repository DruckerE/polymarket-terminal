"""Manual order entry modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet, Static

from src.models.order import OrderRequest, OrderType
from src.models.position import OutcomeType, Side


class OrderEntryScreen(ModalScreen):
    """Modal for manual order placement."""

    DEFAULT_CSS = """
    OrderEntryScreen {
        align: center middle;
        background: #000000cc;
    }

    #order-container {
        width: 50;
        height: auto;
        max-height: 22;
        border: double #FFB000;
        background: #0A0A0A;
        padding: 1 2;
    }

    #order-title {
        color: #FFB000;
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
    }

    .order-row {
        layout: horizontal;
        height: 3;
    }

    .order-label {
        width: 12;
        color: #E0E0E0;
        padding: 1 1 0 0;
    }
    """

    class OrderPlaced(Message):
        def __init__(self, request: OrderRequest) -> None:
            self.request = request
            super().__init__()

    def __init__(self, market_id: str, token_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._market_id = market_id
        self._token_id = token_id

    def compose(self) -> ComposeResult:
        with Container(id="order-container"):
            yield Static("ORDER ENTRY", id="order-title")

            with Container(classes="order-row"):
                yield Label("Side", classes="order-label")
                with RadioSet(id="side-set"):
                    yield RadioButton("BUY", value=True)
                    yield RadioButton("SELL")

            with Container(classes="order-row"):
                yield Label("Outcome", classes="order-label")
                with RadioSet(id="outcome-set"):
                    yield RadioButton("YES", value=True)
                    yield RadioButton("NO")

            with Container(classes="order-row"):
                yield Label("Price", classes="order-label")
                yield Input(placeholder="0.50", id="price-input")

            with Container(classes="order-row"):
                yield Label("Size", classes="order-label")
                yield Input(placeholder="10", id="size-input")

            with Horizontal():
                yield Button("Place Order", id="place-btn", variant="success")
                yield Button("Cancel", id="cancel-btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "place-btn":
            self._submit_order()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)

    def _submit_order(self) -> None:
        try:
            price_input = self.query_one("#price-input", Input)
            size_input = self.query_one("#size-input", Input)

            price = float(price_input.value)
            size = float(size_input.value)

            if price <= 0 or price >= 1:
                self.notify("Price must be between 0 and 1", severity="error")
                return
            if size <= 0:
                self.notify("Size must be positive", severity="error")
                return

            request = OrderRequest(
                market_id=self._market_id,
                token_id=self._token_id,
                side=Side.BUY,
                outcome=OutcomeType.YES,
                price=price,
                size=size,
                order_type=OrderType.LIMIT,
            )

            self.post_message(self.OrderPlaced(request))
            self.dismiss(request)

        except ValueError:
            self.notify("Invalid price or size", severity="error")

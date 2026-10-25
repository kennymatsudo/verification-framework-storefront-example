"""The storefront web app: catalog, cart, checkout, saved cards, and order history for one signed-in customer."""

from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from shop import db
from shop.cards import card_expired, parse_expiry
from shop.payments_client import PaymentsClient, PaymentsUnavailable
from shop.version import current_commit

HERE = Path(__file__).parent
templates = Jinja2Templates(directory=HERE / "templates")
templates.env.filters["money"] = lambda cents: f"${cents / 100:,.2f}"
templates.env.filters["when"] = lambda stamp: datetime.fromisoformat(stamp).strftime("%b %-d, %Y at %H:%M UTC")


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def create_app(
    repository: db.Repository | None = None,
    payments: PaymentsClient | None = None,
    today: Callable[[], date] = utc_today,
) -> FastAPI:
    app = FastAPI(title="Storefront")
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    if repository is None:
        connection = db.connect()
        db.seed(connection)
        repository = db.Repository(connection)
    app.state.repository = repository
    app.state.payments = payments or PaymentsClient()
    app.state.commit = current_commit()
    customer_id = db.DEMO_CUSTOMER

    def render(request: Request, template: str, **context):
        repository = request.app.state.repository
        cart = repository.cart(customer_id)
        return templates.TemplateResponse(
            request,
            template,
            {"customer": repository.customer(customer_id), "cart_count": sum(line["quantity"] for line in cart), **context},
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "commit": app.state.commit, "database": str(db.DEFAULT_PATH)}

    @app.get("/", response_class=HTMLResponse)
    def catalog(request: Request):
        return render(request, "catalog.html", products=request.app.state.repository.products())

    @app.post("/cart/add")
    def add_to_cart(request: Request, product_id: int = Form()):
        if request.app.state.repository.product(product_id) is None:
            return RedirectResponse("/", status_code=303)
        request.app.state.repository.add_to_cart(customer_id, product_id)
        return RedirectResponse("/cart", status_code=303)

    @app.post("/cart/remove")
    def remove_from_cart(request: Request, product_id: int = Form()):
        request.app.state.repository.remove_from_cart(customer_id, product_id)
        return RedirectResponse("/cart", status_code=303)

    @app.get("/cart", response_class=HTMLResponse)
    def cart(request: Request):
        lines = request.app.state.repository.cart(customer_id)
        return render(request, "cart.html", lines=lines, total_cents=sum(line["line_cents"] for line in lines))

    def saved_cards(repository: db.Repository) -> list[dict]:
        return [
            {**card, "expired": card_expired(card["expiry"], today())}
            for card in repository.saved_cards(customer_id)
        ]

    def render_checkout(request: Request, lines, total_cents: int, error: str | None = None):
        return render(
            request, "checkout.html", lines=lines, total_cents=total_cents,
            saved_cards=saved_cards(request.app.state.repository), error=error,
        )

    @app.get("/checkout", response_class=HTMLResponse)
    def checkout(request: Request):
        lines = request.app.state.repository.cart(customer_id)
        if not lines:
            return RedirectResponse("/cart", status_code=303)
        return render_checkout(request, lines, sum(line["line_cents"] for line in lines))

    @app.post("/checkout", response_class=HTMLResponse)
    def place_order(
        request: Request,
        card_number: str | None = Form(None),
        expiry: str | None = Form(None),
        name_on_card: str | None = Form(None),
        save_card: bool = Form(False),
        saved_card_id: int | None = Form(None),
    ):
        repository = request.app.state.repository
        payments = request.app.state.payments
        lines = repository.cart(customer_id)
        if not lines:
            return RedirectResponse("/cart", status_code=303)
        total_cents = sum(line["line_cents"] for line in lines)

        saved_card = None
        if saved_card_id is not None:
            saved_card = repository.saved_card(customer_id, saved_card_id)
            if saved_card is None:
                return render_checkout(request, lines, total_cents, "That card is no longer saved. Please choose another.")
            if card_expired(saved_card["expiry"], today()):
                return render_checkout(request, lines, total_cents, "That card has expired. Please use another card.")
        elif not (card_number and expiry and name_on_card):
            return render_checkout(request, lines, total_cents, "Please enter the name on the card, its number, and its expiry.")
        elif save_card and parse_expiry(expiry) is None:
            return render_checkout(request, lines, total_cents, "Please enter the expiry as MM/YY to save this card.")

        order_id = repository.create_order(customer_id, lines, total_cents)
        try:
            if saved_card is not None:
                charge = payments.charge_saved(total_cents, saved_card["payments_card_id"])
            else:
                charge = payments.charge(total_cents, card_number, expiry, name_on_card, save_card=save_card)
        except PaymentsUnavailable:
            repository.set_order_status(order_id, "failed")
            return render_checkout(
                request, lines, total_cents, "We couldn't reach the payment service. Your card was not charged."
            )
        if charge.status != "succeeded":
            repository.set_order_status(order_id, "declined", charge.id)
            return render_checkout(request, lines, total_cents, "Your card was declined. Please try another card.")
        repository.set_order_status(order_id, "paid", charge.id)
        if saved_card is None and save_card and charge.card_id:
            year, month = parse_expiry(expiry)
            last4 = card_number.replace(" ", "")[-4:]
            repository.save_card(customer_id, charge.card_id, last4, f"{month:02d}/{year % 100:02d}")
        repository.clear_cart(customer_id)
        return RedirectResponse(f"/orders/{order_id}", status_code=303)

    @app.get("/cards", response_class=HTMLResponse)
    def cards(request: Request):
        return render(request, "cards.html", saved_cards=saved_cards(request.app.state.repository))

    @app.post("/cards/remove")
    def remove_card(request: Request, saved_card_id: int = Form(), back: str = Form("/cards")):
        repository = request.app.state.repository
        card = repository.saved_card(customer_id, saved_card_id)
        if card is not None:
            try:
                request.app.state.payments.forget_card(card["payments_card_id"])
            except PaymentsUnavailable:
                return render(
                    request, "cards.html", saved_cards=saved_cards(repository),
                    error="We couldn't reach the payment service, so the card is still saved. Please try again.",
                )
            repository.remove_saved_card(customer_id, saved_card_id)
        # Only the two pages that list saved cards are valid places to return to.
        return RedirectResponse(back if back in ("/checkout", "/cards") else "/cards", status_code=303)

    @app.get("/orders", response_class=HTMLResponse)
    def orders(request: Request):
        return render(request, "orders.html", orders=request.app.state.repository.orders(customer_id))

    @app.get("/orders/{order_id}", response_class=HTMLResponse)
    def order(request: Request, order_id: int):
        repository = request.app.state.repository
        order = repository.order(order_id)
        if order is None or order["customer_id"] != customer_id:
            return RedirectResponse("/orders", status_code=303)
        return render(request, "order.html", order=order, lines=repository.order_lines(order_id))

    return app


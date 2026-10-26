"""The storefront web app: catalog, cart, checkout, and order history for one signed-in customer."""

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from shop import db
from shop.payments_client import PaymentsClient, PaymentsUnavailable
from shop.version import current_commit

HERE = Path(__file__).parent
templates = Jinja2Templates(directory=HERE / "templates")
templates.env.filters["money"] = lambda cents: f"${cents / 100:,.2f}"
templates.env.filters["when"] = lambda stamp: datetime.fromisoformat(stamp).strftime("%b %-d, %Y at %H:%M UTC")


def create_app(repository: db.Repository | None = None, payments: PaymentsClient | None = None) -> FastAPI:
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

    def checkout_context(lines, code: str | None):
        subtotal_cents = sum(line["line_cents"] for line in lines)
        discount = db.discount_for(code, subtotal_cents)
        return {
            "lines": lines,
            "subtotal_cents": subtotal_cents,
            "discount": discount,
            "code": code or "",
            "code_rejected": bool(code) and discount is None,
            "total_cents": subtotal_cents - (discount.cents if discount else 0),
        }

    @app.get("/checkout", response_class=HTMLResponse)
    def checkout(request: Request, code: str | None = None):
        lines = request.app.state.repository.cart(customer_id)
        if not lines:
            return RedirectResponse("/cart", status_code=303)
        return render(request, "checkout.html", **checkout_context(lines, code))

    @app.post("/checkout", response_class=HTMLResponse)
    def place_order(
        request: Request,
        card_number: str = Form(),
        expiry: str = Form(),
        name_on_card: str = Form(),
        code: str = Form(""),
    ):
        repository = request.app.state.repository
        lines = repository.cart(customer_id)
        if not lines:
            return RedirectResponse("/cart", status_code=303)
        context = checkout_context(lines, code)
        subtotal_cents, total_cents = context["subtotal_cents"], context["total_cents"]
        order_id = repository.create_order(customer_id, lines, total_cents, context["discount"])
        try:
            charge = request.app.state.payments.charge(subtotal_cents, card_number, expiry, name_on_card)
        except PaymentsUnavailable:
            repository.set_order_status(order_id, "failed")
            return render(
                request, "checkout.html", **context,
                error="We couldn't reach the payment service. Your card was not charged.",
            )
        if charge.status != "succeeded":
            repository.set_order_status(order_id, "declined", charge.id)
            return render(
                request, "checkout.html", **context,
                error="Your card was declined. Please try another card.",
            )
        repository.set_order_status(order_id, "paid", charge.id)
        repository.clear_cart(customer_id)
        return RedirectResponse(f"/orders/{order_id}", status_code=303)

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


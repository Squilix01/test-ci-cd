import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from services import ShippingService


class Product:
    def __init__(self, name, price, available_amount):
        self.name = name
        self.price = price
        self.available_amount = available_amount

    def is_available(self, requested_amount):
        return self.available_amount >= requested_amount

    def buy(self, requested_amount):
        if self.is_available(requested_amount):
            self.available_amount -= requested_amount
        else:
            raise ValueError("Not enough items")

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name


class ShoppingCart:
    def __init__(self):
        self.products = dict()

    def contains_product(self, product):
        return product in self.products

    def get_product_count(self, product):
        return self.products.get(product, 0)

    def calculate_total(self):
        return sum([p.price * count for p, count in self.products.items()])

    def add_product(self, product: Product, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if not product.is_available(amount):
            raise ValueError(f"Product {product} has only {product.available_amount} items")

        current_amount = self.products.get(product, 0)
        self.products[product] = current_amount + amount

    def remove_product(self, product):
        if product in self.products:
            del self.products[product]

    # МОДИФИКАЦИЯ ДЛЯ ЛР3 (листинг 3.8)
    def submit_cart_order(self):
        product_ids = []
        for product, count in self.products.items():
            product.buy(count)
            product_ids.append(str(product))
        self.products.clear()
        return product_ids


@dataclass
class Order:
    cart: ShoppingCart
    shipping_service: ShippingService
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def place_order(self, shipping_type, due_date: datetime = None):
        if not due_date:
            due_date = datetime.now(timezone.utc) + timedelta(seconds=3)

        product_ids = self.cart.submit_cart_order()
        return self.shipping_service.create_shipping(shipping_type, product_ids, self.order_id, due_date)


@dataclass
class Shipment:
    shipping_id: str
    shipping_service: ShippingService

    def check_shipping_status(self):
        return self.shipping_service.check_status(self.shipping_id)

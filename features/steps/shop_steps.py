from behave import given, when, then
from app.eshop import Product, ShoppingCart, Order


@given('A product "{name}" with price {price} and availability {amount}')
def create_product(context, name, price, amount):
    context.product = Product(name=name, price=float(price), available_amount=int(amount))

@given('An empty shopping cart')
def create_cart(context):
    context.cart = ShoppingCart()
    context.error = None


@when('I add product to the cart in amount {amount}')
def add_product_step(context, amount):
    try:
        context.cart.add_product(context.product, int(amount))
        context.success = True
    except ValueError as e:
        context.success = False
        context.error = e

@when('I remove the product from the cart')
def remove_product_step(context):
    context.cart.remove_product(context.product)

@when('I place an order')
def place_order_step(context):
    order = Order(context.cart)
    order.place_order()


@then('Product is added to the cart successfully')
def check_success(context):
    assert context.success is True

@then('Product is not added to cart (Error occurs)')
def check_fail(context):
    assert context.success is False

@then('The cart total should be {total}')
def check_total(context, total):
    assert context.cart.calculate_total() == float(total)

@then('The cart should be empty')
def check_empty(context):
    assert len(context.cart.products) == 0

@then('The product availability should be {remaining}')
def check_stock(context, remaining):
    assert context.product.available_amount == int(remaining)

@then('Checking availability for {amount} should return True')
def check_is_avail_true(context, amount):
    assert context.product.is_available(int(amount)) is True

@then('Checking availability for {amount} should return False')
def check_is_avail_false(context, amount):
    assert context.product.is_available(int(amount)) is False
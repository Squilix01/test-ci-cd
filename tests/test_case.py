import unittest
from unittest.mock import MagicMock
from app.eshop import Product, ShoppingCart, Order


class TestProduct(unittest.TestCase):
    def setUp(self):
        self.product = Product(name="Test", price=10.0, available_amount=5)

    def test_is_available_true_when_enough(self):
        self.assertTrue(self.product.is_available(5))
        self.assertTrue(self.product.is_available(1))

    def test_is_available_false_when_not_enough(self):
        self.assertFalse(self.product.is_available(6))

    def test_buy_decreases_available_amount(self):
        self.product.buy(3)
        self.assertEqual(self.product.available_amount, 2)

    def test_buy_raises_when_not_enough(self):
        with self.assertRaises(ValueError):
            self.product.buy(999)

    def test_products_equal_by_name(self):
        p1 = Product("A", 10, 1)
        p2 = Product("A", 999, 999)
        self.assertEqual(p1, p2)  

    def test_products_hash_by_name(self):
        p1 = Product("A", 10, 1)
        p2 = Product("A", 20, 2)
        s = {p1, p2}
        self.assertEqual(len(s), 1)  


class TestShoppingCart(unittest.TestCase):
    def setUp(self):
        self.p1 = Product("P1", 10.0, 10)
        self.p2 = Product("P2", 5.0, 10)
        self.cart = ShoppingCart()

    def test_contains_product_false_initially(self):
        self.assertFalse(self.cart.contains_product(self.p1))

    def test_add_product_increases_count(self):
        self.cart.add_product(self.p1, 2)
        self.assertTrue(self.cart.contains_product(self.p1))
        self.assertEqual(self.cart.get_product_count(self.p1), 2)

    def test_add_same_product_twice_sums_amount(self):
        self.cart.add_product(self.p1, 2)
        self.cart.add_product(self.p1, 3)
        self.assertEqual(self.cart.get_product_count(self.p1), 5)

    def test_add_zero_amount_raises(self):
        with self.assertRaises(ValueError):
            self.cart.add_product(self.p1, 0)

    def test_add_negative_amount_raises(self):
        with self.assertRaises(ValueError):
            self.cart.add_product(self.p1, -1)

    def test_add_more_than_available_raises(self):
        with self.assertRaises(ValueError):
            self.cart.add_product(self.p1, 999)

    def test_calculate_total(self):
        self.cart.add_product(self.p1, 2)  # 2 * 10
        self.cart.add_product(self.p2, 3)  # 3 * 5
        self.assertEqual(self.cart.calculate_total(), 35.0)

    def test_remove_product_removes(self):
        self.cart.add_product(self.p1, 1)
        self.cart.remove_product(self.p1)
        self.assertFalse(self.cart.contains_product(self.p1))
        self.assertEqual(self.cart.get_product_count(self.p1), 0)

    def test_submit_cart_order_buys_and_clears_cart(self):
        self.cart.add_product(self.p1, 4)
        self.cart.submit_cart_order()
        self.assertEqual(self.p1.available_amount, 6)   # 10 - 4
        self.assertFalse(self.cart.contains_product(self.p1))
        self.assertEqual(self.cart.calculate_total(), 0)

    def test_submit_cart_order_calls_buy_for_each_product(self):

        self.p1.buy = MagicMock()
        self.p2.buy = MagicMock()
        self.cart.add_product(self.p1, 2)
        self.cart.add_product(self.p2, 3)

        self.cart.submit_cart_order()

        self.p1.buy.assert_called_once_with(2)
        self.p2.buy.assert_called_once_with(3)


class TestOrder(unittest.TestCase):
    def test_place_order_calls_submit_cart_order(self):
        cart = ShoppingCart()
        cart.submit_cart_order = MagicMock(return_value=["Product"])

        fake_shipping_service = MagicMock()
        fake_shipping_service.create_shipping = MagicMock(return_value="ship_1")

        order = Order(cart, fake_shipping_service)
        order.place_order("Нова Пошта")

        cart.submit_cart_order.assert_called_once()
        fake_shipping_service.create_shipping.assert_called_once()


if __name__ == "__main__":
    unittest.main()

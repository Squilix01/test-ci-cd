Feature: E-shop functionality
  We want to test Product, ShoppingCart and Order capabilities

  # --- Scenarios for Adding to Cart ---
  Scenario: Successful add product to cart
    Given A product "Apple" with price 10 and availability 50
    And An empty shopping cart
    When I add product to the cart in amount 10
    Then Product is added to the cart successfully

  Scenario: Failed add product to cart (Not enough items)
    Given A product "Apple" with price 10 and availability 50
    And An empty shopping cart
    When I add product to the cart in amount 51
    Then Product is not added to cart (Error occurs)

  Scenario: Add boundary amount (All available)
    Given A product "Laptop" with price 1000 and availability 5
    And An empty shopping cart
    When I add product to the cart in amount 5
    Then Product is added to the cart successfully

  Scenario: Add zero items (Boundary check)
      Given A product "Mouse" with price 20 and availability 10
      And An empty shopping cart
      When I add product to the cart in amount 0
      Then Product is not added to cart (Error occurs)

  # --- Scenarios for Cart Operations ---
  Scenario: Calculate total price
    Given A product "Phone" with price 500 and availability 10
    And An empty shopping cart
    When I add product to the cart in amount 2
    Then The cart total should be 1000

  Scenario: Remove product from cart
    Given A product "Tablet" with price 300 and availability 10
    And An empty shopping cart
    When I add product to the cart in amount 1
    And I remove the product from the cart
    Then The cart should be empty

  # --- Scenarios for Order Processing ---
  Scenario: Submit order successfully reduces stock
    Given A product "Monitor" with price 200 and availability 10
    And An empty shopping cart
    When I add product to the cart in amount 3
    And I place an order
    Then The product availability should be 7

  Scenario: Submit order clears the cart
    Given A product "Keyboard" with price 50 and availability 20
    And An empty shopping cart
    When I add product to the cart in amount 1
    And I place an order
    Then The cart should be empty

  # --- Scenarios for Product Logic ---
  Scenario: Check availability returns True
    Given A product "Milk" with price 2 and availability 100
    Then Checking availability for 50 should return True

  Scenario: Check availability returns False
    Given A product "Bread" with price 1 and availability 10
    Then Checking availability for 11 should return False
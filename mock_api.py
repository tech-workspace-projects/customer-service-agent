"""
This file simulates the e-commerce backend APIs as defined
in the POC Scope of Work.
"""

# Mock database tables
MOCKED_ORDERS = {
    "12345": "Your order 12345 is currently out for delivery and should arrive today.",
    "54321": "Your order 54321 was delivered on Tuesday.",
    "12346": "Your order 12346 has shipped and is expected Friday.",
    "99999": "Your order 99999 is still processing."
}

MOCKED_RETURNS = {
    "12345": "Your order 12345 is not eligible for return as it is still in transit.",
    "54321": "Your order 54321 is eligible for return. You can start the process here: [www.example.com/return/54321]",
    "12346": "Your order 12346 is eligible for return. You can start the process here: [www.example.com/return/12346]"
}

MOCKED_PRODUCTS = {
    "red shoes": "Yes, the 'Red Shoes' are in stock in sizes 8, 9, and 10.",
    "blue shirt": "I'm sorry, the 'Blue Shirt' is currently out of stock.",
    "skyhook": "I'm sorry, I don't see a product called 'Skyhook' in our catalog."
}


def track(order_id: str) -> str:
    """
    Mocks the API call to track an order.
    """
    return MOCKED_ORDERS.get(order_id, "I'm sorry, I could not find an order with that number.")

def return_eligible(order_id: str) -> str:
    """
    Mocks the API call to check if an order is eligible for return.
    """
    return MOCKED_RETURNS.get(order_id, "I'm sorry, I could not find an order with that number.")

def get_product_info(product_name: str) -> str:
    """
    Mocks the API call to get product information.
    """
    product_name_lower = product_name.lower().strip()
    return MOCKED_PRODUCTS.get(product_name_lower, f"I'm sorry, I don't have any information on a product called '{product_name}'.")

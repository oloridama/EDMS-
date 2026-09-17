from shared.logging import log

class PricingRepository:
    """
    The repository for persisting and retrieving pricing info for the business
    """
    def __init__(self, products_price_list: dict):
        """
        Initializes the PricingRepository with a dictionary of product prices.
        """
        self.price_list = products_price_list if products_price_list else {}
        pass

    def save_price(self, product: str, price: int):
        """
        Saves the price of a product in the price list.
        """
        self.price_list[product] = price

    def edit_price(self, product: str, amount: int):
        """
        Edits the price of a product in the price list.
        """
        for product_name, unit_price in self.price_list.items():
            if product_name == product:
                self.price_list[product_name] = amount
                log(f"{product_name} old price removed, new unit price {unit_price} is set!")

    def get_price(self, product: str):
        """
        Retrieves the price of a product from the price list.
        """
        for product_name, unit_price in self.price_list.items():
            if product_name == product:
                return unit_price

    @staticmethod
    def total(unit_price: int, quantity: int):
        return unit_price * quantity
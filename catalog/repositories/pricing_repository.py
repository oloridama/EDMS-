from shared.logging import log

class PricingRepository:
    """
    The repository for persisting and retrieving pricing info for the business
    """
    def __init__(self, products_price_list: dict):
        self.price_list = products_price_list if products_price_list else {}
        pass

    def save_price(self, product: str, price: int):
        self.price_list[product] = price

    def edit_price(self, product: str, amount: int):
        for product_name, unit_price in self.price_list.items():
            if product_name == product:
                self.price_list[product_name] = amount
                log(f"{product_name} old price removed, new unit price {unit_price} is set!")

    def get_price(self, product: str):
        for product, unit_price in self.price_list.items():
            if product == product:
                return unit_price

    @staticmethod
    def total(unit_price: int, quantity: int):
        return unit_price * quantity
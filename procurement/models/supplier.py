from dataclasses import dataclass

@dataclass
class Supplier:
    """
    A person or establishment that edms buys product from
    """
    name: str
    address: str
    email: str
    phone: str
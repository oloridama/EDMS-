from dataclasses import dataclass

@dataclass
class Transporter:
    name: str # the name of the transporter company, e.g. "FedEx", "UPS", "DHL" OR the name of the driver if company is handling the delivery themselves
    contact_number: str # the contact number of the transporter company OR driver
    email: str # the email address of the transporter company or driver
    address: str # the address of the transporter company or driver
    transportation_type: str # the type of transportation used by the transporter company or driver, e.g. "Air", "Sea", "Land"
    marital_status: str | None # the marital status of the transporter company or driver, e.g. "Single", "Married", "Divorced", "Widowed"
    dob: str | None # the date of birth of the transporter company or driver, e.g. "YYYY-MM-DD"
    citizenship: str | None # the citizenship of the transporter company or driver, e.g. "USA", "Canada", "UK"
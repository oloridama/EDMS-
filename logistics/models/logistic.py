from dataclasses import dataclass
from logistics.models.mode_of_transport import ModeOfTransport
from logistics.models.transporter import Transporter
from logistics.models.mode_of_transport import ModeOfTransport

@dataclass
class Logistic:
    tracking_id: str
    eta: str    # estimated time of arrival for the delivery
    status: str # shows the status of the delivery, e.g. "In Transit", "Delivered", "Delayed"
    transporter: Transporter # the transporter company or driver handling the delivery
    mode_of_transportation: ModeOfTransport # the mode of transportation used for the delivery, e.g. "Air", "Sea", "Land"

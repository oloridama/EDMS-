from dataclasses import dataclass

from catalog.models.product_configuration import ProductConfiguration

from logistics.models.mode_of_transport import ModeOfTransport
from logistics.models.transporter import Transporter
from logistics.models.mode_of_transport import ModeOfTransport

from enum import Enum
from datetime import datetime
class LogisticStatus(Enum):
    CREATED = "Created"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    DELAYED = "Delayed"
    CANCELLED = "Cancelled"
@dataclass
class Logistic:
    tracking_id: str
    eta: datetime | None    # estimated time of arrival for the delivery
    package: list[ProductConfiguration]     # A list of products' configurations ordered  that is to be delivered
    status: LogisticStatus    # shows the status of the delivery, e.g. "In Transit", "Delivered", "Delayed"
    transporter_id: str         # Unique identification for the transporter avoid duplicates in the system
    transporter_name_at_dispatch: str        # the transporter company or driver handling the delivery
    mode_of_transportation: ModeOfTransport     # the mode of transportation used for the delivery, e.g. "Air", "Sea", "Land"

    def update_status(self, new_status: LogisticStatus) -> None:
        allowed_transitions = {
            LogisticStatus.CREATED: {
                LogisticStatus.IN_TRANSIT,
                LogisticStatus.CANCELLED,
            },
            LogisticStatus.IN_TRANSIT: {
                LogisticStatus.DELIVERED,
                LogisticStatus.DELAYED,
            },
            LogisticStatus.DELAYED: {
                LogisticStatus.IN_TRANSIT,
                LogisticStatus.CANCELLED,
            },
            LogisticStatus.DELIVERED: set(),
            LogisticStatus.CANCELLED: set(),
        }

        if new_status not in allowed_transitions[self.status]:
            raise ValueError(
                f"Cannot move shipment from {self.status.value} "
                f"to {new_status.value}."
            )

        self.status = new_status

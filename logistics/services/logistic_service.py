# First question logistics asks is who or what is getting their order moved
# Quantity of goods to be moved determines the mode of transportation selected

from logistics.models.logistic import Logistic, LogisticStatus

from logistics.repositories.logistic_repository import LogisticRepository

from datetime import datetime

class LogisticService:
    def __init__(self, logistic_repo: LogisticRepository):
        self.logistic_repo = logistic_repo

    def create_logistic_ticket(
        self,
        tracking_id, 
        eta_text: str,
        package,
        transporter_id, 
        transporter_name,
        mode_of_transport
    ):
        """
        The ticket that shows the information of the move of the product
        """
        # Convert the optional eta string to datetime format
        eta_value = datetime.fromisoformat(eta_text) if eta_text else None

        # Create the ticket for the package logistics
        logistic_ticket = Logistic(
            tracking_id=tracking_id,
            eta=eta_value,
            package=package,
            status=LogisticStatus.CREATED,
            transporter_id=transporter_id,
            transporter_name_at_dispatch=transporter_name,
            mode_of_transportation=mode_of_transport
        )

        # Save the logistic ticket
        self.logistic_repo.save_ticket(logistic_ticket)
        return logistic_ticket

    def update_logistic_status(self, status: LogisticStatus, ticket_id):
        ticket = self.logistic_repo.fetch_ticket_by_id(ticket_id)
        if ticket is None:
            raise ValueError(f"Shipment '{ticket_id}' was not found.")

        ticket.update_status(status)
        self.logistic_repo.update_ticket(ticket)
        return ticket

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from catalog.models.product_configuration import ProductConfiguration
from catalog.repositories.records import (
    CategoryRecord,
    ProductConfigurationRecord,
    ProductRecord,
)
from catalog.repositories.mappers import configuration_from_record, product_from_record
from logistics.models.logistic import Logistic, LogisticStatus
from logistics.models.mode_of_transport import Dimensions, ModeOfTransport
from logistics.repositories.records import LogisticPackageRecord, LogisticRecord


class LogisticRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save_ticket(self, ticket: Logistic) -> str:
        existing = self.db_session.get(LogisticRecord, ticket.tracking_id)
        if existing is not None:
            raise ValueError(f"Shipment '{ticket.tracking_id}' already exists.")

        mode = ticket.mode_of_transportation
        record = LogisticRecord(
            tracking_id=ticket.tracking_id,
            eta=ticket.eta,
            status=ticket.status.value,
            transporter_id=ticket.transporter_id,
            transporter_name_at_dispatch=ticket.transporter_name_at_dispatch,
            mode_name_at_dispatch=mode.name,
            mode_reg_no_at_dispatch=mode.reg_no,
            mode_length_at_dispatch=mode.description.length,
            mode_width_at_dispatch=mode.description.width,
            mode_height_at_dispatch=mode.description.height,
        )
        for configuration in ticket.package:
            record.package.append(
                LogisticPackageRecord(
                    configuration_id=self._configuration_id_for(configuration)
                )
            )
        self.db_session.add(record)
        self.db_session.flush()
        return record.tracking_id

    def fetch_ticket_by_id(self, ticket_id: str) -> Logistic | None:
        record = self.db_session.scalar(
            select(LogisticRecord)
            .options(selectinload(LogisticRecord.package))
            .where(LogisticRecord.tracking_id == ticket_id)
        )
        if record is None:
            return None
        configurations = [
            self._configuration_from_package(item.configuration)
            for item in record.package
        ]
        return Logistic(
            tracking_id=record.tracking_id,
            eta=record.eta,
            package=configurations,
            status=LogisticStatus(record.status),
            transporter_id=record.transporter_id,
            transporter_name_at_dispatch=record.transporter_name_at_dispatch,
            mode_of_transportation=ModeOfTransport(
                name=record.mode_name_at_dispatch,
                description=Dimensions(
                    length=record.mode_length_at_dispatch,
                    width=record.mode_width_at_dispatch,
                    height=record.mode_height_at_dispatch,
                ),
                reg_no=record.mode_reg_no_at_dispatch,
            ),
        )

    def update_ticket(self, ticket: Logistic) -> None:
        record = self.db_session.get(LogisticRecord, ticket.tracking_id)
        if record is None:
            raise ValueError(f"Shipment '{ticket.tracking_id}' was not found.")
        record.status = ticket.status.value
        record.eta = ticket.eta
        self.db_session.flush()

    def get_package_configuration_ids(self, ticket_id: str) -> list[int]:
        """Return the persisted configuration IDs loaded into a shipment's package."""
        record = self.db_session.scalar(
            select(LogisticRecord)
            .options(selectinload(LogisticRecord.package))
            .where(LogisticRecord.tracking_id == ticket_id)
        )
        if record is None:
            return []
        return [item.configuration_id for item in record.package]

    def _configuration_id_for(self, configuration: ProductConfiguration) -> int:
        product_id = configuration.product.product_id
        records = self.db_session.scalars(
            select(ProductConfigurationRecord)
            .join(ProductRecord)
            .where(ProductRecord.product_id == product_id)
        ).all()
        for record in records:
            candidate = self._configuration_from_package(record)
            if self._same_configuration(candidate, configuration):
                return record.id
        raise ValueError(
            f"Product configuration for '{product_id}' must be saved before dispatch."
        )

    @staticmethod
    def _configuration_from_package(record: ProductConfigurationRecord) -> ProductConfiguration:
        product = product_from_record(record.product)
        return configuration_from_record(record, product)

    @staticmethod
    def _same_configuration(first: ProductConfiguration, second: ProductConfiguration) -> bool:
        scalar_fields = (
            "material", "weight", "color", "size", "volume", "length", "width",
            "unit", "additional_features",
        )
        if any(getattr(first, field) != getattr(second, field) for field in scalar_fields):
            return False
        first_specs = {(item.type.name, item.value) for item in first.specifications}
        second_specs = {(item.type.name, item.value) for item in second.specifications}
        first_prices = {
            (item.min_quantity, item.max_quantity, item.unit_price)
            for item in first.pricing.pricing_rules
        }
        second_prices = {
            (item.min_quantity, item.max_quantity, item.unit_price)
            for item in second.pricing.pricing_rules
        }
        return first_specs == second_specs and first_prices == second_prices

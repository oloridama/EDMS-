from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from catalog.models.product_configuration import ProductConfiguration
from catalog.repositories.configuration_repository import ConfigurationRepository
from catalog.repositories.mappers import configuration_from_record, product_from_record
from catalog.repositories.records import (
    CategoryRecord,
    ProductConfigurationRecord,
    ProductRecord,
)
from sales.models.sales_order import (
    Customer,
    SalesOrder,
    SalesOrderLine,
    SalesOrderStatus,
)
from sales.repositories.records import CustomerRecord, SalesOrderLineRecord, SalesOrderRecord


class SalesOrderRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save_order(self, order: SalesOrder) -> int:
        customer_record = self.db_session.get(
            CustomerRecord,
            order.customer.customer_id,
        )
        if customer_record is None:
            customer_record = CustomerRecord(
                customer_id=order.customer.customer_id,
                name=order.customer.name,
                phone=order.customer.phone,
                email=order.customer.email,
                address=order.customer.address,
            )
            self.db_session.add(customer_record)
        else:
            customer_record.name = order.customer.name
            customer_record.phone = order.customer.phone
            customer_record.email = order.customer.email
            customer_record.address = order.customer.address

        record = (
            self.db_session.get(SalesOrderRecord, order.order_id)
            if order.order_id is not None
            else None
        )
        if record is None:
            record = SalesOrderRecord(
                customer=customer_record,
                warehouse_id=order.warehouse_id,
                status=order.status.value,
                total=order.total,
            )
            self.db_session.add(record)
        else:
            record.customer = customer_record
            record.warehouse_id = order.warehouse_id
            record.status = order.status.value
            record.total = order.total
            record.lines.clear()

        record.lines.extend(
            SalesOrderLineRecord(
                configuration_id=line.configuration_id,
                quantity=line.quantity,
                fulfilled_quantity=line.fulfilled_quantity,
                dispatched_quantity=line.dispatched_quantity,
                unit_price=line.unit_price,
            )
            for line in order.lines
        )
        self.db_session.flush()
        order.order_id = record.id
        return record.id

    def get_order(self, order_id: int) -> SalesOrder | None:
        record = self.db_session.scalar(
            select(SalesOrderRecord)
            .options(
                selectinload(SalesOrderRecord.customer),
                selectinload(SalesOrderRecord.lines)
                .selectinload(SalesOrderLineRecord.configuration)
                .selectinload(ProductConfigurationRecord.product)
                .selectinload(ProductRecord.category)
                .selectinload(CategoryRecord.specification_types),
                selectinload(SalesOrderRecord.lines)
                .selectinload(SalesOrderLineRecord.configuration)
                .selectinload(ProductConfigurationRecord.specifications),
                selectinload(SalesOrderRecord.lines)
                .selectinload(SalesOrderLineRecord.configuration)
                .selectinload(ProductConfigurationRecord.pricing_rules),
            )
            .where(SalesOrderRecord.id == order_id)
        )
        if record is None:
            return None
        customer = Customer(
            customer_id=record.customer.customer_id,
            name=record.customer.name,
            phone=record.customer.phone,
            email=record.customer.email,
            address=record.customer.address,
        )
        lines = []
        for line_record in record.lines:
            product = product_from_record(line_record.configuration.product)
            configuration = configuration_from_record(line_record.configuration, product)
            lines.append(
                SalesOrderLine(
                    product_configuration=configuration,
                    configuration_id=line_record.configuration_id,
                    quantity=line_record.quantity,
                    unit_price=line_record.unit_price,
                    fulfilled_quantity=line_record.fulfilled_quantity,
                    dispatched_quantity=line_record.dispatched_quantity,
                )
            )
        order = SalesOrder(customer, record.warehouse_id, lines)
        order.status = SalesOrderStatus(record.status)
        order.order_id = record.id
        return order

    def get_configuration(self, configuration_id: int) -> ProductConfiguration | None:
        return ConfigurationRepository(self.db_session).get_configuration(configuration_id)

    def get_configuration_id(self, configuration: ProductConfiguration) -> int:
        return ConfigurationRepository(self.db_session).get_configuration_id(configuration)

    def get_orders(self) -> list[SalesOrder]:
        order_ids = self.db_session.scalars(select(SalesOrderRecord.id)).all()
        return [self.get_order(order_id) for order_id in order_ids]

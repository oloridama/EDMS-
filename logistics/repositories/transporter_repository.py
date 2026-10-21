from uuid import uuid4

from sqlalchemy.orm import Session

from logistics.models.transporter import Transporter
from logistics.repositories.records import TransporterRecord


class TransporterRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save(self, transporter: Transporter) -> str:
        transporter_id = transporter.transporter_id or str(uuid4())
        if self.db_session.get(TransporterRecord, transporter_id) is not None:
            raise ValueError(f"Transporter '{transporter_id}' already exists.")
        record = TransporterRecord(
            transporter_id=transporter_id,
            name=transporter.name,
            contact_number=transporter.contact_number,
            email=transporter.email,
            address=transporter.address,
            transportation_type=transporter.transportation_type,
            marital_status=transporter.marital_status,
            dob=transporter.dob,
            citizenship=transporter.citizenship,
        )
        self.db_session.add(record)
        self.db_session.flush()
        transporter.transporter_id = transporter_id
        return transporter_id

    def get_by_id(self, transporter_id: str) -> Transporter | None:
        record = self.db_session.get(TransporterRecord, transporter_id)
        if record is None:
            return None
        return Transporter(
            name=record.name,
            contact_number=record.contact_number,
            email=record.email,
            address=record.address,
            transportation_type=record.transportation_type,
            marital_status=record.marital_status,
            dob=record.dob,
            citizenship=record.citizenship,
            transporter_id=record.transporter_id,
        )

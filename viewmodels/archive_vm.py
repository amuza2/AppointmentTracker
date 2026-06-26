import logging
from viewmodels.base_viewmodel import BaseViewModel
from services import database
from models.appointment import Appointment

logger = logging.getLogger("archive_vm")


class ArchiveViewModel(BaseViewModel):
    def __init__(self):
        super().__init__()
        self._appointments: list[Appointment] = []
        self.load()

    @property
    def appointments(self) -> list[Appointment]:
        return self._appointments

    def load(self):
        self._appointments = database.get_archived_appointments()
        logger.info("load() -> %d archived: %s", len(self._appointments), [(a.id, a.city) for a in self._appointments])
        self.notify_change()

    def delete(self, appointment_id):
        database.delete_appointment(appointment_id)
        self.load()

    def recover(self, appointment_id):
        logger.info("recover(id=%s)", appointment_id)
        database.unarchive_appointment(appointment_id)
        self.load()

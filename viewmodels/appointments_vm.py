import logging
from viewmodels.base_viewmodel import BaseViewModel
from services import database
from models.appointment import Appointment

logger = logging.getLogger("appointments_vm")


class AppointmentsViewModel(BaseViewModel):
    def __init__(self):
        super().__init__()
        self._appointments: list[Appointment] = []
        self._filter_day: str | None = None
        self._filter_city: str = ""
        self.load()

    @property
    def appointments(self) -> list[Appointment]:
        filtered = self._appointments
        if self._filter_day:
            filtered = [a for a in filtered if a.day.lower() == self._filter_day.lower()]
        if self._filter_city:
            filtered = [a for a in filtered if self._filter_city.lower() in a.city.lower()]
        return filtered

    @property
    def cities(self) -> list[str]:
        seen = []
        for a in self._appointments:
            if a.city not in seen:
                seen.append(a.city)
        return sorted(seen)

    def load(self):
        self._appointments = database.get_active_appointments()
        logger.info("load() -> %d appointments: %s", len(self._appointments), [(a.id, a.city) for a in self._appointments])
        self.notify_change()

    def add(self, day, time, city, url, description):
        database.insert_appointment(day, time, city, url, description)
        self.load()

    def update(self, appointment_id, day, time, city, url, description):
        database.update_appointment(appointment_id, day, time, city, url, description)
        self.load()

    def archive(self, appointment_id):
        logger.info("archive(id=%s)", appointment_id)
        database.archive_appointment(appointment_id)
        self.load()

    def set_status(self, appointment_id, status):
        logger.info("set_status(id=%s, status=%s)", appointment_id, status)
        database.update_appointment_status(appointment_id, status)
        self.load()

    def set_filter_day(self, day: str | None):
        self._filter_day = day
        self.notify_change()

    def set_filter_city(self, city: str):
        self._filter_city = city
        self.notify_change()

    def clear_filters(self):
        self._filter_day = None
        self._filter_city = ""
        self.notify_change()

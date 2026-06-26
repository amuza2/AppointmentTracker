from dataclasses import dataclass


@dataclass
class Appointment:
    id: int | None
    day: str
    time: str
    city: str
    url: str
    description: str
    archived: bool = False
    status: str = "pending"
    created_at: str | None = None

from dataclasses import dataclass
from enum import Enum


@dataclass
class ToDo:
    name: str
    start_time: str
    end_time: str

    def __str__(self) -> str:
        return f"{self.start_time} - {self.end_time} {self.name}"


class DayOfWeek(Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

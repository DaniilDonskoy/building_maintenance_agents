from __future__ import annotations
from dataclasses import dataclass

from .incident_type import IncidentType


@dataclass
class Incident:
    incident_id: int
    incident_type: IncidentType
    severity: float
    location_id: int  # ID of node | edge
    location_type: str  # node | edge
    start_time: int
    duration: int = 0  # incident duration
    spread_count: int = 0
    # Максимальная продолжительность до просрочки (72 часа)
    max_duration: int = 72

    def __post_init__(self):
        base_duration = {
            IncidentType.GVS_RISER_FAILURE: 18,
            IncidentType.GVS_PIPE_FAILURE: 12,
            IncidentType.HVS_RISER_FAILURE: 18,
            IncidentType.HVS_PIPE_FAILURE: 12,
        }.get(self.incident_type, 15)

        self.duration = int(base_duration * (1 + self.severity))
        # Флаг для отслеживания применённого штрафа
        self._overdue_penalty_applied = False

    @property
    def is_active(self) -> bool:
        return self.duration > 0 and self.severity > 0

    @property
    def is_overdue(self) -> bool:
        """Проверяет, является ли инцидент просроченным (длительность превышает максимальную)."""
        age = self._get_age()
        return age >= self.max_duration

    @property
    def overdue_hours(self) -> int:
        """Количество часов просрочки."""
        age = self._get_age()
        return max(0, age - self.max_duration)

    def _get_age(self) -> int:
        """Возвращает возраст инцидента в часах."""
        # Используем base_duration как начальную длительность, но отслеживаем реальное время
        # В оригинальном коде duration уменьшается, поэтому возраст = начальная длительность - текущая длительность
        base_duration = {
            IncidentType.GVS_RISER_FAILURE: 18,
            IncidentType.GVS_PIPE_FAILURE: 12,
            IncidentType.HVS_RISER_FAILURE: 18,
            IncidentType.HVS_PIPE_FAILURE: 12,
        }.get(self.incident_type, 15)
        initial_duration = int(base_duration * (1 + self.severity))
        return initial_duration - self.duration

    def update(self) -> None:
        """Обновляет состояние инцидента на каждом шаге."""
        if self.is_active:
            decay = self.incident_type.decay_rate
            self.severity = max(0, self.severity - decay)
            self.duration -= 1

    def to_dict(self) -> dict:
        """Возвращает словарь с данными инцидента для логирования."""
        return {
            "incident_id": self.incident_id,
            "incident_type": self.incident_type.value,
            "severity": self.severity,
            "location_id": self.location_id,
            "location_type": self.location_type,
            "start_time": self.start_time,
            "duration": self.duration,
            "is_active": self.is_active,
            "is_overdue": self.is_overdue,
            "overdue_hours": self.overdue_hours,
            "spread_count": self.spread_count
        }

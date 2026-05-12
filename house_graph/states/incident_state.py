from typing import Dict, Union
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger


@dataclass(slots=True)
class IncidentState:

    has_incident: bool = field(default_factory=bool)
    message: str = field(default_factory=str)
    created_at: Optional[int] = field(default=None)

    def set_incident(self, message: str, current_step: int = 0):
        if not self.has_incident and not bool(self.message):
            self.has_incident = True
            self.message = message
            self.created_at = current_step
            logger.info("Set incident: {}".format(message))

    def update_incident(self, message: str):
        if self.has_incident:
            self.message = message
            logger.info("Update incident: {}".format(message))

    def fix_incident(self):
        if self.has_incident:
            self.has_incident = False
            self.message = ""
            self.created_at = None
            logger.info("Fix incident")

    def age(self, current_step: int) -> int:
        if not self.has_incident or self.created_at is None:
            return 0
        return current_step - self.created_at
from typing import Dict, Union
from dataclasses import dataclass, field

from loguru import logger


@dataclass(slots=True)
class IncidentState:
    
    has_incident: bool = field(default_factory=bool)
    message: str = field(default_factory=str)
    obj: None = field(default=None)
    
    def set_incident(self, message: str):
        if not self.has_incident and not bool(self.message):
            self.has_incident = True
            self.message = message
            if self.obj:
                self.obj.house.incident_count += 1
            logger.info("Set incident: {}".format(message))
            
    
    def update_incident(self, message: str):
        if self.has_incident:
            self.message = message
            logger.info("Update incident: {}".format(message))
            
    def fix_incident(self):
        if self.has_incident:
            self.has_incident = False
            self.message = ""
            if self.obj:
                self.obj.house.incident_count -= 1
            logger.info("Fix incident")
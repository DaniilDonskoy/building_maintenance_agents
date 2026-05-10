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
            if self.obj:
                self.obj.house.incident_count += 1
                message += " (Total incidents in house {}: {})".format(id(self.obj.house), self.obj.house.incident_count)
            self.message = message
            logger.info("Set incident: {}".format(message))
            
    
    def update_incident(self, message: str):
        if self.has_incident:
            if self.obj:
                message += " (Total incidents in house {}: {})".format(id(self.obj.house), self.obj.house.incident_count)
            self.message = message
            logger.info("Update incident: {}".format(message))
            
    def fix_incident(self):
        if self.has_incident:
            self.has_incident = False
            message = ""
            if self.obj:
                self.obj.house.incident_count -= 1
                message += " (Total incidents in house {}: {})".format(id(self.obj.house), self.obj.house.incident_count)
            self.message = message
            logger.info("Fix incident{}".format(message))
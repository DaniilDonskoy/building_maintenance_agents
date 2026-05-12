from house_graph.house import House
from house_graph.states import IncidentState


class Complex:
    def __init__(self, houses: list[House]):
        self.houses = houses

    @property
    def incident_state(self) -> IncidentState:
        return IncidentState(
            has_incident=any(house.incident_state.has_incident for house in self.houses),
            message=f"{sum(house.incident_state.has_incident for house in self.houses)} houses with incidents"
        )

    def to_json(self):
        return {
            "houses": [house.to_json().model_dump() for house in self.houses]
        }

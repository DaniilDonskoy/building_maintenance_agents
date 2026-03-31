from house_graph.house import House


class Complex:
    def __init__(self, houses: list[House]):
        self.houses = houses

    def to_json(self):
        return {
            "houses": [house.to_json() for house in self.houses]
        }

from house_graph.samples import House15Factory, House16Factory, House27Factory
from random import choice as random_choice
from .complex import Complex


HOUSE_SPACING = 50.0


class ComplexFactory:
    @classmethod
    def build(cls, houses_x: int = 3, houses_y: int = 2) -> Complex:
        complex_houses = []
        for y in range(houses_y):
            for x in range(houses_x):
                house_factory = random_choice([House15Factory, House16Factory, House27Factory])
                if x == 0:
                    house_x = 0
                else:
                    house_x = x * HOUSE_SPACING + complex_houses[-1].length
                house = house_factory.build(x=house_x, y=y*HOUSE_SPACING)
                complex_houses.append(house)

        return Complex(houses=complex_houses)
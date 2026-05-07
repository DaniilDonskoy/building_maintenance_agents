from house_graph.samples import House15Factory, House16Factory, House27Factory
from random import choice as random_choice, uniform
from .complex import Complex


HOUSE_WIDTH = 10.0


class ComplexFactory:
    @classmethod
    def build(cls, total_houses: int) -> Complex:
        complex_houses = []
        max_attempts = 100

        for _ in range(total_houses):
            attempts = 0
            placed = False
            while attempts < max_attempts and not placed:
                house_factory = random_choice([House15Factory, House16Factory, House27Factory])
                
                x = uniform(0, 1000)
                y = uniform(0, 1000)
                
                house = house_factory.build(x=x, y=y)
                
                collides = False
                for existing in complex_houses:
                    if cls._houses_collide(house, existing):
                        collides = True
                        break
                
                if not collides:
                    complex_houses.append(house)
                    placed = True
                
                attempts += 1
        
        return Complex(houses=complex_houses)

    @staticmethod
    def _houses_collide(h1, h2):
        # Проверка на пересечение bounding box
        # h1.x to h1.x + h1.length, h1.y to h1.y + HOUSE_WIDTH
        return not (h1.x + h1.length <= h2.x or
                    h2.x + h2.length <= h1.x or
                    h1.y + HOUSE_WIDTH <= h2.y or
                    h2.y + HOUSE_WIDTH <= h1.y)
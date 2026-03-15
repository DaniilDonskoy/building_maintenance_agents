from ..house_factory import HouseFactory


class House15Factory(HouseFactory):
    floors = 15
    sections = 2
    apartments_per_section = 3
    lifts_per_section = 1
    risers_per_section = 1
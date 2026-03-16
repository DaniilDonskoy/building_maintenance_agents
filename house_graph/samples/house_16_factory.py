from ..house_factory import HouseFactory


class House16Factory(HouseFactory):
    floors = 16
    sections = 2
    apartments_per_section = 6
    lifts_per_section = 2
    risers_per_section = 2
from ..house_factory import HouseFactory


class House16Factory(HouseFactory):
    floors = 16
    sections = 2
    flats_per_section = 6
    elevs_per_section = 2
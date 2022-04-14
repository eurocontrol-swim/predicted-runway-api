from enum import Enum


class DestinationICAO(Enum):
    EHAM = 'EHAM'
    LFBO = 'LFBO'
    LFPO = 'LFPO'


DESTINATION_ICAOS = [destination_icao.value for destination_icao in DestinationICAO]

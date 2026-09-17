from dataclasses import dataclass

@dataclass
class Dimensions:
    length: float # the length of the mode of transport in meters
    width: float # the width of the mode of transport in meters
    height: float # the height of the mode of transport in meters
    
@dataclass
class ModeOfTransport:
    name: str # the name of the mode of transportation, e.g. "Air", "Sea", "Land"
    description: Dimensions   # describe the size of the mode of transport, the list should contain the length, width, and height of the mode of transport in meters, e.g. [length, width, height]
    reg_no: str # the registration number of the mode of transport, e.g. "ABC123", "XYZ456", "LMN789"

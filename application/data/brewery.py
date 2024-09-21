from dataclasses import dataclass


@dataclass
class Brewery:
    id: str
    name: str
    type: str
    full_location: str
    country: str
    num_checkins: int
    avg_rating: float

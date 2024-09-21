from dataclasses import dataclass


@dataclass
class Country:
    name: str
    num_breweries: int
    num_checkins: int
    avg_rating: float

from dataclasses import dataclass


@dataclass
class Style:
    name: str
    num_checkins: int
    avg_rating: float
    min_rating: float
    max_rating: float
    median_rating: float

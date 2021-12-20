from typing import List

import concentration.fuzzy.parse as parse
from concentration.fuzzy.classes import Interval


if __name__ == "__main__":
    intervals: List[Interval] = parse.read_intervals_from_json("intervals.json")
    parse.save_chart_of_intervals("intervals.jpg", intervals)

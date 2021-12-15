from typing import List

import fuzzy.parse as parse
from fuzzy.classes import Interval
from lib.concentration_grader import save_chart_of_intervals


if __name__ == "__main__":
    intervals: List[Interval] = parse.read_intervals_from_json("good_intervals.json")
    save_chart_of_intervals("good_intervals.jpg", intervals)

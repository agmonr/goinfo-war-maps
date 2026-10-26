"""Explicit minutes of the day (0-1439, simulated clock) for the acts of each war day whose clock label is only a word ("בצהריים", "ערב"...).
The casualty smoke (marker leaves the map 2 SIMULATION hours after it appears) needs minutes; where the act label has a time (07:45) that time is used,
for the rest these are OUR ASSUMPTIONS, chosen from the act's own text and kept monotonic with the neighbouring timed acts. key = act start (animation seconds)."""
MINUTES = {
    "1967-06-06": {78: 480, 90: 510, 100: 540, 110: 720, 122: 750, 132: 810, 146: 840, 184: 1020, 205: 1260, 222: 1430},
    "1967-06-07": {40: 480, 48: 490, 96: 660, 108: 720, 116: 750, 128: 780, 146: 1000, 172: 1200, 190: 1260},
    "1967-06-08": {0: 30, 26: 330, 40: 480, 72: 810, 100: 860, 116: 900, 128: 960, 166: 1380},
    "1967-06-09": {10: 240, 30: 435, 74: 760, 90: 800, 166: 1110, 176: 1120, 186: 1200, 200: 1260, 212: 1320, 226: 1400},
    "1967-06-10": {0: 60, 14: 120, 34: 520, 48: 560, 62: 640, 108: 830, 134: 1140, 146: 1150, 158: 1160},
}

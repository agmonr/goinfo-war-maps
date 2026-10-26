"""Which side a place on the war maps belonged to on the morning of 5 June 1967 (before the war), for the colour of its dot.
the owner 2026-10-19: bordeaux = other side, blue = Israel, grey = neutral/divided/international. Captured places keep the side they had BEFORE the capture."""
IL = set("nitz netanya kfs nahalal ramd lod tlv mevaseret rachel scopus megiddo degania hores dan dan2 teldan roshpina afula eilat ashdod haon gadot eingev gonen knaan".split())
# neutral: divided or international (Jerusalem as a whole, the UN's Government House, the Mandelbaum crossing, the Upper Customs House, the US ship Liberty)
NEUTRAL = set("jer gov mandel customs liberty".split())
def side(key):
    return "il" if key in IL else "neutral" if key in NEUTRAL else "ar"

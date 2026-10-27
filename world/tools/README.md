# Globe textures

`index.html` at the site root draws the ASCII globe from two small textures in this folder:

- `world.png` (1024x512, grayscale): character density. Land is white, ocean is dim gray.
- `classes.png` (1024x512, RGB): red channel is the terrain class per texel (0 deep ocean, 1 mid, 2 shallow,
  3 green, 4 tan, 5 gray mountain, 6 white ice), each stored as class x 36. Green channel is city light
  intensity 0 to 255 for the night side.

Both are produced by `tools/classify.py` from three NASA sources, all public domain via Wikimedia Commons.
Download them into one folder, named as below:

| file | source |
| --- | --- |
| `land_alpha.png` | Land shallow topo alpha 2048 (land mask) https://commons.wikimedia.org/wiki/File:Land_shallow_topo_alpha_2048.png |
| `land_topo.jpg` | Land shallow topo 2048 (Blue Marble true color, actually 21600x10800) https://commons.wikimedia.org/wiki/File:Land_shallow_topo_2048.jpg |
| `srtm_ramp.jpg` | SRTM ramp2 world (8 bit heightmap, sea level = 12, about 25 m per step) https://commons.wikimedia.org/wiki/File:Srtm_ramp2.world.21600x10800.jpg |
| `citylights.jpg` | Earth's City Lights by DMSP, 1994-1995 https://commons.wikimedia.org/wiki/File:Earth%27s_City_Lights_by_DMSP,_1994-1995_(large).jpg |

The script expects the two big JPEGs pre-reduced to 2048x1024 PNGs (`topo_2048.png`, `srtm_2048.png`);
run `prepare.py` once to make them. Then:

```
python3 -m venv venv && ./venv/bin/pip install numpy pillow
./venv/bin/python tools/prepare.py <sources dir>
./venv/bin/python tools/classify.py <sources dir> . 1900 3300 750
```

The three numbers are the mountain thresholds in metres: elevation that counts as gray, elevation that counts
as white, and local relief (max minus min in a 7x7 window) that counts as rugged. The values shipped are
1900, 3300, 750. Lights are shaped in the script: the base level subtracted, a gamma of 0.72, and a
70/30 blend of max and mean pooling so a metropolis stays brighter than its sprawl.

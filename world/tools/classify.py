"""Build classes.png (terrain class per texel, plus city lights) and world.png (character density) for the globe.

Sources, both NASA, public domain, via Wikimedia Commons:
  topo_2048.png   Blue Marble land/shallow topo, true color
  srtm_2048.png   SRTM ramp heightmap, 8 bit, sea level = 12, roughly 25 m per step
  land_alpha.png  Blue Marble land mask (alpha)

Usage: classify.py <model_dir> <out_dir> [gray_m] [white_m] [relief_m]
"""
import sys, os
import numpy as np
from PIL import Image

model, out = sys.argv[1], sys.argv[2]
GRAY_M = float(sys.argv[3]) if len(sys.argv) > 3 else 1500    # elevation that counts as mountain
WHITE_M = float(sys.argv[4]) if len(sys.argv) > 4 else 3200   # elevation that counts as snow
RELIEF_M = float(sys.argv[5]) if len(sys.argv) > 5 else 500   # local relief that counts as rugged
M_PER_STEP = 25.0
SEA = 12

a = np.asarray(Image.open(os.path.join(model, 'topo_2048.png')).convert('RGB')).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
bright = (r + g + b) / 3
sat = a.max(axis=2) - a.min(axis=2)
land = np.asarray(Image.open(os.path.join(model, 'land_alpha.png')).convert('RGBA').split()[3].resize((2048, 1024), Image.LANCZOS)) > 128
elev = (np.asarray(Image.open(os.path.join(model, 'srtm_2048.png')).convert('L')).astype(float) - SEA).clip(0) * M_PER_STEP

def dilate(m, n):
    o = m.copy()
    for _ in range(n):
        o = o | np.roll(o, 1, 0) | np.roll(o, -1, 0) | np.roll(o, 1, 1) | np.roll(o, -1, 1)
    return o

# local relief: max minus min elevation in a 7x7 window
def win_max(x, k):
    o = x.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            o = np.maximum(o, np.roll(np.roll(x, dy, 0), dx, 1))
    return o
relief = win_max(elev, 3) - (-win_max(-elev, 3))

coast = dilate(land, 22) & ~land
cls = np.zeros(r.shape, np.uint8)                      # 0 deep ocean
cls[~land & ((bright >= 28) | coast)] = 1               # 1 mid
cls[~land & (bright >= 45)] = 2                          # 2 shallow
cls[land] = 3                                            # 3 green
cls[land & (r > g) & (g > b) & ((r - b) > 40) & (bright > 100)] = 4   # 4 tan
mountain = land & ((elev >= GRAY_M) | ((relief >= RELIEF_M) & (elev >= 700)))
cls[mountain] = 5                                        # 5 gray
snow = land & (elev >= WHITE_M)
cls[snow] = 6                                            # 6 white
ice = land & (bright >= 195) & (sat < 45)
cls[ice] = 6
rows = np.arange(cls.shape[0])[:, None]
cls[land & (rows < 60) & (bright >= 150)] = 6
cls[land & (rows > 1024 - 140)] = 6

names = ['deep', 'mid', 'shallow', 'green', 'tan', 'gray', 'white']
print({n: round(float((cls == i).mean() * 100), 2) for i, n in enumerate(names)})

# City lights from the DMSP night composite: lights are white or yellow over a blue base, so take
# the lesser of red and green above the base level. Max pool so small cities survive the downsample.
night = np.asarray(Image.open(os.path.join(model, 'citylights.jpg')).convert('RGB').resize((2048, 1024), Image.LANCZOS)).astype(float)
lights = np.clip((np.minimum(night[..., 0], night[..., 1]) - 85) / (255 - 85), 0, 1)
lights[~land | (cls == 6)] = 0
lights = np.power(lights, 0.72)
# Pool as a blend of max and mean: max keeps small cities alive, mean keeps a metropolis brighter than its sprawl.
blocks = lights.reshape(512, 2, 1024, 2)
small_lights = 0.7 * blocks.max(axis=(1, 3)) + 0.3 * blocks.mean(axis=(1, 3))
# A light touch of softening against flicker, far less than before so cities stay distinct.
nb = sum(np.roll(np.roll(small_lights, dy, 0), dx, 1) for dy, dx in [(1, 0), (-1, 0), (0, 1), (0, -1)]) / 4
small_lights = np.clip(np.maximum(small_lights, nb * 0.35), 0, 1)
print('lit texels', round(float((small_lights > 0.1).mean() * 100), 2), '%')

small = cls[::2, ::2]
tex = np.zeros(small.shape + (3,), np.uint8); tex[..., 0] = small * 36; tex[..., 1] = (small_lights * 255).astype(np.uint8)
Image.fromarray((small_lights * 255).astype(np.uint8), 'L').save(os.path.join(model, 'lights_preview.png'))
Image.fromarray(tex).save(os.path.join(out, 'classes.png'), optimize=True)
dens = np.where(land, 255, 130).astype(np.uint8)[::2, ::2]   # ocean 130 sRGB = 0.223 linear, matching ALBEDO in index.html
Image.fromarray(dens, 'L').save(os.path.join(out, 'world.png'), optimize=True)

pal = np.array([[0x2A,0x64,0xE0],[0x4F,0x93,0xF5],[0x93,0xCE,0xFF],[0x5C,0xC6,0x6A],[0xD9,0xB9,0x8C],[0xA3,0xA3,0xA3],[0xF5,0xF5,0xF5]], np.uint8)
Image.fromarray(pal[small]).resize((1024, 512)).save(os.path.join(model, 'class_preview.png'))
print('wrote', out)

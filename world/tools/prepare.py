"""Reduce the two full size NASA JPEGs to 2048x1024 PNGs for classify.py.

Usage: prepare.py <sources dir>
"""
import os, sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
d = sys.argv[1]
for src, dst, mode in [('land_topo.jpg', 'topo_2048.png', 'RGB'), ('srtm_ramp.jpg', 'srtm_2048.png', 'L')]:
    im = Image.open(os.path.join(d, src)); im.draft(mode, (2700, 1350)); im = im.convert(mode)
    im.resize((2048, 1024), Image.LANCZOS).save(os.path.join(d, dst))
    print('wrote', dst)

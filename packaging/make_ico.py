"""Renders packaging/steamos-isomounttool.svg into a multi-size Windows .ico.

Usage: python packaging/make_ico.py OUT.ico   (needs PySide6 + Pillow)
Created by Dominic Lesina x Claude
"""
import io
import os
import sys

from PIL import Image
from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
app = QGuiApplication(sys.argv[:1])
svg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steamos-isomounttool.svg")
renderer = QSvgRenderer(svg)
img = QImage(256, 256, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
renderer.render(p)
p.end()
buf = QBuffer()
buf.open(QIODevice.WriteOnly)
img.save(buf, "PNG")
pil = Image.open(io.BytesIO(bytes(buf.data())))
pil.save(sys.argv[1], sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon written:", sys.argv[1])

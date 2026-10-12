# lcd.py - pilote minimal ST7796 pour carte E32R40T (ESP32-32E 4.0" 320x480)
# Brochage carte : CS=15  DC=2  SCK=14  MOSI=13  MISO=12  BL=27  RST=EN
# Usage :
#   import lcd
#   lcd.init(landscape=True)
#   lcd.fill(lcd.BLACK)
#   lcd.text("Bus 31", 10, 10, lcd.WHITE, lcd.BLACK, scale=4)

from machine import Pin, SPI
import framebuf, time

WIDTH, HEIGHT = 320, 480

# Couleurs RGB565
BLACK  = 0x0000
WHITE  = 0xFFFF
RED    = 0xF800
GREEN  = 0x07E0
BLUE   = 0x001F
YELLOW = 0xFFE0
ORANGE = 0xFC00
GREY   = 0x8410

_bl  = Pin(27, Pin.OUT)
_cs  = Pin(15, Pin.OUT)
_dc  = Pin(2,  Pin.OUT)
_spi = SPI(1, baudrate=40_000_000, polarity=0, phase=0,
           sck=Pin(14), mosi=Pin(13), miso=Pin(12))
_cs.value(1)


def _cmd(c, data=None):
    _cs.value(0)
    _dc.value(0)
    _spi.write(bytes([c]))
    if data:
        _dc.value(1)
        _spi.write(bytes(data))
    _cs.value(1)


def init(landscape=False):
    """Reveille l'ecran et allume le retroeclairage."""
    global WIDTH, HEIGHT
    _cmd(0x01); time.sleep_ms(150)          # reset logiciel
    _cmd(0x11); time.sleep_ms(120)          # sortie de veille
    _cmd(0x3A, [0x55])                      # RGB565
    if landscape:
        _cmd(0x36, [0x28]); WIDTH, HEIGHT = 480, 320
    else:
        _cmd(0x36, [0x48]); WIDTH, HEIGHT = 320, 480
    _cmd(0x29); time.sleep_ms(50)           # allumage dalle
    _bl.value(1)


def backlight(on=True):
    _bl.value(1 if on else 0)


def _window(x, y, w, h):
    """Definit la zone d'ecriture et laisse CS bas, pret pour les pixels."""
    x2, y2 = x + w - 1, y + h - 1
    _cmd(0x2A, [x >> 8, x & 0xFF, x2 >> 8, x2 & 0xFF])
    _cmd(0x2B, [y >> 8, y & 0xFF, y2 >> 8, y2 & 0xFF])
    _cs.value(0)
    _dc.value(0)
    _spi.write(b'\x2C')
    _dc.value(1)


def fill_rect(x, y, w, h, color):
    _window(x, y, w, h)
    line = bytes([color >> 8, color & 0xFF]) * w
    for _ in range(h):
        _spi.write(line)
    _cs.value(1)


def fill(color=BLACK):
    fill_rect(0, 0, WIDTH, HEIGHT, color)


def text(s, x, y, fg=WHITE, bg=BLACK, scale=3):
    """Texte en police 8x8 integree, agrandie scale fois.
    Largeur occupee : len(s)*8*scale, hauteur : 8*scale."""
    w = len(s) * 8
    stride = (w + 7) // 8
    mask = bytearray(stride * 8)
    fb = framebuf.FrameBuffer(mask, w, 8, framebuf.MONO_HLSB)
    fb.fill(0)
    fb.text(s, 0, 0, 1)

    fg_hi, fg_lo = fg >> 8, fg & 0xFF
    bg_hi, bg_lo = bg >> 8, bg & 0xFF
    line = bytearray(w * scale * 2)

    _window(x, y, w * scale, 8 * scale)
    for row in range(8):
        i = 0
        base = row * stride
        for col in range(w):
            on = (mask[base + (col >> 3)] >> (7 - (col & 7))) & 1
            hi, lo = (fg_hi, fg_lo) if on else (bg_hi, bg_lo)
            for _ in range(scale):
                line[i] = hi
                line[i + 1] = lo
                i += 2
        for _ in range(scale):
            _spi.write(line)
    _cs.value(1)
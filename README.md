# Geometry Dash Icon Maker

A small Python desktop app for building a layered icon spritesheet and its
matching `.plist`. Runs on macOS, Windows, and Linux.

## Run it

Install Python 3 and Pillow:

```sh
python3 -m pip install -r requirements.txt
python3 icon_maker.py
```

On Windows, use `python` instead of `python3` if that is your Python command.
On macOS, use a Python installation that includes Tkinter (the python.org
installer includes it).

## Use it

Choose transparent image artwork for the base, secondary base, glow, and detail
layers. Set each layer's tint and opacity, and use the arrows to adjust the
overlap order. Select **Export PNG + plist** to save:

- `icon-maker.png`: a transparent, horizontal spritesheet containing one
  128 × 128 frame per layer, followed by the combined icon.
- `icon-maker.plist`: Cocos2d frame metadata matching that spritesheet.

PNG artwork is recommended to preserve transparent edges. Image files are
opened locally; the app does not upload your art.

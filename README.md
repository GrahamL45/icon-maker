# Icon Maker

A Geode mod for Geometry Dash 2.2081 that lets you recolor four icon-art layers
(base, secondary, glow, and detail), preview the combined icon, and export a
five-frame PNG atlas with matching plist metadata.

## Install on macOS

The `Build macOS` GitHub Actions workflow creates a `.geode` package artifact
for each push to `main`. Download the latest `icon-maker-macos` artifact from
the repository's **Actions** tab, extract it, and install the `.geode` file
with Geode.

The mod requires Geometry Dash 2.2081 and Geode 5.10.1.

## Build locally

Install the Geode CLI and SDK, then run:

```sh
geode build
```

The `.geode` package is created in `build/`. The mod adds an **ICON** button to
the main menu. Choose a layer, adjust its RGB channels, and click **Export PNG
+ PLIST**. The files are written to this mod's Geode save directory.

The spritesheet frames are `base.png`, `secondary.png`, `glow.png`, `detail.png`,
and `icon.png`.

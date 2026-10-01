#!/usr/bin/env python3
"""Create a layered Geometry Dash icon spritesheet and matching plist."""

from __future__ import annotations

import plistlib
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageTk

ICON_SIZE = 128
LAYER_SPECS = (
    ("base", "Base", "#ffffff", 100),
    ("secondary", "Secondary base", "#ffffff", 100),
    ("glow", "Glow", "#ffffff", 80),
    ("detail", "Detail", "#ffffff", 100),
)


@dataclass
class IconLayer:
    key: str
    name: str
    color: str
    opacity: int
    image: Image.Image | None = None
    path: Path | None = None


def render_layer(layer: IconLayer, size: int = ICON_SIZE) -> Image.Image:
    """Fit, tint, and set the opacity of one layer on a transparent canvas."""
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if layer.image is None:
        return output

    image = layer.image.convert("RGBA")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    left = (size - image.width) // 2
    top = (size - image.height) // 2
    output.alpha_composite(image, (left, top))

    red = int(layer.color[1:3], 16)
    green = int(layer.color[3:5], 16)
    blue = int(layer.color[5:7], 16)
    red_channel, green_channel, blue_channel, alpha_channel = output.split()
    red_channel = ImageChops.multiply(red_channel, Image.new("L", output.size, red))
    green_channel = ImageChops.multiply(green_channel, Image.new("L", output.size, green))
    blue_channel = ImageChops.multiply(blue_channel, Image.new("L", output.size, blue))
    alpha_channel = alpha_channel.point(lambda value: value * layer.opacity // 100)
    return Image.merge("RGBA", (red_channel, green_channel, blue_channel, alpha_channel))


def compose_icon(layers: list[IconLayer], size: int = ICON_SIZE) -> Image.Image:
    """Composite the layers in list order."""
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for layer in layers:
        icon.alpha_composite(render_layer(layer, size))
    return icon


def build_spritesheet(layers: list[IconLayer], size: int = ICON_SIZE) -> Image.Image:
    """Return the layer frames and combined icon in a horizontal RGBA atlas."""
    sheet = Image.new("RGBA", (size * (len(layers) + 1), size), (0, 0, 0, 0))
    for index, layer in enumerate(layers):
        sheet.alpha_composite(render_layer(layer, size), (index * size, 0))
    sheet.alpha_composite(compose_icon(layers, size), (len(layers) * size, 0))
    return sheet


def build_plist(layers: list[IconLayer], texture_name: str, size: int = ICON_SIZE) -> dict:
    """Build Cocos2d plist data whose frames match build_spritesheet()."""
    names = [f"{layer.key}.png" for layer in layers] + ["icon.png"]
    frames = {}
    for index, name in enumerate(names):
        x = index * size
        frames[name] = {
            "frame": f"{{{{{x},0}},{{{size},{size}}}}}",
            "offset": "{0,0}",
            "rotated": False,
            "sourceColorRect": f"{{{{0,0}},{{{size},{size}}}}}",
            "sourceSize": f"{{{size},{size}}}",
        }
    return {
        "frames": frames,
        "metadata": {
            "format": 3,
            "pixelFormat": "RGBA8888",
            "realTextureFileName": texture_name,
            "size": f"{{{size * len(names)},{size}}}",
            "textureFileName": texture_name,
        },
    }


class IconMakerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Geometry Dash Icon Maker")
        self.root.minsize(760, 520)
        self.root.configure(background="#171824")
        self.layers = [
            IconLayer(key, name, color, opacity)
            for key, name, color, opacity in LAYER_SPECS
        ]
        self._preview_image = None
        self._color_vars: list[tk.StringVar] = []
        self._opacity_vars: list[tk.IntVar] = []
        self._file_labels: list[ttk.Label] = []
        self._up_buttons: list[ttk.Button] = []
        self._down_buttons: list[ttk.Button] = []

        self._style()
        self._build_ui()
        self._refresh_preview()

    def _style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("App.TFrame", background="#171824")
        style.configure("Card.TFrame", background="#222434")
        style.configure("App.TLabel", background="#171824", foreground="#f3f2fa")
        style.configure("Card.TLabel", background="#222434", foreground="#f3f2fa")
        style.configure("Hint.TLabel", background="#222434", foreground="#aaaabd")
        style.configure("Card.TButton", padding=(8, 5))
        style.configure("Export.TButton", padding=(12, 9), font=("", 10, "bold"))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, style="App.TFrame", padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer, text="GEOMETRY DASH", style="App.TLabel",
            font=("", 9, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            outer, text="Icon Maker", style="App.TLabel",
            font=("", 24, "bold"),
        ).pack(anchor="w", pady=(2, 4))
        ttk.Label(
            outer,
            text="Load your own art, adjust each layer, and export a spritesheet with its plist.",
            style="App.TLabel",
        ).pack(anchor="w", pady=(0, 15))

        body = ttk.Frame(outer, style="App.TFrame")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        layer_card = ttk.Frame(body, style="Card.TFrame", padding=14)
        layer_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        layer_card.columnconfigure(0, weight=1)
        ttk.Label(
            layer_card, text="Icon layers", style="Card.TLabel",
            font=("", 13, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        headers = ttk.Frame(layer_card, style="Card.TFrame")
        headers.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        headers.columnconfigure(0, weight=1)
        for column, title in enumerate(("Artwork", "Tint", "Opacity", "Order")):
            ttk.Label(headers, text=title, style="Hint.TLabel").grid(
                row=0, column=column, padx=(0, 10), sticky="w"
            )

        self.rows = ttk.Frame(layer_card, style="Card.TFrame")
        self.rows.grid(row=2, column=0, sticky="new")
        self.rows.columnconfigure(0, weight=1)

        right = ttk.Frame(body, style="App.TFrame")
        right.grid(row=0, column=1, sticky="n")
        preview_card = ttk.Frame(right, style="Card.TFrame", padding=14)
        preview_card.pack(fill="x")
        ttk.Label(
            preview_card, text="Live preview", style="Card.TLabel",
            font=("", 13, "bold"),
        ).pack(anchor="w")
        self.preview = tk.Canvas(
            preview_card, width=256, height=256, bg="#38394a",
            highlightthickness=1, highlightbackground="#57586d",
        )
        self.preview.pack(pady=(10, 6))
        ttk.Label(
            preview_card, text="Checkerboard shows transparency",
            style="Hint.TLabel",
        ).pack(anchor="center")

        export_card = ttk.Frame(right, style="Card.TFrame", padding=14)
        export_card.pack(fill="x", pady=(12, 0))
        ttk.Label(
            export_card, text="Export files", style="Card.TLabel",
            font=("", 13, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            export_card,
            text="128 × 128 frames: each layer, then the combined icon.",
            style="Hint.TLabel", wraplength=245,
        ).pack(anchor="w", pady=(6, 12))
        ttk.Button(
            export_card, text="Export PNG + plist", style="Export.TButton",
            command=self._export,
        ).pack(fill="x")
        self.status = ttk.Label(
            export_card, text="", style="Hint.TLabel", wraplength=245,
        )
        self.status.pack(anchor="w", pady=(8, 0))

        ttk.Label(
            outer,
            text="Artwork is processed locally and is never uploaded.",
            style="App.TLabel",
        ).pack(anchor="center", pady=(14, 0))

        self._render_layer_rows()

    def _render_layer_rows(self) -> None:
        for child in self.rows.winfo_children():
            child.destroy()
        self._color_vars.clear()
        self._opacity_vars.clear()
        self._file_labels.clear()
        self._up_buttons.clear()
        self._down_buttons.clear()

        for index, layer in enumerate(self.layers):
            row = ttk.Frame(self.rows, style="Card.TFrame", padding=(0, 8))
            row.grid(row=index, column=0, sticky="ew")
            row.columnconfigure(0, weight=1)
            if index:
                ttk.Separator(row).grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 8))

            artwork = ttk.Frame(row, style="Card.TFrame")
            artwork.grid(row=1, column=0, sticky="ew", padx=(0, 8))
            artwork.columnconfigure(0, weight=1)
            ttk.Label(
                artwork, text=layer.name, style="Card.TLabel",
                font=("", 10, "bold"),
            ).grid(row=0, column=0, sticky="w")
            file_name = layer.path.name if layer.path else "Choose image…"
            file_label = ttk.Label(
                artwork, text=file_name, style="Hint.TLabel",
                width=25, anchor="w",
            )
            file_label.grid(row=1, column=0, sticky="w", pady=(2, 4))
            self._file_labels.append(file_label)
            ttk.Button(
                artwork, text="Choose PNG…", style="Card.TButton",
                command=lambda target=layer: self._choose_image(target),
            ).grid(row=2, column=0, sticky="w")

            color = tk.StringVar(value=layer.color)
            self._color_vars.append(color)
            ttk.Button(
                row, text=layer.color.upper(), style="Card.TButton",
                command=lambda target=layer: self._choose_color(target),
            ).grid(row=1, column=1, padx=(0, 10), sticky="n")

            opacity = tk.IntVar(value=layer.opacity)
            self._opacity_vars.append(opacity)
            scale = ttk.Scale(
                row, from_=0, to=100, orient="horizontal",
                command=lambda value, target=layer, variable=opacity: self._set_opacity(
                    target, variable, value
                ),
            )
            scale.set(layer.opacity)
            scale.grid(row=1, column=2, padx=(0, 10), sticky="ew")

            order = ttk.Frame(row, style="Card.TFrame")
            order.grid(row=1, column=3, sticky="n")
            up = ttk.Button(
                order, text="↑", width=3, style="Card.TButton",
                command=lambda i=index: self._move_layer(i, -1),
            )
            up.pack(pady=(0, 3))
            down = ttk.Button(
                order, text="↓", width=3, style="Card.TButton",
                command=lambda i=index: self._move_layer(i, 1),
            )
            down.pack()
            self._up_buttons.append(up)
            self._down_buttons.append(down)

        for index, button in enumerate(self._up_buttons):
            button.configure(state="disabled" if index == 0 else "normal")
            self._down_buttons[index].configure(
                state="disabled" if index == len(self.layers) - 1 else "normal"
            )

    def _choose_image(self, layer: IconLayer) -> None:
        file_path = filedialog.askopenfilename(
            title=f"Choose {layer.name} artwork",
            filetypes=(
                ("Image files", "*.png *.webp *.jpg *.jpeg"),
                ("All files", "*"),
            ),
        )
        if not file_path:
            return
        try:
            with Image.open(file_path) as source:
                image = source.convert("RGBA")
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not open image", str(error), parent=self.root)
            return

        layer.image = image
        layer.path = Path(file_path)
        self.status.configure(text="")
        self._render_layer_rows()
        self._refresh_preview()

    def _choose_color(self, layer: IconLayer) -> None:
        chosen = colorchooser.askcolor(
            color=layer.color, title=f"{layer.name} tint", parent=self.root
        )[1]
        if chosen:
            layer.color = chosen
            self._render_layer_rows()
            self._refresh_preview()

    def _set_opacity(self, layer: IconLayer, variable: tk.IntVar, value: str) -> None:
        layer.opacity = round(float(value))
        variable.set(layer.opacity)
        self._refresh_preview()

    def _move_layer(self, index: int, direction: int) -> None:
        destination = index + direction
        if not 0 <= destination < len(self.layers):
            return
        self.layers[index], self.layers[destination] = (
            self.layers[destination], self.layers[index]
        )
        self._render_layer_rows()
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        icon = compose_icon(self.layers)
        checker = Image.new("RGBA", icon.size, "#333446")
        draw = ImageDraw.Draw(checker)
        tile = 16
        for y in range(0, ICON_SIZE, tile):
            for x in range(0, ICON_SIZE, tile):
                if (x // tile + y // tile) % 2:
                    draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill="#505165")
        checker.alpha_composite(icon)
        self._preview_image = ImageTk.PhotoImage(
            checker.resize((256, 256), Image.Resampling.NEAREST)
        )
        self.preview.delete("all")
        self.preview.create_image(0, 0, anchor="nw", image=self._preview_image)

    def _export(self) -> None:
        png_path = filedialog.asksaveasfilename(
            title="Save icon spritesheet",
            initialfile="icon-maker.png",
            defaultextension=".png",
            filetypes=(("PNG image", "*.png"),),
        )
        if not png_path:
            return

        output = Path(png_path)
        plist_path = output.with_suffix(".plist")
        try:
            build_spritesheet(self.layers).save(output, format="PNG")
            plist_data = build_plist(self.layers, output.name)
            with plist_path.open("wb") as file:
                plistlib.dump(plist_data, file, fmt=plistlib.FMT_XML, sort_keys=False)
        except (OSError, ValueError) as error:
            messagebox.showerror("Export failed", str(error), parent=self.root)
            return

        self.status.configure(text=f"Saved {output.name} and {plist_path.name}.")
        messagebox.showinfo(
            "Export complete",
            f"Created:\n{output}\n{plist_path}",
            parent=self.root,
        )


def main() -> None:
    root = tk.Tk()
    IconMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

"""Color palettes, theme styling, and symbols for Rich console."""

from rich.theme import Theme

# Harmonious modern palette (Slate, Emerald, Amber, Rose)
CUSTOM_THEME = Theme(
    {
        "primary": "bold cyan",
        "secondary": "bold bright_blue",
        "accent": "bold spring_green3",
        "highlight": "bold gold3",
        "warning": "bold yellow",
        "danger": "bold red",
        "success": "bold green",
        "muted": "grey62",
        "card_border": "cyan",
        "admin_badge": "bold black on yellow",
        "adopter_badge": "bold black on cyan",
    }
)

BANNER_ART = r"""
 [bold cyan]  _____                 _    _                            [/]
 [bold cyan] |  __ \               | |  | |                           [/]
 [bold bright_cyan] | |__) | __ ___      _| |__| | __ ___   _____ _ __       [/]
 [bold bright_cyan] |  ___/ _` \ \ /\ / /  __  |/ _` \ \ / / _ \ '_ \      [/]
 [bold #48cae4] | |  | (_| |\ V  V /| |  | | (_| |\ V /  __/ | | |     [/]
 [bold #48cae4] |_|   \__,_| \_/\_/ |_|  |_|\__,_| \_/ \___|_| |_|     [/]
 [italic #90e0ef]      ✦  Pet Adoption Center & Rescue Shelter  ✦          [/]
"""

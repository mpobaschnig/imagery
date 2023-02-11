# prompt_ideas_manager.py
#
# Copyright 2023 Martin Pobaschnig
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as i18n
from typing import Dict, List

# Many ideas from:
# https://github.com/divamgupta/diffusionbee-stable-diffusion-ui/blob/master/electron_app/src/modifiers.json
prompt_idea_categories: Dict[str, List[str]] = {
    i18n("Drawing Style"): [
        "Children's Drawing",
        "Detailed and Intricate",
        "Doodle",
        "Sketch"
    ],
    i18n("Visual Style"): [
        "2D",
        "3D",
        "8-bit",
        "16-bit",
        "Anime",
        "CGI",
        "Cartoon",
        "Digital Art",
        "Fantasy",
        "Impressionistic",
        "Manga",
        "Modern Art",
        "Mosaic",
        "Photo",
        "Realistic",
        "Surrealistic"
    ],
    i18n("Pen"): [
        "Chalk",
        "Colored Pencil",
        "Graphite",
        "Ink",
        "Oil Paint",
        "Pastel Art"
    ],
    i18n("Camera"): [
        "Aerial View",
        "Cinematic",
        "Close-Up",
        "Dramatic",
        "Film Grain",
        "Fisheye Lens",
        "HD",
        "Landscape",
        "Polaroid",
        "Photoshoot",
        "Portrait",
        "Vintage",
        "War Photography"
    ],
    i18n("Color"): [
        "Beautiful Lighting",
        "Cold Color Palette",
        "Colorful",
        "Dynamic Lighting",
        "Synthwave",
        "Warm Color Palette"
    ],
    i18n("Emotions"): [
        "Angry",
        "Bitter",
        "Disgusted",
        "Embarrased",
        "Evil",
        "Excited",
        "Fear",
        "Funny",
        "Happy",
        "Horrifying",
        "Lonely",
        "Sad",
        "Serene",
        "Surprised",
        "Melancholic"
    ],
    i18n("CGI Rendering"): [
        "3D Render",
        "Creature Design",
        "Detailed Render",
        "Environment Design",
        "Global Illumination",
        "Subsurface Scattering"
    ]
}

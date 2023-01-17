# outpainting.py
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

from gi.repository import Gtk, GLib, Adw, Gio
from gettext import gettext as i18n

import os
import logging
from enum import Enum


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/outpainting_page.ui')
class OutpaintingPage(Gtk.Box):
    __gtype_name__ = "OutpaintingPage"

    def __init__(self):
        """Outpainting Page widget"""
        super().__init__()

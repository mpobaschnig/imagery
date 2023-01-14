# text_to_image_page.py
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
from typing import Optional

import os
import logging
from enum import Enum

from .downloader import Downloader


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/text_to_image_page.ui')
class TextToImagePage(Gtk.Box):
    __gtype_name__ = "TextToImagePage"

    def __init__(self):
        """Text to Image Page widget"""
        super().__init__()

    _progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _download_model_button: Gtk.Button = Gtk.Template.Child()
    _model_license_hint_label: Gtk.Label = Gtk.Template.Child()

    _stack: Gtk.Stack = Gtk.Template.Child()

    _downloader: Optional[Downloader] = None

    def __init__(self):
        """Start Page widget"""
        super().__init__()

        path = os.path.join(GLib.get_user_data_dir(),
                            "v2-1_768-ema-pruned.ckpt")

        if os.path.exists(path) and os.path.isfile(path):
            self._stack.set_visible_child_name("main")
            return
        
        url = "https://huggingface.co/stabilityai/stable-diffusion-2-1/resolve/main/v2-1_768-ema-pruned.ckpt"

        self._downloader: Downloader = Downloader(path=path,
                                                  url=url,
                                                  download_model_button=self._download_model_button,
                                                  model_license_hint_label=self._model_license_hint_label,
                                                  progress_bar=self._progress_bar)

    @Gtk.Template.Callback()
    def _on_download_model_button_clicked(self, _button):
        if self._downloader.is_finished():
            self._stack.set_visible_child_name("main")
        else:
            self._downloader.download()

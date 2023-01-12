# window.py
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


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/window.ui')
class ImageryWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ImageryWindow'

    stack: Gtk.Stack = Gtk.Template.Child()
    run_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_start()

    @Gtk.Template.Callback()
    def _on_run_button_clicked(self, _button):
        pass

    @Gtk.Template.Callback()
    def _on_save_button_clicked(self, _button):
        pass

    def _init_start(self) -> None:
        model_path = os.path.join(GLib.get_user_data_dir(),
                                  "v2-1_768-ema-pruned.ckpt")

        if os.path.exists(model_path) and os.path.isfile(model_path):
            logging.debug(f"Model exists at path: {model_path}")
            self.stack.set_visible_child_name("text_to_image")
        else:
            logging.debug(f"Model does not exist at path: {model_path}")
            self.stack.set_visible_child_name("start")

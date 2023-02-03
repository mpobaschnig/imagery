# start_page.py
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

import logging
import os
from enum import Enum
from gettext import gettext as i18n
from typing import Optional

from gi.repository import GObject, Gio, GLib, Gtk

from .download_manager import DownloadManager
from .model_files import sd15_files, sd15_folder


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/start_page.ui')
class StartPage(Gtk.Box):
    __gtype_name__ = "StartPage"

    __gsignals__ = {
        "finished": (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    _progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _download_model_button: Gtk.Button = Gtk.Template.Child()
    _cancel_download_button: Gtk.Button = Gtk.Template.Child()
    _continue_button: Gtk.Button = Gtk.Template.Child()
    _model_license_hint_label: Gtk.Label = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self._download_manager: DownloadManager = DownloadManager(sd15_files)

        self._download_manager.connect("reset", self._reset)
        self._download_manager.connect("update", self._update)
        self._download_manager.connect("cancelled", self._cancelled)
        self._download_manager.connect("finished", self._finished)

    def _reset(self, download_manager: DownloadManager):
        self._progress_bar.set_show_text(i18n("Initializing..."))
        self._progress_bar.set_fraction(0.0)
        self._progress_bar.set_visible(True)

    def _update(self,
                _download_manager: DownloadManager,
                fraction: float,
                current_downloaded: int,
                total_size: int,
                unit: str,
                current_index: int,
                total_files: int):
        self._progress_bar.set_text(i18n(
            f"{current_downloaded} {unit} / {total_size} {unit} - ({current_index} of {total_files})"
        ))
        self._progress_bar.set_fraction(fraction)

    def _cancelled(self, download_manager: DownloadManager):
        self._progress_bar.set_visible(False)
        self._download_model_button.set_visible(True)
        self._cancel_download_button.set_visible(False)
        self._model_license_hint_label.set_visible(True)

    def _finished(self, download_manager: DownloadManager):
        self._progress_bar.set_fraction(100)
        self._progress_bar.set_text(i18n("Download finished."))
        self._continue_button.set_visible(True)
        self._cancel_download_button.set_visible(False)

    @Gtk.Template.Callback()
    def _on_download_model_button_clicked(self, _button):
        self._cancel_download_button.set_visible(True)
        self._download_model_button.set_visible(False)

        self._model_license_hint_label.set_visible(False)

        self._download_manager.start()

    @Gtk.Template.Callback()
    def _on_cancel_download_button_clicked(self, _button):
        self._download_manager.cancel()

    @Gtk.Template.Callback()
    def _on_continue_button_clicked(self, _button):
        self.emit("finished")

    def all_files_available(self) -> bool:
        for file in sd15_files:
            if file.exists() is False:
                return False

        return True

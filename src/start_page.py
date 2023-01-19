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

from gi.repository import Gio, GLib, Gtk


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/start_page.ui')
class StartPage(Gtk.Box):
    class DownloadState(Enum):
        DOWNLOAD = 0
        CANCEL = 1

    __gtype_name__ = "StartPage"

    _progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _download_model_button: Gtk.Button = Gtk.Template.Child()
    _model_license_hint_label: Gtk.Label = Gtk.Template.Child()

    _download_state: DownloadState = DownloadState.DOWNLOAD
    _download_cancellable: Optional[Gio.Cancellable] = None

    @Gtk.Template.Callback()
    def _on_download_model_button_clicked(self, _button):
        if self._download_state == self.DownloadState.CANCEL:
            self._download_cancellable.cancel()
            self._toggle_download_state()
            return

        download_path = os.path.join(GLib.get_user_data_dir(),
                                     "v2-1_768-ema-pruned.ckpt")
        #pylint: disable-next=line-too-long
        download_uri = "https://huggingface.co/stabilityai/stable-diffusion-2-1/resolve/main/v2-1_768-ema-pruned.ckpt"

        model_uri_file: Gio.File = Gio.File.new_for_uri(download_uri)
        model_file = Gio.File.new_for_path(download_path)
        self._download_cancellable = Gio.Cancellable.new()
        model_uri_file.copy_async(model_file,
                                  Gio.FileCopyFlags.OVERWRITE,
                                  GLib.PRIORITY_DEFAULT, self._download_cancellable,
                                  self._on_download_progress_cb, (),
                                  self._on_download_finished_cb, None)

        self._toggle_download_state()

    def _on_download_progress_cb(self, current_num_bytes, total_num_bytes):
        fraction = current_num_bytes / total_num_bytes
        self._progress_bar.set_fraction(fraction)

        curr_gib = current_num_bytes / 1024 / 1024 / 1024
        total_gib = total_num_bytes / 1024 / 1024 / 1024
        self._progress_bar.set_text(
            f"{round(curr_gib,1)} GiB / {round(total_gib, 1)} GiB"
        )

    def _toggle_download_state(self):
        if self._download_state == self.DownloadState.DOWNLOAD:
            self._download_model_button.remove_css_class("suggested-action")
            self._download_model_button.add_css_class("destructive-action")
            self._download_model_button.set_label(i18n("Cancel"))

            self._download_state = self.DownloadState.CANCEL

            self._progress_bar.set_text(i18n("Initializing..."))
            self._progress_bar.set_show_text(True)
            self._progress_bar.set_fraction(0.0)
            self._progress_bar.set_visible(True)

            self._model_license_hint_label.set_visible(False)
        else:
            self._download_model_button.remove_css_class("destructive-action")
            self._download_model_button.add_css_class("suggested-action")
            self._download_model_button.set_label(i18n("Download Model"))

            self._download_state = self.DownloadState.DOWNLOAD

            self._progress_bar.set_visible(False)

            self._model_license_hint_label.set_visible(True)

    def _on_download_finished_cb(self, file, result, user_data):
        try:
            file.copy_finish(result)
        except GLib.Error as error:
            logging.error(error)

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

from gi.repository import Gtk, GLib, Adw, Gio
from gettext import gettext as i18n

import os
import logging
from enum import Enum


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/start_page.ui')
class StartPage(Gtk.Box):
    class DownloadState(Enum):
        Download = 0,
        Cancel = 1,

    __gtype_name__ = "StartPage"

    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    download_model_button: Gtk.Button = Gtk.Template.Child()
    model_license_hint_label: Gtk.Label = Gtk.Template.Child()

    download_state: DownloadState = DownloadState.Download

    def __init__(self):
        """Start Page widget"""
        super().__init__()

    @Gtk.Template.Callback()
    def _on_download_model_button_clicked(self, _button):
        if self.download_state == self.DownloadState.Cancel:
            self.download_cancellable.cancel()
            self._toggle_download_state()
            return

        download_path = os.path.join(GLib.get_user_data_dir(),
                                     "v2-1_768-ema-pruned.ckpt")
        download_uri = "https://huggingface.co/stabilityai/stable-diffusion-2-1/resolve/main/v2-1_768-ema-pruned.ckpt"

        model_uri_file: Gio.File = Gio.File.new_for_uri(download_uri)
        model_file = Gio.File.new_for_path(download_path)
        self.download_cancellable = Gio.Cancellable.new()
        model_uri_file.copy_async(model_file,
                                  Gio.FileCopyFlags.OVERWRITE,
                                  GLib.PRIORITY_DEFAULT, self.download_cancellable,
                                  self._on_download_progress_cb, (),
                                  self._on_download_finished_cb, None)

        self._toggle_download_state()

    def _on_download_progress_cb(self, current_num_bytes, total_num_bytes):
        fraction = current_num_bytes / total_num_bytes
        self.progress_bar.set_fraction(fraction)

        curr_gib = current_num_bytes / 1024 / 1024 / 1024
        total_gib = total_num_bytes / 1024 / 1024 / 1024
        self.progress_bar.set_text(
            f"{round(curr_gib,1)} GiB / {round(total_gib, 1)} GiB"
        )

    def _toggle_download_state(self):
        if self.download_state == self.DownloadState.Download:
            self.download_model_button.remove_css_class("suggested-action")
            self.download_model_button.add_css_class("destructive-action")
            self.download_model_button.set_label(i18n("Cancel"))

            self.download_state = self.DownloadState.Cancel

            self.progress_bar.set_text(i18n("Initializing..."))
            self.progress_bar.set_show_text(True)
            self.progress_bar.set_fraction(0.0)
            self.progress_bar.set_visible(True)

            self.model_license_hint_label.set_visible(False)
        else:
            self.download_model_button.remove_css_class("destructive-action")
            self.download_model_button.add_css_class("suggested-action")
            self.download_model_button.set_label(i18n("Download Model"))

            self.download_state = self.DownloadState.Download

            self.progress_bar.set_visible(False)

            self.model_license_hint_label.set_visible(True)

    def _on_download_finished_cb(self, file, result, user_data):
        try:
            file.copy_finish(result)
        except GLib.Error as e:
            logging.error(e)

# downloader.py
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

import hashlib
import logging
from enum import Enum


class Downloader:
    class DownloadState(Enum):
        Start = 0,
        Download = 1,
        Continue = 2,
        SHA_MISMATCH = 3,

    _url: Optional[str] = None
    _path: Optional[str] = None
    _sha256: Optional[str] = None

    _progress_bar: Optional[Gtk.ProgressBar] = None
    _download_model_button: Optional[Gtk.Button] = None
    _model_license_hint_label: Optional[Gtk.Label] = None

    _download_state: DownloadState = DownloadState.Start
    _download_cancellable: Optional[Gio.Cancellable] = None

    def __init__(self,
                 path: str,
                 url: str,
                 sha256: str,
                 download_model_button: Gtk.Button,
                 model_license_hint_label: Gtk.Label,
                 progress_bar: Gtk.ProgressBar):

        self._path = path
        self._url = url
        self._sha256 = sha256
        self._progress_bar = progress_bar
        self._download_model_button = download_model_button
        self._model_license_hint_label = model_license_hint_label

    def download(self) -> None:
        if self.download_state == self.DownloadState.Start or \
                self.download_state == self.DownloadState.SHA_MISMATCH:
            self._download_cancellable = Gio.Cancellable.new()
            model_uri_file: Gio.File = Gio.File.new_for_uri(self._url)
            model_file = Gio.File.new_for_path(self._path)
            model_uri_file.copy_async(model_file,
                                      Gio.FileCopyFlags.OVERWRITE,
                                      GLib.PRIORITY_DEFAULT,
                                      self._download_cancellable,
                                      self._progress_cb, (),
                                      self._finished_cb, None)

            self.download_state = self.DownloadState.Download
        elif self.download_state == self.DownloadState.Download:
            self.cancel_download()
            self.download_state = self.DownloadState.Start

    def cancel_download(self):
        self._download_cancellable.cancel()

    def _progress_cb(self, current_num_bytes, total_num_bytes):
        fraction = current_num_bytes / total_num_bytes
        self._progress_bar.set_fraction(fraction)

        curr = current_num_bytes / 1024 / 1024
        total = total_num_bytes / 1024 / 1024
        unit = "MiB"
        if total_num_bytes > 1073741824:
            curr /= 1024
            total /= 1024
            unit = "GiB"

        self._progress_bar.set_text(
            f"{round(curr,1)} {unit} / {round(total, 1)} {unit}"
        )

    def _finished_cb(self, file, result, on_user):
        try:
            file.copy_finish(result)
            if not self._is_sha_matching():
                self.download_state = self.download_state.SHA_MISMATCH
            else:
                self.download_state = self.DownloadState.Continue
        except GLib.Error as e:
            logging.error(e)

    def is_finished(self) -> bool:
        if self.download_state == self.DownloadState.Continue:
            return True
        else:
            return False

    @property
    def download_state(self) -> DownloadState:
        return self._download_state

    @download_state.setter
    def download_state(self, new_download_state: DownloadState) -> None:
        self._download_state = new_download_state

        if new_download_state == self.DownloadState.Start:
            self._download_model_button.remove_css_class("destructive-action")
            self._download_model_button.add_css_class("suggested-action")
            self._download_model_button.set_label(i18n("Download Model"))

            self._progress_bar.set_visible(False)

            self._model_license_hint_label.set_visible(True)
        elif new_download_state == self.DownloadState.Download:
            self._download_model_button.remove_css_class("suggested-action")
            self._download_model_button.add_css_class("destructive-action")
            self._download_model_button.set_label(i18n("Cancel"))

            self._progress_bar.set_text(i18n("Initializing..."))
            self._progress_bar.set_show_text(True)
            self._progress_bar.set_fraction(0.0)
            self._progress_bar.set_visible(True)

            self._model_license_hint_label.set_visible(False)
        elif new_download_state == self.DownloadState.Continue:
            self._download_model_button.add_css_class("suggested-action")
            self._download_model_button.set_label(i18n("Continue"))

            self._progress_bar.set_text(i18n("Download finished"))

            self._model_license_hint_label.set_visible(False)
        elif new_download_state == self.download_state.SHA_MISMATCH:
            self._download_model_button.remove_css_class("destructive-action")
            self._download_model_button.add_css_class("suggested-action")
            self._download_model_button.set_label(i18n("Download Again"))

            self._progress_bar.set_text(i18n("SHA256 Mismatch"))
            self._progress_bar.add_css_class("error")

            self._model_license_hint_label.set_visible(True)

    def _is_sha_matching(self) -> bool:
        buffer_size = 65536

        sha256 = hashlib.sha256()

        self._progress_bar.set_text(i18n("Verifying hashes..."))

        with open(self._path, "rb") as f:
            while (data := f.read(buffer_size)):
                sha256.update(data)

        sha256_hexvalue = sha256.hexdigest()

        logging.info(
            f"Downloaded files has sha256: {sha256_hexvalue}, should be: {self._sha256}"
        )

        return sha256_hexvalue == self._sha256

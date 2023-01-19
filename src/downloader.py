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

import hashlib
import logging
import os
from enum import Enum
from gettext import gettext as i18n
from pathlib import Path
from typing import List, Optional

from gi.repository import Gio, GLib, GObject, Gtk

from .file import File

# pylint: disable-next=too-many-instance-attributes


class Downloader(GObject.Object):
    class DownloadState(Enum):
        """The state of the downloader.
        """
        START = 0
        DOWNLOAD = 1
        CONTINUE = 2
        SHA_MISMATCH = 3

    _current_i: int = 0
    _files: List[File] = []

    _task: Optional[Gio.Task] = None

    _progress_bar: Gtk.ProgressBar = None
    _download_model_button: Gtk.Button
    _model_license_hint_label: Gtk.Label = None

    _download_state: DownloadState = DownloadState.START
    _download_cancellable: Optional[Gio.Cancellable] = None
    _download_cancelled: bool = False

    def __init__(self,
                 files: List[File],
                 download_model_button: Gtk.Button,
                 model_license_hint_label: Gtk.Label,
                 progress_bar: Gtk.ProgressBar):
        super().__init__()

        self._files = files
        self._progress_bar = progress_bar
        self._download_model_button = download_model_button
        self._model_license_hint_label = model_license_hint_label

    def _run(self, _task, _source_object, _task_data, _cancellable):
        self._download_file()

    def download(self) -> None:
        if self.download_state in (self.DownloadState.START,
                                   self.DownloadState.SHA_MISMATCH):
            self._current_i = 0
            file = self._files[self._current_i]

            path: Path = Path(file.path)
            if not Path.exists(path.parent):
                Path.mkdir(path.parent, parents=True)

            self.download_state = self.DownloadState.DOWNLOAD

            self._task: Gio.Task = Gio.Task.new(self,
                                                None,
                                                None,
                                                None)

            self._task.run_in_thread(self._run)
        elif self.download_state == self.DownloadState.DOWNLOAD:
            self.cancel_download()
            self.download_state = self.DownloadState.START

    def _download_file(self):
        self._progress_bar.set_fraction(0)

        if self._download_cancelled:
            return

        if self._current_i >= len(self._files):
            self._verify_hashes()
            return

        file: File = self._files[self._current_i]

        if self._does_file_exist(file, self._current_i):
            self._current_i += 1
            self._download_file()
            return

        self._download_cancellable = Gio.Cancellable.new()
        model_uri_file: Gio.File = Gio.File.new_for_uri(file.url)
        model_file = Gio.File.new_for_path(file.path)
        model_uri_file.copy_async(model_file,
                                  Gio.FileCopyFlags.OVERWRITE,
                                  GLib.PRIORITY_DEFAULT,
                                  self._download_cancellable,
                                  self._progress_cb, (self._current_i,),
                                  self._finished_cb, (self._current_i,))

    def cancel_download(self):
        logging.info("Cancelled download")
        self._download_cancelled = True
        if self._download_cancellable is not None:
            self._download_cancellable.cancel()

    def _progress_cb(self, current_num_bytes, total_num_bytes, current_i):
        fraction = current_num_bytes / total_num_bytes
        self._progress_bar.set_fraction(fraction)

        curr = current_num_bytes / 1024
        total = total_num_bytes / 1024
        unit = "KiB"
        if total_num_bytes > 1048576:
            curr /= 1024
            total /= 1024
            unit = "MiB"
        if total_num_bytes > 1073741824:
            curr /= 1024
            total /= 1024
            unit = "GiB"

        curr = round(curr, 1)
        total = round(total, 1)

        self._progress_bar.set_text(i18n(
            f"{curr} {unit} / {total} {unit} - ({current_i + 1} of {len(self._files)})"
        ))

    def _finished_cb(self, file, result, user_data):
        logging.info("Finished downloading file.")

        try:
            file.copy_finish(result)
        except GLib.Error as error:
            logging.error(error)

        self._task = Gio.Task.new(self,
                                  self._download_cancellable,
                                  None,
                                  None)

        if self._current_i == len(self._files):
            self._task.run_in_thread(self._verify_hashes)
            return

        self._current_i += 1
        if self._current_i >= len(self._files):
            self._task.run_in_thread(self._verify_hashes)
            return
        file = self._files[self._current_i]

        path: Path = Path(file.path)
        if not Path.exists(path.parent):
            Path.mkdir(path.parent, parents=True)

        self._download_file()

    def is_finished(self) -> bool:
        return self.download_state == self.DownloadState.CONTINUE

    @property
    def download_state(self) -> DownloadState:
        return self._download_state

    @download_state.setter
    def download_state(self, new_download_state: DownloadState) -> None:
        self._download_state = new_download_state

        if new_download_state == self.DownloadState.START:
            self._download_model_button.remove_css_class("destructive-action")
            self._download_model_button.add_css_class("suggested-action")
            self._download_model_button.set_label(i18n("Download Model"))

            self._progress_bar.set_visible(False)

            self._model_license_hint_label.set_visible(True)
        elif new_download_state == self.DownloadState.DOWNLOAD:
            self._download_model_button.remove_css_class("suggested-action")
            self._download_model_button.add_css_class("destructive-action")
            self._download_model_button.set_label(i18n("Cancel"))

            self._download_cancelled = False

            self._progress_bar.set_text(i18n("Initializing..."))
            self._progress_bar.set_show_text(True)
            self._progress_bar.set_fraction(0.0)
            self._progress_bar.set_visible(True)

            self._model_license_hint_label.set_visible(False)
        elif new_download_state == self.DownloadState.CONTINUE:
            self._download_model_button.add_css_class("suggested-action")
            self._download_model_button.set_label(i18n("Continue"))

            self._progress_bar.set_text(i18n("Download finished"))

            self._model_license_hint_label.set_visible(False)
        elif new_download_state == self.DownloadState.SHA_MISMATCH:
            self._download_model_button.remove_css_class("destructive-action")
            self._download_model_button.add_css_class("suggested-action")
            self._download_model_button.set_label(i18n("Download Again"))

            self._progress_bar.set_text(i18n("SHA256 Mismatch"))
            self._progress_bar.add_css_class("error")

            self._model_license_hint_label.set_visible(True)

    def _does_file_exist(self, file: File, current_i: int) -> bool:
        path: Path = Path(file.path)
        logging.info("Checking if file %s exists... (%s of %s)",
                     path.name,
                     current_i + 1,
                     len(self._files))

        self._progress_bar.set_text(i18n(
            f"Checking if file {path.name} exists... \
                ({current_i + 1} of {len(self._files)})",
        ))
        self._progress_bar.set_fraction((current_i + 1) / len(self._files))

        sha256 = hashlib.sha256()

        if not os.path.exists(file.path) or not os.path.isfile(file.path):
            logging.info("File %s does not exist, starting download.",
                         file.path)
            return False

        buffer_size = 65536

        with open(file.path, "rb") as open_file:
            while (data := open_file.read(buffer_size)):
                if self._download_cancelled:
                    return False
                sha256.update(data)

        sha256_hexvalue = sha256.hexdigest()

        if sha256_hexvalue != file.sha256:
            logging.info("Existing file has sha256: %s, should be: %s",
                         sha256_hexvalue,
                         file.sha256)
            return False

        return True

    def _verify_hashes(self) -> None:
        logging.info("Verifying hashes...")

        buffer_size = 65536

        for (i, file) in enumerate(self._files):
            logging.info("Verifying hashes of %s", file.path)
            self._progress_bar.set_text(i18n(
                f"Verifying hashes... ({i + 1} of {len(self._files)})"
            ))

            sha256 = hashlib.sha256()

            if not os.path.exists(file.path) or not os.path.isfile(file.path):
                logging.error(
                    "Could not verify hash: File does not exist."
                )
                self.download_state = self.DownloadState.SHA_MISMATCH
                break

            with open(file.path, "rb") as open_file:
                while (data := open_file.read(buffer_size)):
                    if self._download_cancelled:
                        return
                    sha256.update(data)

            sha256_hexvalue = sha256.hexdigest()

            if sha256_hexvalue != file.sha256:
                logging.info("Downloaded files has sha256: %s, should be: %s",
                             sha256_hexvalue,
                             file.sha256)
                self.download_state = self.DownloadState.SHA_MISMATCH
                break

            self._progress_bar.set_fraction((i + 1) / (len(self._files)))

        self.download_state = self.DownloadState.CONTINUE

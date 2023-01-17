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

from gi.repository import Gtk, GLib, Adw, Gio, GObject
from gettext import gettext as i18n
from typing import List, Optional

from pathlib import Path
import hashlib
import logging
from enum import Enum
import os
from threading import Thread
import time

from .file import File


class Downloader(GObject.Object):
    class DownloadState(Enum):
        Start = 0,
        Download = 1,
        Continue = 2,
        SHA_MISMATCH = 3,

    _currnt_index: int = 0
    _files: List[File] = []

    _task: Optional[Gio.Task] = None

    _progress_bar: Optional[Gtk.ProgressBar] = None
    _download_model_button: Optional[Gtk.Button] = None
    _model_license_hint_label: Optional[Gtk.Label] = None

    _download_state: DownloadState = DownloadState.Start
    _download_cancellable: Optional[Gio.Cancellable] = None
    _download_cancelled: bool = False

    def __init__(self,
                 files,
                 download_model_button: Gtk.Button,
                 model_license_hint_label: Gtk.Label,
                 progress_bar: Gtk.ProgressBar):
        super().__init__()

        self._files = files
        self._progress_bar = progress_bar
        self._download_model_button = download_model_button
        self._model_license_hint_label = model_license_hint_label

    def _run(self, task, source_object, task_data, cancellable):
        self._download_file()

    def download(self) -> None:
        if self.download_state == self.DownloadState.Start or \
                self.download_state == self.DownloadState.SHA_MISMATCH:
            self._current_i = 0
            file = self._files[self._current_i]

            p: Path = Path(file.path)
            if not Path.exists(p.parent):
                Path.mkdir(p.parent, parents=True)

            self.download_state = self.DownloadState.Download

            self._task: Gio.Task = Gio.Task.new(self,
                                                None,
                                                None,
                                                None)

            self._task.run_in_thread(self._run)
        elif self.download_state == self.DownloadState.Download:
            self.cancel_download()
            self.download_state = self.DownloadState.Start

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

        self._progress_bar.set_text(i18n(
            f"{round(curr,1)} {unit} / {round(total, 1)} {unit} - ({current_i + 1} of {len(self._files)})"
        ))

    def _finished_cb(self, file, result, user_data):
        logging.info("Finished downloading file.")

        try:
            file.copy_finish(result)
        except GLib.Error as e:
            logging.error(e)

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

        p: Path = Path(file.path)
        if not Path.exists(p.parent):
            Path.mkdir(p.parent, parents=True)

        self._download_file()

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

            self._download_cancelled = False

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

    def _does_file_exist(self, file: File, current_i: int) -> bool:
        p: Path = Path(file.path)
        logging.info(
            f"Checking if file {p.name} exists... ({current_i + 1} of {len(self._files)})"
        )

        self._progress_bar.set_text(i18n(
            f"Checking if file {p.name} exists... ({current_i + 1} of {len(self._files)})"
        ))

        sha256 = hashlib.sha256()

        if not os.path.exists(file.path) or not os.path.isfile(file.path):
            logging.info(
                f"File {file.path} does not exist, starting download."
            )
            return False

        buffer_size = 65536

        with open(file.path, "rb") as f:
            while (data := f.read(buffer_size)):
                if self._download_cancelled:
                    return False
                sha256.update(data)

        sha256_hexvalue = sha256.hexdigest()

        if sha256_hexvalue != file.sha256:
            logging.info(
                f"Existing file has sha256: {sha256_hexvalue}, should be: {file._sha256}"
            )
            return False

        return True

    def _verify_hashes(self) -> None:
        logging.info("Verifying hashes...")

        buffer_size = 65536

        for (i, file) in enumerate(self._files):
            logging.info(f"Verifying hashes of {file.path}")
            self._progress_bar.set_text(i18n(
                f"Verifying hashes... ({i + 1} of {len(self._files)})"
            ))

            sha256 = hashlib.sha256()

            if not os.path.exists(file.path) or not os.path.isfile(file.path):
                logging.error(
                    f"Could not verify hash: File does not exist."
                )
                self.download_state = self.DownloadState.SHA_MISMATCH
                break

            with open(file.path, "rb") as f:
                while (data := f.read(buffer_size)):
                    if self._download_cancelled:
                        return
                    sha256.update(data)

            sha256_hexvalue = sha256.hexdigest()

            if sha256_hexvalue != file.sha256:
                logging.info(
                    f"Downloaded files has sha256: {sha256_hexvalue}, should be: {self._sha256}"
                )
                self.download_state = self.DownloadState.SHA_MISMATCH
                break

        self.download_state = self.DownloadState.Continue

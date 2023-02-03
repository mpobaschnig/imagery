# downloader_manager.py
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
from typing import List, Optional

from gi.repository import Gio, GLib, GObject

from .file import File


class DownloadManager(GObject.Object):
    __gsignals__ = {
        "reset": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "update": (GObject.SignalFlags.RUN_FIRST,
                   None,
                   (float, int, int, str, int, int,)),
        "cancelled": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "finished": (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self,
                 files: List[File]):
        super().__init__()

        self._files = files

        self._running: bool = False
        self._current_i: int = 0
        self._task: Optional[Gio.Task] = None
        self._download_cancellable: Optional[Gio.Cancellable] = None

    def _start_download(self, _task, _source_object, _task_data, _cancellable):
        self._running = True
        self._download_file()

    def _download_file(self):
        if self._running is False:
            return

        if self._current_i >= len(self._files):
            self.emit("finished")
            return

        file: File = self._files[self._current_i]

        if file.exists():
            logging.info("File %s exists, skipping.", file.path)
            self._current_i += 1
            self._download_file()
            return

        file.create_path()

        logging.info("Downloading file %s...", file.path)

        self._download_cancellable = Gio.Cancellable.new()
        model_uri_file: Gio.File = Gio.File.new_for_uri(file.url)
        model_file = Gio.File.new_for_path(file.path)
        model_uri_file.copy_async(model_file,
                                  Gio.FileCopyFlags.OVERWRITE,
                                  GLib.PRIORITY_DEFAULT,
                                  self._download_cancellable,
                                  self._progress_cb, (self._current_i,),
                                  self._finished_cb, (self._current_i,))

    def _progress_cb(self, current_num_bytes, total_num_bytes, current_i):
        fraction = current_num_bytes / total_num_bytes

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

        self.emit("update",
                  fraction,
                  curr,
                  total,
                  unit,
                  current_i + 1,
                  len(self._files))

    def _finished_cb(self, file, result, _user_data):
        self._download_cancellable = None

        try:
            file.copy_finish(result)
        except GLib.Error as error:
            logging.error(error)

        self._current_i += 1

        self._download_file()

    def start(self):
        self.emit("reset")

        self._current_i = 0

        self._download_cancellable = Gio.Cancellable.new()
        self._task = Gio.Task.new(self,  # type: ignore
                                  self._download_cancellable,
                                  None,
                                  None)

        self._task.run_in_thread(self._start_download)  # type: ignore

    def cancel(self):
        self._running = False

        if self._download_cancellable:
            self._download_cancellable.cancel()

            file = self._files[self._current_i]
            file.remove()

        self.emit("cancelled")

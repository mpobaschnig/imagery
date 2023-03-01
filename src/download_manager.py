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

import hashlib
import logging
from pathlib import Path
from typing import List, Optional

from gi.repository import Gio, GLib, GObject

from .file import File
from .model_files import sd_files_size


class DownloadManager(GObject.Object):
    __gsignals__ = {
        "reset": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "verify": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "verify-progress": (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        "update": (GObject.SignalFlags.RUN_FIRST,
                   None,
                   (int, int,)),
        "cancelled": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "finished": (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self,
                 files: List[File]):
        super().__init__()

        self._files = files
        self._current_download_size: int = 0
        self._total_download_size: int = sd_files_size

        self._task: Optional[Gio.Task] = None
        self._task_cancellable: Gio.Cancellable = Gio.Cancellable()
        self._cancelled: bool = False

    def _start_download(self, _task, _source_object, _task_data, _cancellable):
        logging.info("Start downloading")
        self._current_download_size: int = 0

        download_queue: List[File] = []

        for file in self._files:
            if file.exists():
                path: Path = Path(file.path)
                current_size: int = 0
                buffer_size = 65536
                sha256 = hashlib.sha256()
                with open(path, "rb") as open_file:
                    while (data := open_file.read(buffer_size)):
                        if self._cancelled is True:
                            return

                        sha256.update(data)

                        current_size += buffer_size

                if file.sha256 == sha256.hexdigest():
                    self._total_download_size -= file.get_size()
                    continue

            download_queue.append(file)

        for file in download_queue:
            file.create_path()

            model_uri_file: Gio.File = Gio.File.new_for_uri(file.url)
            model_file = Gio.File.new_for_path(file.path)
            try:
                model_uri_file.copy(model_file,
                                    Gio.FileCopyFlags.OVERWRITE,
                                    _cancellable,
                                    self._progress_cb)
            except GLib.Error as err:
                logging.error(err.message)
                return

            self._current_download_size += file.get_size()

        self.emit("finished")

    def _progress_cb(self, current_num_bytes, _total_num_bytes):
        curr = (self._current_download_size + current_num_bytes) / 1024 / 1024
        total = self._total_download_size / 1024 / 1024

        self.emit("update",
                  curr,
                  total)

    def start(self):
        self._cancelled: bool = False
        self._task_cancellable.reset()

        self._task = Gio.Task.new(self,  # type: ignore
                                  self._task_cancellable,
                                  None,
                                  None)

        self._task.run_in_thread(self._start_download)  # type: ignore

    def cancel(self):
        self._cancelled = True

        self._task_cancellable.cancel()

        self.emit("cancelled")

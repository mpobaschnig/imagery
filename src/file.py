# file.py
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

import os
from pathlib import Path

from gi.repository import GObject


class File(GObject.Object):
    _url: str
    _sha256: str
    _path: str

    def __init__(self, url: str, path: str, sha256: str) -> None:
        super().__init__()

        self._url = url
        self._path = path
        self._sha256 = sha256

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url: str) -> None:
        self._url = url

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path: str) -> None:
        self._path = path

    @property
    def sha256(self):
        return self._sha256

    @sha256.setter
    def sha256(self, sha256: str) -> None:
        self._path = sha256

    def exists(self) -> bool:
        path: Path = Path(self.path)

        if not os.path.exists(path) or not os.path.isfile(path):
            return False

        return True

    def create_path(self):
        path: Path = Path(self.path)

        if not Path.exists(path.parent):
            Path.mkdir(path.parent, parents=True)

    def remove(self):
        path: Path = Path(self.path)

        if self.exists():
            path.unlink()

# settings_manager.py
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

from gi.repository import Gio

settings = Gio.Settings.new("io.github.mpobaschnig.Imagery")


def is_nsfw_allowed() -> bool:
    return settings.get_boolean("allow-nsfw")


def is_model_download_finished() -> bool:
    return settings.get_boolean("download-finished")


def set_model_download_finished(value: bool) -> bool:
    return settings.set_boolean("download-finished", value)

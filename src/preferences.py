# preferences.py
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

from gi.repository import Gtk, Gio, GObject, Adw


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/preferences.ui')
class Preferences(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesDialog"

    def __init__(self, window):
        super().__init__()

        self.window = window
        self.set_transient_for(window)

        action_group = Gio.SimpleActionGroup.new()
        settings = Gio.Settings.new("io.github.mpobaschnig.Imagery")

        allow_nsfw_action = settings.create_action("allow-nsfw")

        action_group.add_action(allow_nsfw_action)

        self.insert_action_group("prefs", action_group)
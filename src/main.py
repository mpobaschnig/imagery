# main.py
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
# pylint: disable=wrong-import-position
import logging
import sys

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gio, Gtk

from .mod import load_widgets
from .preferences import Preferences
from .window import ImageryWindow


class ImageryApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.mpobaschnig.Imagery',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.create_action('quit', self.quit, ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)

        logging.getLogger().setLevel(logging.INFO)

    def do_activate(self):  # pylint: disable=arguments-differ
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = ImageryWindow(application=self)
        win.present()

    def do_startup(self):  # pylint: disable=arguments-differ
        Adw.Application.do_startup(self)

        Gtk.Window.set_default_icon_name("io.github.mpobaschnig.Imagery")

        load_widgets()

    def on_about_action(self, _widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Imagery',
                                application_icon='io.github.mpobaschnig.Imagery',
                                developer_name='Martin Pobaschnig',
                                version='0.2.0',
                                developers=['Martin Pobaschnig'],
                                copyright='© 2023 Martin Pobaschnig')
        about.present()

    def on_preferences_action(self, _widget, _):
        """Callback for the app.preferences action."""
        Preferences(self.props.active_window).present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(_version):
    """The application's entry point."""
    app = ImageryApplication()
    return app.run(sys.argv)

# window.py
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

from enum import Enum
from gettext import gettext as i18n

from gi.repository import Adw, Gio, Gtk

from .model_files import all_files_available


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/window.ui')
class ImageryWindow(Adw.ApplicationWindow):
    class PageState(Enum):
        START = 0
        TEXT_TO_IMAGE = 1
        IMAGE_TO_IMAGE = 2

    __gtype_name__ = 'ImageryWindow'

    _stack: Gtk.Stack = Gtk.Template.Child()
    _menu_button_page: Gtk.MenuButton = Gtk.Template.Child()
    _page_state: PageState = PageState.START

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect("unrealize", self._on_window_close_cb, None)

        self.create_action('text_to_image', self._on_text_to_image_clicked)
        self.create_action('image_to_image', self._on_image_to_image_clicked)

        if all_files_available():
            self.page_state = self.PageState.TEXT_TO_IMAGE
            return

        self._stack.get_child_by_name("start").connect("finished",
                                                       self._start_finished)
        self.page_state = self.PageState.START

    def _start_finished(self, _object):
        self._menu_button_page.set_visible(True)
        self.page_state = self.PageState.TEXT_TO_IMAGE

    def create_action(self, name, callback, _shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)

    def _on_text_to_image_clicked(self, _widget, _):
        self.page_state = self.PageState.TEXT_TO_IMAGE

    def _on_image_to_image_clicked(self, _widget, _):
        self.page_state = self.PageState.IMAGE_TO_IMAGE

    @property
    def page_state(self) -> PageState:
        return self._page_state

    @page_state.setter
    def page_state(self, new_page_state: PageState) -> None:
        stack = self._stack

        self._page_state = new_page_state

        if new_page_state == self.PageState.START:
            self._menu_button_page.set_visible(False)
        elif new_page_state == self.PageState.TEXT_TO_IMAGE:
            stack.set_visible_child_name("text_to_image")
            self.set_menu_button_label(self.PageState.TEXT_TO_IMAGE)
        elif new_page_state == self.PageState.IMAGE_TO_IMAGE:
            stack.set_visible_child_name("image_to_image")
            self.set_menu_button_label(self.PageState.IMAGE_TO_IMAGE)

    def set_menu_button_label(self, new_page_state: PageState) -> None:
        menu_button_page = self._menu_button_page

        if new_page_state == self.PageState.TEXT_TO_IMAGE:
            menu_button_page.set_label(i18n("Text to Image"))
        elif new_page_state == self.PageState.IMAGE_TO_IMAGE:
            menu_button_page.set_label(i18n("Image to Image"))

    def _on_window_close_cb(self, window, user_data):
        self._stack.get_child_by_name("text_to_image").cleanup()
        self._stack.get_child_by_name("image_to_image").cleanup()

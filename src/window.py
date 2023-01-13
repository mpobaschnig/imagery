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

from gi.repository import Gtk, GLib, Adw, Gio
from gettext import gettext as i18n

import os
import logging
from enum import Enum


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/window.ui')
class ImageryWindow(Adw.ApplicationWindow):
    class PageState(Enum):
        START = 0,
        TEXT_TO_IMAGE = 1,
        IMAGE_TO_IMAGE = 2,
        UPSCALING = 3,
        INPAINTING = 4,
        OUTPAINTING = 5

    __gtype_name__ = 'ImageryWindow'

    _stack: Gtk.Stack = Gtk.Template.Child()
    _button_run: Gtk.Button = Gtk.Template.Child()
    _menu_button_page: Gtk.MenuButton = Gtk.Template.Child()
    _page_state: PageState = PageState.TEXT_TO_IMAGE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.create_action('text_to_image', self._on_text_to_image_clicked)
        self.create_action('image_to_image', self._on_image_to_image_clicked)
        self.create_action('upscaling', self._on_upscaling_clicked)
        self.create_action('inpainting', self._on_inpainting_clicked)
        self.create_action('outpainting', self._on_outpainting_clicked)

        self.page_state = self.PageState.TEXT_TO_IMAGE

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def _on_text_to_image_clicked(self, widget, _):
        self.page_state = self.PageState.TEXT_TO_IMAGE

    def _on_image_to_image_clicked(self, widget, _):
        self.page_state = self.PageState.IMAGE_TO_IMAGE

    def _on_upscaling_clicked(self, widget, _):
        self.page_state = self.PageState.UPSCALING

    def _on_inpainting_clicked(self, widget, _):
        self.page_state = self.PageState.INPAINTING

    def _on_outpainting_clicked(self, widget, _):
        self.page_state = self.PageState.OUTPAINTING

    @property
    def page_state(self) -> PageState:
        return self._page_state

    @page_state.setter
    def page_state(self, new_page_state: PageState) -> None:
        stack = self._stack
        menu_button_page = self._menu_button_page

        self._page_state = new_page_state

        if new_page_state == self.PageState.START:
            stack.set_visible_child_name("start")
            self.set_menu_button_label(self.PageState.TEXT_TO_IMAGE)
        elif new_page_state == self.PageState.TEXT_TO_IMAGE:
            stack.set_visible_child_name("text_to_image")
            self.set_menu_button_label(self.PageState.TEXT_TO_IMAGE)
        elif new_page_state == self.PageState.IMAGE_TO_IMAGE:
            stack.set_visible_child_name("image_to_image")
            self.set_menu_button_label(self.PageState.IMAGE_TO_IMAGE)
        elif new_page_state == self.PageState.UPSCALING:
            stack.set_visible_child_name("upscaling")
            self.set_menu_button_label(self.PageState.UPSCALING)
        elif new_page_state == self.PageState.INPAINTING:
            stack.set_visible_child_name("inpainting")
            self.set_menu_button_label(self.PageState.INPAINTING)
        elif new_page_state == self.PageState.OUTPAINTING:
            stack.set_visible_child_name("outpainting")
            self.set_menu_button_label(self.PageState.OUTPAINTING)

    def set_menu_button_label(self, new_page_state: PageState) -> None:
        menu_button_page = self._menu_button_page

        if new_page_state == self.PageState.TEXT_TO_IMAGE:
            menu_button_page.set_label(i18n("Text to Image"))
        elif new_page_state == self.PageState.IMAGE_TO_IMAGE:
            menu_button_page.set_label(i18n("Text to Image"))
        elif new_page_state == self.PageState.UPSCALING:
            menu_button_page.set_label(i18n("Upscaling"))
        elif new_page_state == self.PageState.INPAINTING:
            menu_button_page.set_label(i18n("Inpainting"))
        elif new_page_state == self.PageState.OUTPAINTING:
            menu_button_page.set_label(i18n("Outpainting"))

# text_to_image_page.py
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
import os
import time
from enum import Enum
from gettext import gettext as i18n
from typing import List

from gi.repository import Adw, Gio, GLib, Gtk

from .text_to_image_runner import TextToImageRunner
from .prompt_ideas import prompt_idea_categories


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/text_to_image_page.ui')
class TextToImagePage(Gtk.Box):
    class PageState(Enum):
        START = 0
        RUNNING = 1
        FINISHED = 2

    __gtype_name__ = "TextToImagePage"

    _settings_menu_button: Gtk.MenuButton = Gtk.Template.Child()
    _flow_box: Gtk.FlowBox = Gtk.Template.Child()
    _generating_progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _height_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _inference_steps_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _list_box: Gtk.ListBox = Gtk.Template.Child()
    _number_images_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _prompt_entry: Adw.EntryRow = Gtk.Template.Child()
    _run_button: Gtk.Button = Gtk.Template.Child()
    _scheduler_drop_down: Gtk.DropDown = Gtk.Template.Child()
    _width_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _cancel_run_button: Gtk.Button = Gtk.Template.Child()
    _spin_button: Gtk.Button = Gtk.Template.Child()
    _spinner: Gtk.Spinner = Gtk.Template.Child()
    _prompt_ideas_scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    _flow_box_scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    _prompt_ideas_box: Gtk.Box = Gtk.Template.Child()

    _flow_box_pictures: List[Gtk.Picture] = []

    def __init__(self, orientation=None, spacing=None):
        super().__init__(orientation, spacing)

        self._text_to_image_runner: TextToImageRunner = TextToImageRunner()

        self._text_to_image_runner.connect("update", self._update)
        self._text_to_image_runner.connect("finished", self._finished)
        self._text_to_image_runner.connect("cancelled", self._cancelled)

        self._fill_prompt_box()

        self.page_state: self.PageState = self.PageState.START

        self._t_previous: float = 0

    def _update(self, _: TextToImageRunner, step: int) -> None:
        t_now = time.time()
        t_diff = t_now - self._t_previous
        self._t_previous = t_now

        number_steps = int(self._inference_steps_spin_button.get_value())

        time_left = (number_steps - step) * t_diff

        minutes: int = int(time_left // 60)
        seconds: int = int(time_left % 60)

        if minutes == 0:
            text = i18n(f"~{seconds} s left...")
        else:
            text = i18n(f"~{minutes} min {seconds} s left...")

        self._generating_progress_bar.set_text(text)
        self._generating_progress_bar.set_fraction(step / number_steps)

    def _finished(self, _):
        n_images = int(self._number_images_spin_button.get_value())

        for i in range(n_images):
            self._add_image(i)

        self.page_state = self.PageState.FINISHED

    def _cancelled(self, _):
        self.page_state = self.PageState.START

    def _fill_prompt_box(self):
        def _append_text(button: Gtk.Button, entry: Adw.EntryRow) -> None:
            text: str = str(entry.get_text())
            idea: str = str(button.get_label())

            text = text.strip()

            if text == "":
                text = f"{idea}, "
            elif text.endswith(","):
                text += f" {idea}"
            else:
                text += f", {idea}"

            entry.set_text(text)

        box: Gtk.Box = self._prompt_ideas_box
        box.set_spacing(12)

        label: Gtk.Label = Gtk.Label()
        label.set_text(i18n("Here are some prompt ideas!"))
        label.add_css_class("title-2")
        box.append(label)

        for category, examples in prompt_idea_categories.items():
            label: Gtk.Label = Gtk.Label()
            label.set_text(category)
            label.set_halign(Gtk.Align.START)
            label.add_css_class("title-4")

            box.append(label)

            flow_box: Gtk.FlowBox = Gtk.FlowBox()
            flow_box.set_homogeneous(False)

            for example in examples:
                button: Gtk.Button = Gtk.Button()
                button.set_label(example)
                button.connect("clicked",
                               _append_text,
                               self._prompt_entry)
                flow_box.append(button)

            box.append(flow_box)

    @property
    def page_state(self) -> PageState:
        return self._page_state

    @page_state.setter
    def page_state(self, new_page_state: PageState) -> None:
        self._page_state = new_page_state

        if new_page_state == self.PageState.START:
            self._prompt_ideas_box.set_visible(True)
            self._prompt_ideas_scrolled_window.set_visible(True)

        if new_page_state in (self.PageState.START, self.PageState.RUNNING):
            for i, _ in enumerate(self._flow_box_pictures):
                self._flow_box.remove(self._flow_box_pictures[i])

            self._flow_box_pictures.clear()

        if new_page_state == self.PageState.FINISHED:
            self._flow_box_scrolled_window.set_visible(True)
            self._prompt_ideas_scrolled_window.set_visible(False)

        if new_page_state == self.PageState.RUNNING:
            self._spinner.set_spinning(True)
            self._spin_button.set_visible(True)

            self._run_button.set_visible(False)
            self._cancel_run_button.set_visible(True)
            self._settings_menu_button.set_sensitive(False)

            self._generating_progress_bar.set_text(i18n("Estimating time left..."))
            self._generating_progress_bar.set_show_text(True)
            self._generating_progress_bar.set_fraction(0.0)
            self._generating_progress_bar.set_visible(True)

            self._prompt_ideas_box.set_visible(False)
        else:
            self._spin_button.set_visible(False)
            self._spinner.set_spinning(False)

            self._run_button.set_visible(True)
            self._cancel_run_button.set_visible(False)
            self._settings_menu_button.set_sensitive(True)

            self._generating_progress_bar.set_visible(False)

    def _add_image(self, image_index: int) -> Gtk.Overlay:
        def image_button_clicked(button: Gtk.Button, image: int) -> None:
            def response_cb(dialog: Gtk.FileChooserNative,
                            response: int,
                            user_data: tuple) -> None:
                if response != Gtk.ResponseType.ACCEPT:
                    return

                def _copy_image_finished(file, result, user_data):
                    button = user_data[0]
                    button_spinner = user_data[1]

                    try:
                        file.copy_finish(result)
                    except GLib.Error as error:
                        logging.error(error)

                    button.set_icon_name("document-save-symbolic")
                    button_spinner.set_spinning(False)

                dest_file: Gio.File = dialog.get_file()
                curr_file: Gio.File = Gio.File.new_for_path(
                    os.path.join(GLib.get_user_cache_dir(),
                                 f"t2i_image_{image}.png")
                )

                button: Gtk.Button = user_data[0]
                button_spinner: Gtk.Spinner = user_data[1]

                button.set_child(button_spinner)
                button_spinner.set_spinning(True)

                curr_file.copy_async(dest_file,
                                     Gio.FileCopyFlags.OVERWRITE,
                                     GLib.PRIORITY_DEFAULT,
                                     None,
                                     None, (),
                                     _copy_image_finished, (button, button_spinner,))

            file_chooser_native = Gtk.FileChooserNative()
            file_chooser_native.set_accept_label(i18n("Save Image"))
            file_chooser_native.set_action(Gtk.FileChooserAction.SAVE)
            file_chooser_native.connect("response", response_cb,
                                        (button, button_spinner))
            file_chooser_native.show()

        overlay = Gtk.Overlay()
        overlay.set_halign(Gtk.Align.CENTER)

        button = Gtk.Button()
        button.set_margin_top(6)
        button.set_margin_end(6)
        button.set_icon_name("document-save-symbolic")
        button.set_halign(Gtk.Align.END)
        button.set_valign(Gtk.Align.START)
        button.add_css_class("osd")

        overlay.add_overlay(button)

        button_spinner: Gtk.Spinner = Gtk.Spinner()

        button.connect("clicked", image_button_clicked, image_index)

        curr_file_name = os.path.join(GLib.get_user_cache_dir(),
                                      f"t2i_image_{image_index}.png")

        img = Gtk.Picture()
        img.set_filename(curr_file_name)
        img.add_css_class("card")
        img.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
        img.set_halign(Gtk.Align.CENTER)

        img_width = img.get_paintable().get_intrinsic_width()
        img_height = img.get_paintable().get_intrinsic_height()

        overlay.set_size_request(img_width, img_height)
        overlay.set_child(img)
        overlay.set_clip_overlay(img, True)

        flow_box_child = Gtk.FlowBoxChild.new()
        flow_box_child.set_child(overlay)
        flow_box_child.set_halign(Gtk.Align.CENTER)

        self._flow_box_pictures.append(flow_box_child)
        self._flow_box.insert(flow_box_child, image_index)

    @Gtk.Template.Callback()
    def _on_run_button_clicked(self, _button):
        scheduler = str(self._scheduler_drop_down.get_selected_item().get_string())
        prompt = str(self._prompt_entry.get_text())
        height = int(self._width_spin_button.get_value())
        width = int(self._height_spin_button.get_value())
        inf_steps = int(self._inference_steps_spin_button.get_value())
        n_images = int(self._number_images_spin_button.get_value())

        self.page_state = self.PageState.RUNNING

        self._t_previous = time.time()

        self._text_to_image_runner.run(
            scheduler,
            prompt,
            height,
            width,
            inf_steps,
            n_images
        )

    @Gtk.Template.Callback()
    def _on_prompt_entry_changed(self, _entry):
        if self._prompt_entry.get_text():
            self._run_button.set_sensitive(True)
        else:
            self._run_button.set_sensitive(False)

    @Gtk.Template.Callback()
    def _on_cancel_run_button_clicked(self, _button):
        self._text_to_image_runner.cancel()
        self.page_state = self.PageState.START

    def cleanup(self) -> None:
        self._text_to_image_runner.cancel()

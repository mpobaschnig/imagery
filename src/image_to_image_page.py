# image_to_image_page.py
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
import logging
import os
import time
from gettext import gettext as i18n
from typing import List, Optional, Tuple

from gi.repository import Adw, Gio, GLib, Gtk, GObject

from .image_to_image_runner import ImageToImageRunner
from .prompt_ideas import prompt_idea_categories


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/ui/image_to_image_page.ui')
class ImageToImagePage(Gtk.Box):
    class PageState(Enum):
        START = 0
        RUNNING = 1
        FINISHED = 2

    __gtype_name__ = "ImageToImagePage"

    _settings_menu_button: Gtk.MenuButton = Gtk.Template.Child()
    _flow_box: Gtk.FlowBox = Gtk.Template.Child()
    _generating_progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _inference_steps_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _seed_switch: Gtk.Switch = Gtk.Template.Child()
    _seed_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _number_images_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _run_button: Gtk.Button = Gtk.Template.Child()
    _cancel_run_button: Gtk.Button = Gtk.Template.Child()
    _open_image_button: Gtk.Button = Gtk.Template.Child()
    _left_stack: Gtk.Stack = Gtk.Template.Child()
    _image_bin: Adw.Bin = Gtk.Template.Child()
    _separator: Gtk.Separator = Gtk.Template.Child()
    _strength_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _guidance_scale_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _flow_box_pictures: List[Gtk.Picture] = []
    _spin_button: Gtk.Button = Gtk.Template.Child()
    _spinner: Gtk.Spinner = Gtk.Template.Child()
    _image_path: Optional[str] = None
    _prompt_ideas_box: Gtk.Box = Gtk.Template.Child()
    _prompt_text_view: Gtk.TextView = Gtk.Template.Child()
    _neg_prompt_text_view: Gtk.TextView = Gtk.Template.Child()
    _prompt_ideas_menu_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, orientation=None, spacing=None):
        super().__init__(orientation, spacing)

        self._image_to_image_runner: ImageToImageRunner = ImageToImageRunner()

        self._image_to_image_runner.connect("update", self._update)
        self._image_to_image_runner.connect("finished", self._finished)
        self._image_to_image_runner.connect("cancelled", self._cancelled)

        self._prompt_text_view.get_buffer().connect(
            "changed", self._on_prompt_text_view_buffer_change_cb
        )

        self._seed_switch.bind_property(
            "active",
            self._seed_spin_button,
            "sensitive",
            GObject.BindingFlags.BIDIRECTIONAL
        )

        self._fill_prompt_box()

        self.page_state: self.PageState = self.PageState.START

        self._t_previous: float = 0

    def _update(self, _: ImageToImageRunner, step: int) -> None:
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

        def update(data: Tuple[str, int, int]) -> None:
            text: str = data[0]
            step: int = data[1]
            number_steps: int = data[2]

            self._generating_progress_bar.set_text(text)
            self._generating_progress_bar.set_fraction(step / number_steps)

        GLib.idle_add(update, (text, step, number_steps))

    def _finished(self, _):
        n_images = int(self._number_images_spin_button.get_value())

        for i in range(n_images):
            self._add_image(i)

        self.page_state = self.PageState.FINISHED

    def _cancelled(self, _):
        self.page_state = self.PageState.START

    def _fill_prompt_box(self):
        def _append_text(button: Gtk.Button, text_view: Gtk.TextView) -> None:
            start, end = text_view.get_buffer().get_bounds()
            text: str = str(text_view.get_buffer().get_text(start, end, False))
            idea: str = str(button.get_label())

            text = text.strip()

            if text == "":
                text = f"{idea}, "
            elif text.endswith(","):
                text += f" {idea}"
            else:
                text += f", {idea}"

            text_view.get_buffer().set_text(text)

        box: Gtk.Box = self._prompt_ideas_box
        box.set_spacing(12)

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
                               self._prompt_text_view)
                flow_box.append(button)

            box.append(flow_box)

    @property
    def page_state(self) -> PageState:
        return self._page_state

    @page_state.setter
    def page_state(self, new_page_state: PageState) -> None:
        self._page_state = new_page_state

        if new_page_state in (self.PageState.START, self.PageState.RUNNING):
            for i, _ in enumerate(self._flow_box_pictures):
                self._flow_box.remove(self._flow_box_pictures[i])

            self._flow_box_pictures.clear()

            self._separator.set_visible(False)
            self._flow_box.set_visible(False)

        if new_page_state == self.PageState.FINISHED:
            self._separator.set_visible(True)
            self._flow_box.set_visible(True)

        if new_page_state == self.PageState.RUNNING:
            self._spinner.set_spinning(True)
            self._spin_button.set_visible(True)

            self._prompt_text_view.set_sensitive(False)
            self._neg_prompt_text_view.set_sensitive(False)

            self._run_button.set_visible(False)
            self._cancel_run_button.set_visible(True)
            self._settings_menu_button.set_sensitive(False)
            self._prompt_ideas_menu_button.set_sensitive(False)

            self._generating_progress_bar.set_text(i18n("Estimating time left..."))
            self._generating_progress_bar.set_show_text(True)
            self._generating_progress_bar.set_fraction(0.0)
            self._generating_progress_bar.set_visible(True)
        else:
            self._spin_button.set_visible(False)
            self._spinner.set_spinning(False)

            self._prompt_text_view.set_sensitive(True)
            self._neg_prompt_text_view.set_sensitive(True)

            self._run_button.set_visible(True)
            self._cancel_run_button.set_visible(False)
            self._settings_menu_button.set_sensitive(True)
            self._prompt_ideas_menu_button.set_sensitive(True)

            self._generating_progress_bar.set_visible(False)

    def _add_image(self, image_index: int) -> Gtk.Overlay:  # noqa: E501, pylint: disable=too-many-statements
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
                                 f"i2i_image_{image}.png")
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

        overlay: Gtk.Overlay = Gtk.Overlay()
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
                                      f"i2i_image_{image_index}.png")

        img = Gtk.Picture()
        img.set_filename(curr_file_name)
        img.add_css_class("card")
        img.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
        img.set_halign(Gtk.Align.CENTER)

        img_width = img.get_paintable().get_intrinsic_width()
        img_height = img.get_paintable().get_intrinsic_height()
        maximum_width = 240
        if img_width > maximum_width:
            img_height = img_height / (img_width / maximum_width)
            img_width = maximum_width

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
        image_path = self._image_path
        start, end = self._prompt_text_view.get_buffer().get_bounds()
        prompt = str(self._prompt_text_view.get_buffer().get_text(start, end, False))
        nstart, nend = self._neg_prompt_text_view.get_buffer().get_bounds()
        neg_prompt = str(self._neg_prompt_text_view.get_buffer().get_text(
            nstart, nend, False)
        )
        strength = float(self._strength_spin_button.get_value())
        guidance_scale = float(self._guidance_scale_spin_button.get_value())
        inf_steps = int(self._inference_steps_spin_button.get_value())
        use_seed = bool(self._seed_switch.get_active())
        seed = int(self._seed_spin_button.get_value())
        n_images = int(self._number_images_spin_button.get_value())

        self.page_state = self.PageState.RUNNING

        self._t_previous = time.time()

        self._image_to_image_runner.run(
            image_path,
            prompt,
            neg_prompt,
            strength,
            guidance_scale,
            inf_steps,
            use_seed,
            seed,
            n_images
        )

    def _check_run_button_sensitivity(self):
        buffer = self._prompt_text_view.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, False)
        if text and self._image_path is not None:
            self._run_button.set_sensitive(True)
        else:
            self._run_button.set_sensitive(False)

    def _on_prompt_text_view_buffer_change_cb(self, _buffer: Gtk.TextBuffer) -> None:
        self._check_run_button_sensitivity()

    @Gtk.Template.Callback()
    def _on_cancel_run_button_clicked(self, _button):
        self._image_to_image_runner.cancel()
        self.page_state = self.PageState.START

    def _image_to_change_remove_cb(self, _button):
        self._image_path = None
        self._check_run_button_sensitivity()
        self._image_bin.set_child(None)
        self._left_stack.set_visible_child_name("open-image")
        self.page_state = self.PageState.START

    def _open_image_to_change_response_cb(self,
                                          dialog: Gtk.FileChooserDialog,
                                          response: int,
                                          user_data: tuple) -> None:
        if response != Gtk.ResponseType.ACCEPT:
            return

        dest_file: Gio.File = dialog.get_file()

        img: Gtk.Picture = user_data[0]
        img.set_filename(dest_file.get_path())

        self._image_path = dest_file.get_path()

        img_width = img.get_paintable().get_intrinsic_width()
        img_height = img.get_paintable().get_intrinsic_height()
        maximum_width = 240
        if img_width > maximum_width:
            img_height = img_height / (img_width / maximum_width)
            img_width = maximum_width

        overlay: Gtk.Overlay = user_data[1]
        overlay.set_size_request(img_width, img_height)

        self._check_run_button_sensitivity()

        self._left_stack.set_visible_child_name("show-image")

    @Gtk.Template.Callback()
    def _on_open_image_button_clicked_cb(self, _button):
        overlay = Gtk.Overlay()
        overlay.set_halign(Gtk.Align.CENTER)

        button = Gtk.Button()
        button.set_margin_top(6)
        button.set_margin_end(6)
        button.set_icon_name("window-close-symbolic")
        button.set_halign(Gtk.Align.END)
        button.set_valign(Gtk.Align.START)
        button.add_css_class("osd")

        overlay.add_overlay(button)

        button.connect("clicked", self._image_to_change_remove_cb)

        img = Gtk.Picture()
        img.add_css_class("card")
        img.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
        img.set_halign(Gtk.Align.CENTER)

        file_filter: Gtk.FileFilter = Gtk.FileFilter()
        file_filter.set_name("Images")
        file_filter.add_pattern("*.jpg")
        file_filter.add_pattern("*.jpeg")
        file_filter.add_pattern("*.png")

        file_chooser_native = Gtk.FileChooserNative()
        file_chooser_native.set_accept_label(i18n("Open Image"))
        file_chooser_native.set_action(Gtk.FileChooserAction.OPEN)
        file_chooser_native.connect(
            "response", self._open_image_to_change_response_cb, (img, overlay,)
        )
        file_chooser_native.add_filter(file_filter)
        file_chooser_native.show()

        overlay.set_child(img)
        overlay.set_clip_overlay(img, True)

        self._image_bin.set_child(overlay)

    def cleanup(self):
        self._image_to_image_runner.cancel()

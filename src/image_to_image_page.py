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

import logging
import os
import time
from gettext import gettext as i18n
from multiprocessing import Pipe, Process, connection
from typing import List, Optional

import torch
from diffusers import StableDiffusionImg2ImgPipeline as SDI2IPipeline
from gi.repository import Adw, Gio, GLib, Gtk
from PIL import Image

from .download_manager import DownloadManager
from .model_files import sd15_files, sd15_folder
from .settings_manager import is_nsfw_allowed


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/image_to_image_page.ui')
class ImageToImagePage(Gtk.Box):
    __gtype_name__ = "ImageToImagePage"

    _download_model_button: Gtk.Button = Gtk.Template.Child()
    _flow_box: Gtk.FlowBox = Gtk.Template.Child()
    _generating_progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _inference_steps_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _list_box: Gtk.ListBox = Gtk.Template.Child()
    _model_license_hint_label: Gtk.Label = Gtk.Template.Child()
    _number_images_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _prompt_entry: Adw.EntryRow = Gtk.Template.Child()
    _run_button: Gtk.Button = Gtk.Template.Child()
    _stack: Gtk.Stack = Gtk.Template.Child()
    _cancel_run_button: Gtk.Button = Gtk.Template.Child()
    _open_image_button: Gtk.Button = Gtk.Template.Child()
    _left_stack: Gtk.Stack = Gtk.Template.Child()
    _image_bin: Adw.Bin = Gtk.Template.Child()
    _separator: Gtk.Separator = Gtk.Template.Child()
    _strength_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _guidance_scale_spin_button: Gtk.SpinButton = Gtk.Template.Child()

    _download_task: Optional[Gio.Task] = None
    _run_task: Optional[Gio.Task] = None
    _flow_box_pictures: List[Gtk.Picture] = []
    _spinner: Optional[Gtk.Spinner] = Gtk.Spinner()
    _t_previous: float = 0
    _run_process: Optional[Process] = None
    _parent_connection: connection.Connection
    _child_connection: connection.Connection
    _image_path: Optional[str] = None

    _cancel_download_button: Gtk.Button = Gtk.Template.Child()
    _continue_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self):
        """Image To Image Page widget"""
        super().__init__()

        self._download_manager: DownloadManager = DownloadManager(sd15_files)

        self._download_manager.connect("reset", self._reset)
        self._download_manager.connect("update", self._update)
        self._download_manager.connect("cancelled", self._cancelled)
        self._download_manager.connect("finished", self._finished)

        if os.path.exists(sd15_folder):
            self._stack.set_visible_child_name("main")
            return

    def _reset(self, download_manager: DownloadManager):
        self._progress_bar.set_show_text(i18n("Initializing..."))
        self._progress_bar.set_fraction(0.0)
        self._progress_bar.set_visible(True)

    def _update(self,
                _download_manager: DownloadManager,
                fraction: float,
                current_downloaded: int,
                total_size: int,
                unit: str,
                current_index: int,
                total_files: int):
        self._progress_bar.set_text(i18n(
            f"{current_downloaded} {unit} / {total_size} {unit} - ({current_index} of {total_files})"
        ))
        self._progress_bar.set_fraction(fraction)

    def _cancelled(self, download_manager: DownloadManager):
        self._progress_bar.set_visible(False)
        self._download_model_button.set_visible(True)
        self._cancel_download_button.set_visible(False)
        self._model_license_hint_label.set_visible(True)

    def _finished(self, download_manager: DownloadManager):
        self._progress_bar.set_fraction(100)
        self._progress_bar.set_text(i18n("Download finished."))
        self._continue_button.set_visible(True)
        self._cancel_download_button.set_visible(False)

    @Gtk.Template.Callback()
    def _on_download_model_button_clicked(self, _button):
        self._cancel_download_button.set_visible(True)
        self._download_model_button.set_visible(False)

        self._model_license_hint_label.set_visible(False)

        self._download_manager.start()

    @Gtk.Template.Callback()
    def _on_cancel_download_button_clicked(self, _button):
        self._download_manager.cancel()

    @Gtk.Template.Callback()
    def _on_continue_button_clicked(self, _button):
        self._stack.set_visible

    def _pipeline_callback(self,
                           step: int,
                           _timestep: int,
                           _latents: torch.FloatTensor) -> None:
        # pylint: disable=no-member
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

    def _run_process_func(self, child_connection: connection.Connection) -> None:
        def pipeline_callback(step: int,
                              _timestep: int,
                              _latents: torch.FloatTensor) -> None:
            # pylint: disable=no-member
            t_now = time.time()
            t_diff = t_now - self._t_previous
            self._t_previous = t_now

            self._child_connection.send((step, t_diff,))

        model_id = os.path.join(GLib.get_user_data_dir(),
                                "stable-diffusion-v1-5")

        pipeline: SDI2IPipeline = SDI2IPipeline.from_pretrained(model_id)

        if torch.cuda.is_available():
            pipeline = pipeline.to("cuda")
            generator = torch.Generator(device="cuda")
        else:
            generator = torch.Generator()

        if is_nsfw_allowed():
            pipeline.safety_checker = lambda images, **kwargs: (
                images, False
            )

        image = Image.open(self._image_path).convert("RGB")
        prompt = self._prompt_entry.get_text()
        strength = float(self._strength_spin_button.get_value())
        guidance_scale = float(self._guidance_scale_spin_button.get_value())
        inf_steps = int(self._inference_steps_spin_button.get_value())
        n_images = int(self._number_images_spin_button.get_value())

        self._t_previous = time.time()

        result = pipeline(prompt=prompt,
                          image=[image for _ in range(n_images)],
                          strength=strength,
                          guidance_scale=guidance_scale,
                          generator=generator,
                          num_inference_steps=inf_steps,
                          num_images_per_prompt=n_images,
                          callback=pipeline_callback)

        for i in range(n_images):
            file_name = os.path.join(GLib.get_user_cache_dir(),
                                     f"image_{i}.png")
            result.images[i].save(file_name)

        child_connection.send('SENTINEL')

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
                                 f"image_{image}.png")
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
                                      f"image_{image_index}.png")

        img = Gtk.Picture()
        img.set_filename(curr_file_name)
        img.add_css_class("card")
        img.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
        img.set_halign(Gtk.Align.CENTER)

        overlay.set_child(img)
        overlay.set_clip_overlay(img, True)

        flow_box_child = Gtk.FlowBoxChild.new()
        flow_box_child.set_child(overlay)
        flow_box_child.set_halign(Gtk.Align.CENTER)

        self._flow_box_pictures.append(flow_box_child)
        self._flow_box.insert(flow_box_child, image_index)

    def _update_task(self, _task, _source_object, _task_data, _cancellable):
        try:
            for msg in iter(self._parent_connection.recv, 'SENTINEL'):
                step = msg[0]
                t_diff = msg[1]

                number_steps = int(
                    self._inference_steps_spin_button.get_value())

                time_left = (number_steps - step) * t_diff

                minutes: int = int(time_left // 60)
                seconds: int = int(time_left % 60)

                if minutes == 0:
                    text = i18n(f"~{seconds} s left...")
                else:
                    text = i18n(f"~{minutes} min {seconds} s left...")

                self._generating_progress_bar.set_text(text)
                self._generating_progress_bar.set_fraction(step / number_steps)

            self._run_process.join()

            self._spinner.set_spinning(False)
            self._run_button.set_icon_name(
                "media-playback-start-symbolic"
            )
            self._generating_progress_bar.set_visible(False)
            self._cancel_run_button.set_visible(False)

            n_images = int(self._number_images_spin_button.get_value())

            for i in range(n_images):
                self._add_image(i)

            self._separator.set_visible(True)
            self._flow_box.set_visible(True)

        except EOFError as _error:
            logging.info("Pipe broke - Was the run cancelled? : %s", _error)
            return

    @Gtk.Template.Callback()
    def _on_run_button_clicked(self, _button):
        if self._spinner.get_spinning():
            return

        self._separator.set_visible(False)
        self._flow_box.set_visible(False)

        for i, _v in enumerate(self._flow_box_pictures):
            self._flow_box.remove(self._flow_box_pictures[i])

        self._flow_box_pictures.clear()

        self._cancel_run_button.set_visible(True)
        self._run_button.set_child(self._spinner)
        self._spinner.set_spinning(True)
        self._generating_progress_bar.set_text(i18n("Estimating time left..."))
        self._generating_progress_bar.set_show_text(True)
        self._generating_progress_bar.set_fraction(0.0)
        self._generating_progress_bar.set_visible(True)

        self._parent_connection, self._child_connection = Pipe()
        self._run_task = Gio.Task.new(self,
                                      None,
                                      None,
                                      None)
        self._run_task.run_in_thread(self._update_task)

        self._run_process = Process(target=self._run_process_func,
                                    args=(self._child_connection,))

        self._run_process.start()

    def _check_run_button_sensitivity(self):
        if self._prompt_entry.get_text() and self._image_path is not None:
            self._run_button.set_sensitive(True)
        else:
            self._run_button.set_sensitive(False)

    @Gtk.Template.Callback()
    def _on_prompt_entry_changed(self, _entry):
        self._check_run_button_sensitivity()

    @Gtk.Template.Callback()
    def _on_cancel_run_button_clicked(self, _button):
        self._run_process.terminate()

        self._spinner.set_spinning(False)
        self._run_button.set_icon_name(
            "media-playback-start-symbolic"
        )
        self._generating_progress_bar.set_visible(False)
        self._cancel_run_button.set_visible(False)

    def _image_to_change_remove_cb(self, _button):
        self._image_path = None
        self._check_run_button_sensitivity()
        self._left_stack.set_visible_child_name("open-image")

    def _open_image_to_change_response_cb(self,
                                          dialog: Gtk.FileChooserDialog,
                                          response: int,
                                          user_data: tuple) -> None:
        if response != Gtk.ResponseType.ACCEPT:
            return

        dest_file: Gio.File = dialog.get_file()

        img = user_data[0]
        img.set_filename(dest_file.get_path())

        self._image_path = dest_file.get_path()

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

        file_chooser_native = Gtk.FileChooserNative()
        file_chooser_native.set_accept_label(i18n("Open Image"))
        file_chooser_native.set_action(Gtk.FileChooserAction.OPEN)
        file_chooser_native.connect(
            "response", self._open_image_to_change_response_cb, (img,)
        )
        file_chooser_native.show()

        overlay.set_child(img)
        overlay.set_clip_overlay(img, True)

        self._image_bin.set_child(overlay)

    def cleanup(self):
        if self._run_process is not None:
            logging.info("Terminating image-to-image subprocess...")
            self._run_process.terminate()

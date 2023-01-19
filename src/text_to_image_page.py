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

from gi.repository import Gtk, GLib, Adw, Gio
from gettext import gettext as i18n
from typing import Optional, List

import os
import logging
from enum import Enum
import threading
from diffusers import StableDiffusionPipeline
import torch
import functools
import time
from multiprocessing import Process, Pipe
import time

from .settings_manager import is_nsfw_allowed

from .downloader import Downloader
from .model_files import sd15_folder, sd15_files
from .file import File


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/text_to_image_page.ui')
class TextToImagePage(Gtk.Box):
    __gtype_name__ = "TextToImagePage"

    _download_model_button: Gtk.Button = Gtk.Template.Child()
    _flow_box: Gtk.FlowBox = Gtk.Template.Child()
    _generating_progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _height_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _inference_steps_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _list_box: Gtk.ListBox = Gtk.Template.Child()
    _model_license_hint_label: Gtk.Label = Gtk.Template.Child()
    _number_images_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _prompt_entry: Adw.EntryRow = Gtk.Template.Child()
    _run_button: Gtk.Button = Gtk.Template.Child()
    _scheduler_drop_down: Gtk.DropDown = Gtk.Template.Child()
    _stack: Gtk.Stack = Gtk.Template.Child()
    _width_spin_button: Gtk.SpinButton = Gtk.Template.Child()
    _cancel_run_button: Gtk.Button = Gtk.Template.Child()

    _download_task: Optional[Gio.Task] = None
    _run_task: Optional[Gio.Task] = None
    _flow_box_pictures = []
    _spinner: Gtk.Spinner = Gtk.Spinner()
    _t_previous: int = 0

    def __init__(self):
        """Text To Image Page widget"""
        super().__init__()

        if os.path.exists(sd15_folder):
            self._stack.set_visible_child_name("main")
            return

        self._downloader: Downloader = Downloader(files=sd15_files,
                                                  download_model_button=self._download_model_button,
                                                  model_license_hint_label=self._model_license_hint_label,
                                                  progress_bar=self._progress_bar)

    @Gtk.Template.Callback()
    def _on_download_model_button_clicked(self, _button):
        if self._downloader.is_finished():
            self._stack.set_visible_child_name("main")
        else:
            self._downloader.download()

    def _pipeline_callback(self, step: int, timestep: int, latents: torch.FloatTensor):
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

    def _get_scheduler(self, pipeline: StableDiffusionPipeline, scheduler: str):
        if scheduler == "LMSDiscreteScheduler":
            from diffusers import LMSDiscreteScheduler
            return LMSDiscreteScheduler.from_config(pipeline.scheduler.config)
        elif scheduler == "DDIMScheduler":
            from diffusers import DDIMScheduler
            return DDIMScheduler.from_config(pipeline.scheduler.config)
        elif scheduler == "DPMSolverMultistepScheduler":
            from diffusers import DPMSolverMultistepScheduler
            return DPMSolverMultistepScheduler.from_config(pipeline.scheduler.config)
        elif scheduler == "EulerDiscreteScheduler":
            from diffusers import EulerDiscreteScheduler
            return EulerDiscreteScheduler.from_config(pipeline.scheduler.config)
        elif scheduler == "PNDMScheduler":
            from diffusers import PNDMScheduler
            return PNDMScheduler.from_config(pipeline.scheduler.config)
        elif scheduler == "DDPMScheduler":
            from diffusers import DDPMScheduler
            return DDPMScheduler.from_config(pipeline.scheduler.config)
        elif scheduler == "EuelrAncestralDiscreteScheduler":
            from diffusers import EulerAncestralDiscreteScheduler
            return EulerAncestralDiscreteScheduler.from_config(pipeline.scheduler.config)

    def _run_process_func(self, child_connection):
        def pipeline_callback(step: int, timestep: int, latents: torch.FloatTensor):
            t_now = time.time()
            t_diff = t_now - self._t_previous
            self._t_previous = t_now

            self._child_connection.send((step, t_diff,))

        model_id = os.path.join(GLib.get_user_data_dir(),
                                "stable-diffusion-v1-5")

        pipeline: StableDiffusionPipeline = StableDiffusionPipeline.from_pretrained(
            model_id
        )

        scheduler = self._scheduler_drop_down.get_selected_item().get_string()

        pipeline.scheduler = self._get_scheduler(pipeline, scheduler)

        if torch.cuda.is_available():
            pipeline = pipeline.to("cuda")

        if is_nsfw_allowed():
            pipeline.safety_checker = lambda images, **kwargs: (
                images, False
            )

        prompt = self._prompt_entry.get_text()
        height = int(self._width_spin_button.get_value())
        width = int(self._height_spin_button.get_value())
        inf_steps = int(self._inference_steps_spin_button.get_value())
        n_images = int(self._number_images_spin_button.get_value())

        self._t_previous = time.time()

        result = pipeline(prompt=prompt,
                          height=height,
                          width=width,
                          num_inference_steps=inf_steps,
                          num_images_per_prompt=n_images,
                          callback=pipeline_callback)

        for i in range(n_images):
            file_name = os.path.join(GLib.get_user_cache_dir(),
                                     f"image_{i}.png")
            result.images[i].save(file_name)

        child_connection.send('SENTINEL')

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
                file_name = os.path.join(GLib.get_user_cache_dir(),
                                         f"image_{i}.png")

                img = Gtk.Picture()
                img.set_filename(file_name)
                img.add_css_class("card")
                img.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
                img.set_halign(Gtk.Align.CENTER)

                self._flow_box_pictures.append(img)
                self._flow_box.insert(img, i)
        except EOFError as e:
            logging.info(f"EOFError - Pipe broke - Was the run cancelled?")
            return

    @ Gtk.Template.Callback()
    def _on_run_button_clicked(self, _button):
        if self._spinner.get_spinning():
            return

        for i in range(len(self._flow_box_pictures)):
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

        self._run_process: Process = Process(target=self._run_process_func,
                                             args=(self._child_connection,))

        self._run_process.start()

    @Gtk.Template.Callback()
    def _on_prompt_entry_changed(self, _entry):
        if self._prompt_entry.get_text():
            self._run_button.set_sensitive(True)
        else:
            self._run_button.set_sensitive(False)

    @Gtk.Template.Callback()
    def _on_cancel_run_button_clicked(self, _button):
        self._run_process.terminate()

        self._spinner.set_spinning(False)
        self._run_button.set_icon_name(
            "media-playback-start-symbolic"
        )
        self._generating_progress_bar.set_visible(False)
        self._cancel_run_button.set_visible(False)

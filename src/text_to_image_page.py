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

from .downloader import Downloader
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

    _download_task: Optional[Gio.Task] = None
    _run_task: Optional[Gio.Task] = None
    _flow_box_pictures = []
    _spinner: Gtk.Spinner = Gtk.Spinner()

    def __init__(self):
        """Start Page widget"""
        super().__init__()

        path = os.path.join(GLib.get_user_data_dir(),
                            "stable-diffusion-v1-5/")

        if os.path.exists(path):
            self._stack.set_visible_child_name("main")
            return

        folder = os.path.join(GLib.get_user_data_dir(),
                              "stable-diffusion-v1-5/")
        files = [
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/feature_extractor/preprocessor_config.json",
                 folder + "feature_extractor/preprocessor_config.json",
                 "2a1da83b5e1032aaeef397552ddb408dca0d8cd1dc58f61bf6abf38d6f33a0a2"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/safety_checker/config.json",
                 folder + "safety_checker/config.json",
                 "5dd77a06cbd9b155060bd58deb81ffd1aafc1c6d7970acac674c1128bd4edfe2"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/safety_checker/pytorch_model.bin",
                 folder + "safety_checker/pytorch_model.bin",
                 "193490b58ef62739077262e833bf091c66c29488058681ac25cf7df3d8190974"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/scheduler/scheduler_config.json",
                 folder + "scheduler/scheduler_config.json",
                 "699cce92eb7c122e2eb7dfdea78e6187fda76a5ed4a8e42319b85610e620e091"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/text_encoder/config.json",
                 folder + "text_encoder/config.json",
                 "845df614cb9327ae7bbea027316246fae917827407da6df13572e41b5f93b4cc"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/text_encoder/pytorch_model.bin",
                 folder + "text_encoder/pytorch_model.bin",
                 "770a47a9ffdcfda0b05506a7888ed714d06131d60267e6cf52765d61cf59fd67"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/tokenizer/merges.txt",
                 folder + "tokenizer/merges.text",
                 "9fd691f7c8039210e0fced15865466c65820d09b63988b0174bfe25de299051a"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/tokenizer/special_tokens_map.json",
                 folder + "tokenizer/special_tokens_map.json",
                 "c4864a9376a8401918425bed71fc14fc0e81f9b59ec45c1cf96cccb2df508eac"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/tokenizer/tokenizer_config.json",
                 folder + "tokenizer/tokenizer_config.json",
                 "00439066fcba73de57644cf41e4e3b9f2dbb09d7f3fc2005898ba52399045882"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/tokenizer/vocab.json",
                 folder + "tokenizer/vocab.json",
                 "e089ad92ba36837a0d31433e555c8f45fe601ab5c221d4f607ded32d9f7a4349"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/unet/config.json",
                 folder + "unet/config.json",
                 "78f474de6bab3d893868f37be97b636ae65c0df3073ed3256ca458ff599b5f96"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/unet/diffusion_pytorch_model.bin",
                 folder + "unet/diffusion_pytorch_model.bin",
                 "c7da0e21ba7ea50637bee26e81c220844defdf01aafca02b2c42ecdadb813de4"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/vae/config.json",
                 folder + "vae/config.json",
                 "786a7d21647ddea6a04b9675c03d3cb45e90a2f3c6da5fbda2c54ade040036de"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/vae/diffusion_pytorch_model.bin",
                 folder + "vae/diffusion_pytorch_model.bin",
                 "1b134cded8eb78b184aefb8805b6b572f36fa77b255c483665dda931fa0130c5"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/model_index.json",
                 folder + "model_index.json",
                 "72435d612b1363ac5f0727052e7fc74bcdc08f625603e147bb4850e0aa404fea"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned.ckpt",
                 folder + "v1-5-pruned.ckpt",
                 "e1441589a6f3c5a53f5f54d0975a18a7feb7cdf0b0dee276dfc3331ae376a053"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt",
                 folder + "v1-5-pruned-emaonly.ckpt",
                 "cc6cb27103417325ff94f52b7a5d2dde45a7515b25c255d8e396c90014281516"),
            File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/main/v1-inference.yaml",
                 folder + "v1-inference.yaml",
                 "20b7f0acae54d1f88384a6ca15b5d62c0ee4fbbca07ff72f3761fe936083210d")
        ]

        self._downloader: Downloader = Downloader(files=files,
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
        number_steps = int(self._inference_steps_spin_button.get_value())
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

    @Gtk.Template.Callback()
    def _on_run_button_clicked(self, _button):
        if self._spinner.get_spinning():
            return

        for i in range(len(self._flow_box_pictures)):
            self._flow_box.remove(self._flow_box_pictures[i])

        self._flow_box_pictures.clear()

        self._run_button.set_child(self._spinner)
        self._spinner.set_spinning(True)
        self._generating_progress_bar.set_fraction(0.0)
        self._generating_progress_bar.set_visible(True)

        def run(task, source, task_data, cancellable):
            model_id = os.path.join(GLib.get_user_data_dir(),
                                    "stable-diffusion-v1-5")

            pipeline: StableDiffusionPipeline = StableDiffusionPipeline.from_pretrained(
                model_id)

            scheduler = self._scheduler_drop_down.get_selected_item().get_string()

            pipeline.scheduler = self._get_scheduler(pipeline, scheduler)

            if torch.cuda.is_available():
                pipeline = pipeline.to("cuda")

            prompt = self._prompt_entry.get_text()
            height = int(self._width_spin_button.get_value())
            width = int(self._height_spin_button.get_value())
            inf_steps = int(self._inference_steps_spin_button.get_value())
            n_images = int(self._number_images_spin_button.get_value())

            result = pipeline(prompt=prompt,
                              height=height,
                              width=width,
                              num_inference_steps=inf_steps,
                              num_images_per_prompt=n_images,
                              callback=self._pipeline_callback)

            for i in range(n_images):
                file_name = os.path.join(GLib.get_user_cache_dir(),
                                         f"image_{i}.png")
                result.images[i].save(file_name)

                img = Gtk.Picture()
                img.set_filename(file_name)

                self._flow_box_pictures.append(img)
                self._flow_box.insert(img, i)

        def finished(source_object, result, task_data):
            source_object._spinner.set_spinning(False)
            source_object._run_button.set_icon_name("media-playback-start-symbolic")
            source_object._generating_progress_bar.set_visible(False)

        self._run_task = Gio.Task.new(self,
                                      None,
                                      finished,
                                      None)
        self._run_task.run_in_thread(run)

    @Gtk.Template.Callback()
    def _on_prompt_entry_changed(self, _entry):
        if self._prompt_entry.get_text():
            self._run_button.set_sensitive(True)
        else:
            self._run_button.set_sensitive(False)

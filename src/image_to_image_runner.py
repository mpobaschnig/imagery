# image_to_image_runner.py
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
from multiprocessing import Pipe, Process, connection
from typing import Optional

import torch
from diffusers import StableDiffusionImg2ImgPipeline as SDI2IPipeline
from gi.repository import Gio, GLib, GObject
from PIL import Image

from .settings_manager import is_nsfw_allowed


class ImageToImageRunner(GObject.Object):
    __gsignals__ = {
        "cancelled": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "update": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "finished": (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self):
        super().__init__()

        self._task: Optional[Gio.Task] = None
        self._task_cancellable: Optional[Gio.Cancellable] = None

        self._process: Optional[Process] = None

        self._parent_connection: Optional[connection.Connection] = None
        self._child_connection: Optional[connection.Connection] = None

    def _child_func(self,  # pylint: disable=too-many-arguments, too-many-locals
                    child_connection: connection.Connection,
                    image_path: str,
                    prompt: str,
                    strength: float,
                    guidance_scale: float,
                    inf_steps: int,
                    seed: int,
                    n_images: int) -> None:
        def pipeline_callback(step: int,
                              _timestep: int,
                              _latents: torch.FloatTensor) -> None:
            child_connection.send((step,))

        model_id = os.path.join(GLib.get_user_data_dir(),
                                "stable-diffusion-v1-5")

        pipeline: Optional[SDI2IPipeline] = None
        if is_nsfw_allowed():
            pipeline = SDI2IPipeline.from_pretrained(model_id,
                                                     safety_checker=None)
        else:
            pipeline = SDI2IPipeline.from_pretrained(model_id)

        generator: Optional[torch.Generator] = None
        if torch.cuda.is_available():
            pipeline = pipeline.to("cuda")
            generator = torch.Generator(device="cuda").manual_seed(seed)
        else:
            generator = torch.Generator().manual_seed(seed)

        image = Image.open(image_path).convert("RGB")

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
                                     f"i2i_image_{i}.png")
            result.images[i].save(file_name)

        child_connection.send('SENTINEL')

    def _parent_func(self, _task, _source_object, _task_data, _cancellable):
        try:
            for msg in iter(self._parent_connection.recv, 'SENTINEL'):
                self.emit("update", msg[0])

            self._process.join()

            self.emit("finished")
        except EOFError as _error:
            logging.info("Pipe broke - Was the run cancelled? : %s", _error)

    def run(self,  # pylint: disable=too-many-arguments
            scheduler: str,
            prompt: str,
            height: int,
            width: int,
            inf_steps: int,
            seed: int,
            n_images: int) -> None:
        self._parent_connection, self._child_connection = Pipe()

        self._task = Gio.Task.new(self,
                                  None,
                                  None,
                                  None)

        self._task.run_in_thread(self._parent_func)

        self._process = Process(target=self._child_func,
                                args=(self._child_connection,
                                      scheduler,
                                      prompt,
                                      height,
                                      width,
                                      inf_steps,
                                      seed,
                                      n_images))
        self._process.start()

    def cancel(self):
        if self._process is not None:
            logging.info("Terminating text-to-image subprocess...")
            self._process.terminate()

        if self._task_cancellable:
            self._task_cancellable.cancel()

        self.emit("cancelled")

# text_to_image_runner.py
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
from diffusers import (DDIMScheduler, DDPMScheduler,
                       DPMSolverMultistepScheduler,
                       EulerAncestralDiscreteScheduler, EulerDiscreteScheduler,
                       LMSDiscreteScheduler, PNDMScheduler,
                       StableDiffusionPipeline)
from gi.repository import Gio, GLib, GObject

from .settings_manager import is_nsfw_allowed


class TextToImageRunner(GObject.Object):
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

    def _child_func(self,  # pylint: disable=too-many-arguments
                    child_connection: connection.Connection,
                    scheduler: str,
                    prompt: str,
                    height: int,
                    width: int,
                    inf_steps: int,
                    n_images: int) -> None:
        def pipeline_cb(step: int,
                        _timestep: int,
                        _latents: torch.FloatTensor) -> None:
            child_connection.send((step,))

        model_id = os.path.join(GLib.get_user_data_dir(),
                                "stable-diffusion-v1-5")

        if is_nsfw_allowed():
            pipeline: StableDiffusionPipeline = StableDiffusionPipeline.from_pretrained(
                model_id,
                safety_checker=None
            )
        else:
            pipeline: StableDiffusionPipeline = StableDiffusionPipeline.from_pretrained(
                model_id
            )

        pipeline.scheduler = self._get_scheduler(pipeline, scheduler)

        if torch.cuda.is_available():
            pipeline = pipeline.to("cuda")

        result = pipeline(prompt=prompt,
                          height=height,
                          width=width,
                          num_inference_steps=inf_steps,
                          num_images_per_prompt=n_images,
                          callback=pipeline_cb)

        for i in range(n_images):
            file_name = os.path.join(GLib.get_user_cache_dir(),
                                     f"t2i_image_{i}.png")
            result.images[i].save(file_name)

        child_connection.send('SENTINEL')

    # pylint: disable-next=too-many-return-statements
    def _get_scheduler(self,  # type: ignore
                       pipeline: StableDiffusionPipeline,
                       scheduler: str):
        if scheduler == "LMSDiscreteScheduler":
            return LMSDiscreteScheduler.from_config(pipeline.scheduler.config)
        if scheduler == "DDIMScheduler":
            return DDIMScheduler.from_config(pipeline.scheduler.config)
        if scheduler == "DPMSolverMultistepScheduler":
            return DPMSolverMultistepScheduler.from_config(pipeline.scheduler.config)
        if scheduler == "EulerDiscreteScheduler":
            return EulerDiscreteScheduler.from_config(pipeline.scheduler.config)
        if scheduler == "DDPMScheduler":
            return DDPMScheduler.from_config(pipeline.scheduler.config)
        if scheduler == "EuelrAncestralDiscreteScheduler":
            return EulerAncestralDiscreteScheduler.from_config(
                pipeline.scheduler.config
            )
        # This is the default one
        return PNDMScheduler.from_config(pipeline.scheduler.config)

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
                                      n_images))
        self._process.start()

    def cancel(self):
        if self._process is not None:
            logging.info("Terminating text-to-image subprocess...")
            self._process.terminate()

        if self._task_cancellable:
            self._task_cancellable.cancel()

        self.emit("cancelled")

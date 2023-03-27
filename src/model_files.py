# stable_diffusion_1_5.py
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
# pylint: skip-file
from gi.repository import GLib
import os

from .file import File

sd15_folder = os.path.join(GLib.get_user_data_dir(),
                           "stable-diffusion-v1-5/")
sd15_files = [
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/feature_extractor/preprocessor_config.json",
         sd15_folder + "feature_extractor/preprocessor_config.json",
         "2a1da83b5e1032aaeef397552ddb408dca0d8cd1dc58f61bf6abf38d6f33a0a2"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/safety_checker/config.json",
         sd15_folder + "safety_checker/config.json",
         "5dd77a06cbd9b155060bd58deb81ffd1aafc1c6d7970acac674c1128bd4edfe2"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/889b629140e71758e1e0006e355c331a5744b4bf/safety_checker/pytorch_model.bin",
         sd15_folder + "safety_checker/pytorch_model.bin",
         "193490b58ef62739077262e833bf091c66c29488058681ac25cf7df3d8190974"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/scheduler/scheduler_config.json",
         sd15_folder + "scheduler/scheduler_config.json",
         "699cce92eb7c122e2eb7dfdea78e6187fda76a5ed4a8e42319b85610e620e091"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/text_encoder/config.json",
         sd15_folder + "text_encoder/config.json",
         "845df614cb9327ae7bbea027316246fae917827407da6df13572e41b5f93b4cc"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/889b629140e71758e1e0006e355c331a5744b4bf/text_encoder/pytorch_model.bin",
         sd15_folder + "text_encoder/pytorch_model.bin",
         "770a47a9ffdcfda0b05506a7888ed714d06131d60267e6cf52765d61cf59fd67"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/tokenizer/merges.txt",
         sd15_folder + "tokenizer/merges.txt",
         "9fd691f7c8039210e0fced15865466c65820d09b63988b0174bfe25de299051a"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/tokenizer/special_tokens_map.json",
         sd15_folder + "tokenizer/special_tokens_map.json",
         "c4864a9376a8401918425bed71fc14fc0e81f9b59ec45c1cf96cccb2df508eac"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/tokenizer/tokenizer_config.json",
         sd15_folder + "tokenizer/tokenizer_config.json",
         "00439066fcba73de57644cf41e4e3b9f2dbb09d7f3fc2005898ba52399045882"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/tokenizer/vocab.json",
         sd15_folder + "tokenizer/vocab.json",
         "e089ad92ba36837a0d31433e555c8f45fe601ab5c221d4f607ded32d9f7a4349"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/unet/config.json",
         sd15_folder + "unet/config.json",
         "78f474de6bab3d893868f37be97b636ae65c0df3073ed3256ca458ff599b5f96"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/889b629140e71758e1e0006e355c331a5744b4bf/unet/diffusion_pytorch_model.bin",
         sd15_folder + "unet/diffusion_pytorch_model.bin",
         "c7da0e21ba7ea50637bee26e81c220844defdf01aafca02b2c42ecdadb813de4"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/vae/config.json",
         sd15_folder + "vae/config.json",
         "786a7d21647ddea6a04b9675c03d3cb45e90a2f3c6da5fbda2c54ade040036de"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/889b629140e71758e1e0006e355c331a5744b4bf/vae/diffusion_pytorch_model.bin",
         sd15_folder + "vae/diffusion_pytorch_model.bin",
         "1b134cded8eb78b184aefb8805b6b572f36fa77b255c483665dda931fa0130c5"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/model_index.json",
         sd15_folder + "model_index.json",
         "72435d612b1363ac5f0727052e7fc74bcdc08f625603e147bb4850e0aa404fea"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/889b629140e71758e1e0006e355c331a5744b4bf/v1-5-pruned-emaonly.ckpt",
         sd15_folder + "v1-5-pruned-emaonly.ckpt",
         "cc6cb27103417325ff94f52b7a5d2dde45a7515b25c255d8e396c90014281516"),
    File("https://huggingface.co/runwayml/stable-diffusion-v1-5/raw/889b629140e71758e1e0006e355c331a5744b4bf/v1-inference.yaml",
         sd15_folder + "v1-inference.yaml",
         "20b7f0acae54d1f88384a6ca15b5d62c0ee4fbbca07ff72f3761fe936083210d")
]

sd_files_size = 9748455424

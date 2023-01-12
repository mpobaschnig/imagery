# Imagery

Imagery lets you generate images using [Stable Diffusion](https://github.com/Stability-AI/stablediffusion) based on text or image input.

# How to Build

Clone the repository:
```sh
git clone https://github.com/mpobaschnig/imagery
```

Then, download the stable diffusion model `v2-1_768-ema-pruned.ckpt` from the following link and put it into `~/.var/app/io.github.mpobaschnig.Imagery/data/`:

```sh
https://huggingface.co/stabilityai/stable-diffusion-2-1
```

In the end, we can just open GNOME Builder (or vscode with Flatpak extension), and run it from there.

# License

When downloading the model, you accept the [CreativeML Open RAIL-M license](https://github.com/CompVis/stable-diffusion/blob/21f890f9da3cfbeaba8e2ac3c425ee9e998d5229/LICENSE).

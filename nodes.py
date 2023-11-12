import io
import json
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from comfy.cli_args import args
from . import server


class RemoteSaveImage:
    def __init__(self):
        self.type = "output"
        self.prefix_append = ""
        self.server = server.Server()

    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"images": ("IMAGE", ),
                     "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                     "output_dir": ("STRING", {"default": "."}),
                     },
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    RETURN_TYPES = ()
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "image"

    def save_images(self, images, filename_prefix="ComfyUI", output_dir='.', prompt=None, extra_pnginfo=None):
        filename_prefix += self.prefix_append
        for image in images:
            i = 255. * image.cpu().numpy()
            i = np.clip(i, 0, 255).astype(np.uint8)
            img = Image.fromarray(i)

            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            stream = io.BytesIO()
            img.save(stream, format='PNG', pnginfo=metadata, compress_level=4)
            self.server.queue_image(output_dir, filename_prefix, stream.getvalue())
        return {}


NODE_CLASS_MAPPINGS = {
    "RemoteSaveImage": RemoteSaveImage,
}

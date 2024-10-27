from PIL import Image

from .modified_loop import sampling_loop

async def fill_form(img: Image.Image, data: str) -> Image.Image:
    messages = [{"role": "user", "content": f"I am filling out a form on my local computer. Please assist me. Use this data: {data}"}]

    return await sampling_loop(model="claude-3-5-sonnet-20241022", messages=messages, img=img)
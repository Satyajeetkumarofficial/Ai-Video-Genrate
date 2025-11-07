import os
import time
import subprocess
from PIL import Image
import torch
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline

MODEL_ID = os.environ.get("SD_MODEL", "runwayml/stable-diffusion-v1-5")

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def get_text2img_pipe():
    device = torch.device("cpu")
    pipe = StableDiffusionPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.float32)
    pipe.safety_checker = None
    pipe = pipe.to(device)
    pipe.enable_attention_slicing()
    return pipe

def get_img2img_pipe():
    device = torch.device("cpu")
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.float32)
    pipe.safety_checker = None
    pipe = pipe.to(device)
    pipe.enable_attention_slicing()
    return pipe

def text_to_frames(prompt, out_dir, num_frames=12, width=720, height=720, steps=40):
    ensure_dir(out_dir)
    pipe = get_text2img_pipe()
    files = []
    base_seed = int(time.time())
    for i in range(num_frames):
        gen = torch.Generator("cpu").manual_seed(base_seed + i)
        img = pipe(prompt, height=height, width=width, num_inference_steps=steps, generator=gen).images[0]
        path = os.path.join(out_dir, f"frame_{i:03d}.png")
        img.save(path)
        files.append(path)
    return files

def image_prompt_to_frames(init_image_path, prompt, out_dir, num_frames=10, strength=0.65, steps=35):
    ensure_dir(out_dir)
    pipe = get_img2img_pipe()
    files = []
    img = Image.open(init_image_path).convert("RGB")
    for i in range(num_frames):
        gen = torch.Generator("cpu").manual_seed(int(time.time()) + i)
        out = pipe(prompt=prompt, init_image=img, strength=strength, num_inference_steps=steps, generator=gen)
        out_img = out.images[0]
        path = os.path.join(out_dir, f"frame_{i:03d}.png")
        out_img.save(path)
        files.append(path)
    return files

def frames_to_video(frames, out_path, fps=12):
    list_file = out_path + ".txt"
    with open(list_file, "w") as f:
        for p in frames:
            f.write(f"file '{os.path.abspath(p)}'\n")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path
    ]
    subprocess.run(cmd, check=True)
    os.remove(list_file)
    return out_path

def cleanup_dir(d):
    for root, _, files in os.walk(d):
        for f in files:
            try: os.remove(os.path.join(root, f))
            except: pass

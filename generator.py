# generator.py
import os
import time
import subprocess
from PIL import Image
import torch
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline

# Change model id if you have a smaller or different checkpoint
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
    """
    Generate a sequence of images from text prompt.
    Suitable defaults for High-Quality mode (but slow on CPU).
    """
    ensure_dir(out_dir)
    pipe = get_text2img_pipe()
    files = []
    base_seed = int(time.time()) % 1000000
    for i in range(num_frames):
        gen = torch.Generator("cpu").manual_seed(base_seed + i)
        result = pipe(prompt, height=height, width=width, num_inference_steps=steps, generator=gen)
        img = result.images[0]
        path = os.path.join(out_dir, f"frame_{i:03d}.png")
        img.save(path)
        files.append(path)
    return files

def image_prompt_to_frames(init_image_path, prompt, out_dir, num_frames=10, strength=0.65, steps=35):
    """
    Perform img2img for multiple frames to create an animation-like sequence.
    """
    ensure_dir(out_dir)
    pipe = get_img2img_pipe()
    files = []
    init_img = Image.open(init_image_path).convert("RGB")
    base_seed = int(time.time()) % 1000000
    for i in range(num_frames):
        gen = torch.Generator("cpu").manual_seed(base_seed + i)
        out = pipe(prompt=prompt, init_image=init_img, strength=strength, num_inference_steps=steps, generator=gen)
        img = out.images[0]
        path = os.path.join(out_dir, f"frame_{i:03d}.png")
        img.save(path)
        files.append(path)
    return files

def frames_to_video(frames, out_path, fps=12):
    """
    Stitch frames into mp4 using ffmpeg concat demuxer.
    frames: ordered list of file paths
    """
    list_file = out_path + ".txt"
    with open(list_file, "w") as f:
        for p in frames:
            f.write(f"file '{os.path.abspath(p)}'\n")
            # Optionally: set per-frame duration lines if desired
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path
    ]
    subprocess.run(cmd, check=True)
    try:
        os.remove(list_file)
    except:
        pass
    return out_path

def cleanup_dir(d):
    if not os.path.exists(d):
        return
    for root, _, files in os.walk(d):
        for f in files:
            try:
                os.remove(os.path.join(root, f))
            except:
                pass
    try:
        os.rmdir(d)
    except:
        pass

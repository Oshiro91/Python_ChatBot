import torch
from diffusers import DiffusionPipeline

# Check if CUDA is available
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load the pipeline and move it to GPU
pipe = DiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32  # Use float16 for GPU to save memory
)
pipe = pipe.to(device)

# Optional: Enable memory efficient attention if you have limited GPU memory
if device == "cuda":
    pipe.enable_attention_slicing()
    # pipe.enable_xformers_memory_efficient_attention()  # Uncomment if you have xformers installed

prompt = "write your prompt here"
image = pipe(prompt).images[0]
image.save("astronaut_in_jungle.png")

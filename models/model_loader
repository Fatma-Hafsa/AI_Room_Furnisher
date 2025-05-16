import torch
import time
import streamlit as st
from diffusers import (
    StableDiffusionXLInpaintPipeline,
    StableDiffusionXLControlNetInpaintPipeline,
    StableDiffusionXLControlNetPipeline,
    ControlNetModel,
    UniPCMultistepScheduler
)
from transformers import DPTFeatureExtractor, DPTForDepthEstimation
from config.constants import DEVICE
from utils.ui_components import show_loading_spinner

@st.cache_resource(show_spinner=True)
def load_inpainting_model():
    """Charge le modèle d'inpainting pour le mode simple"""
    model_id = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
    pipe = None
    print(f"Attempting to load model {model_id} on {DEVICE}...")

    load_kwargs = {"use_safetensors": True}
    if DEVICE.type == "cuda":
        load_kwargs["torch_dtype"] = torch.float16
        load_kwargs["variant"] = "fp16"
    else: # CPU
        load_kwargs["torch_dtype"] = torch.float32

    try:
        pipe = StableDiffusionXLInpaintPipeline.from_pretrained(model_id, **load_kwargs)
        pipe = pipe.to(DEVICE)
        pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
        if DEVICE.type == "cuda":
            try:
                pipe.enable_xformers_memory_efficient_attention()
            except ImportError:
                print("xformers not available, continuing without it.")
        print(f"Successfully loaded {model_id} on {DEVICE}.")
    except Exception as e:
        print(f"Error loading model {model_id} on {DEVICE}: {e}")
        if DEVICE.type == "cuda": # If CUDA attempt failed, try CPU
            print("CUDA attempt failed. Falling back to CPU.")
            try:
                cpu_load_kwargs = {
                    "torch_dtype": torch.float32,
                    "use_safetensors": True
                }
                pipe = StableDiffusionXLInpaintPipeline.from_pretrained(model_id, **cpu_load_kwargs)
                pipe = pipe.to("cpu") # Explicitly to CPU
                pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
                print(f"Successfully loaded {model_id} on CPU after CUDA failure.")
            except Exception as e_cpu:
                print(f"Error loading model {model_id} on CPU as well: {e_cpu}")
    return pipe

@st.cache_resource(show_spinner=True)
def load_controlnet_pipeline():
    """Charge le pipeline ControlNet pour la génération de meubles"""
    try:
        with st.spinner("Chargement du pipeline ControlNet..."):
            show_loading_spinner("Préparation du modèle ControlNet...")

            controlnet = ControlNetModel.from_pretrained(
                "diffusers/controlnet-depth-sdxl-1.0",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                controlnet=controlnet,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )

            if torch.cuda.is_available():
                pipe.to("cuda")
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                except:
                    pass

            return pipe
    except Exception as e:
        st.error(f"Erreur lors du chargement du modèle de génération: {e}")
        return None

@st.cache_resource(show_spinner=True)
def load_controlnet_inpaint_pipeline():
    """Charge le pipeline ControlNet Inpaint pour le mode IKEA"""
    try:
        with st.spinner("Chargement des modèles d'IA..."):
            show_loading_spinner("Chargement du modèle SDXL ControlNet...")

            controlnet = ControlNetModel.from_pretrained(
                "diffusers/controlnet-depth-sdxl-1.0",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            pipe = StableDiffusionXLControlNetInpaintPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                controlnet=controlnet,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )

            if torch.cuda.is_available():
                pipe = pipe.to("cuda")
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                except:
                    pass
            else:
                pipe = pipe.to("cpu")

            return pipe
    except Exception as e:
        st.error(f"Erreur lors du chargement des modèles: {e}")
        return None

def clear_gpu_memory():
    """Libère la mémoire GPU après utilisation intensive"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        import gc
        gc.collect()

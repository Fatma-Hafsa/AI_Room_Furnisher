import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
import torch
from transformers import DPTFeatureExtractor, DPTForDepthEstimation
import streamlit as st
import uuid

def maintain_aspect_ratio(image, target_size):
    """Redimensionne une image en conservant son ratio d'aspect"""
    if image is None:
        return Image.new("RGB", target_size, (255, 255, 255))

    width, height = image.size
    aspect = width / height

    if aspect > 1:
        new_width = target_size[0]
        new_height = int(new_width / aspect)
    else:
        new_height = target_size[1]
        new_width = int(new_height * aspect)

    new_width = max(1, new_width)
    new_height = max(1, new_height)

    if image.mode == "RGBA":
        resized_img = image.resize((new_width, new_height), Image.LANCZOS)
        new_img = Image.new("RGBA", target_size, (255, 255, 255, 0))
    else:
        resized_img = image.resize((new_width, new_height), Image.LANCZOS)
        new_img = Image.new("RGB", target_size, (255, 255, 255))

    paste_x = (target_size[0] - new_width) // 2
    paste_y = (target_size[1] - new_height) // 2

    if image.mode == "RGBA":
        new_img.paste(resized_img, (paste_x, paste_y), resized_img)
    else:
        new_img.paste(resized_img, (paste_x, paste_y))

    return new_img

def generate_inpainting_mask(image_size, strategy="center_rect", prompt_details=None):
    """Génère un masque blanc sur fond noir pour l'inpainting"""
    # Génère un masque blanc sur fond noir. Par défaut, un rectangle central est rempli.
    width, height = image_size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    if strategy == "center_rect":
        rect_w, rect_h = width // 2, height // 2
        x0, y0 = (width - rect_w) // 2, (height - rect_h) // 2
        x1, y1 = x0 + rect_w, y0 + rect_h
        draw.rectangle([x0, y0, x1, y1], fill=255)
    elif strategy == "full":
        draw.rectangle([0, 0, width, height], fill=255)
    return mask

def generate_rectangle_mask(image, center_ratio=0.7):
    """Génère un masque rectangulaire au centre de l'image"""
    if image is None:
        return None

    width, height = image.size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    # Calcul de la taille du rectangle
    rect_width = int(width * center_ratio)
    rect_height = int(height * center_ratio)

    # Position du rectangle (centré)
    left = (width - rect_width) // 2
    top = (height - rect_height) // 2
    right = left + rect_width
    bottom = top + rect_height

    # Dessiner le rectangle blanc (255) sur fond noir (0)
    draw.rectangle([left, top, right, bottom], fill=255)

    return mask

def generate_smart_mask(original, edited, dilation_factor=25, threshold=30, structure_preservation=0.7):
    """Génère un masque intelligent pour l'inpainting basé sur les différences entre images"""
    try:
        if original.size != edited.size:
            edited = edited.resize(original.size, Image.LANCZOS)

        original_np = np.array(original.convert("RGB"))
        edited_np = np.array(edited.convert("RGB"))

        diff = np.abs(original_np.astype(np.int16) - edited_np.astype(np.int16)).sum(axis=-1)
        furniture_mask = (diff > threshold).astype(np.uint8) * 255

        kernel = np.ones((dilation_factor, dilation_factor), np.uint8)
        dilated_furniture = cv2.dilate(furniture_mask, kernel, iterations=1)

        gray_original = cv2.cvtColor(original_np, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray_original, 50, 150)

        structure_mask = np.zeros_like(gray_original)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(structure_mask, (x1, y1), (x2, y2), 255, 5)

        corners = cv2.cornerHarris(gray_original.astype(np.float32), 2, 3, 0.04)
        corner_mask = np.zeros_like(gray_original)
        corner_mask[corners > 0.01 * corners.max()] = 255
        corner_mask = cv2.dilate(corner_mask, np.ones((3, 3), np.uint8), iterations=2)

        height, width = gray_original.shape
        floor_height = int(height * 0.2)
        floor_mask = np.zeros_like(gray_original)
        floor_mask[height-floor_height:height, :] = 100

        ceiling_height = int(height * 0.1)
        ceiling_mask = np.zeros_like(gray_original)
        ceiling_mask[0:ceiling_height, :] = 100

        combined_structure = np.maximum(structure_mask, corner_mask)
        combined_structure = np.maximum(combined_structure, floor_mask)
        combined_structure = np.maximum(combined_structure, ceiling_mask)

        structure_mask_final = np.minimum(combined_structure, int(255 * structure_preservation)).astype(np.uint8)

        preservation_mask = np.maximum(dilated_furniture, structure_mask_final)
        final_mask = 255 - preservation_mask

        return Image.fromarray(final_mask)
    except Exception as e:
        st.error(f"Erreur lors de la génération du masque: {e}")
        return Image.new("L", original.size, 255)

@st.cache_resource(show_spinner=False)
def get_depth_map(image):
    """Génère une carte de profondeur à partir d'une image"""
    processor = DPTFeatureExtractor.from_pretrained("Intel/dpt-hybrid-midas")
    model = DPTForDepthEstimation.from_pretrained("Intel/dpt-hybrid-midas")

    if image.mode != "RGB":
        image = image.convert("RGB")

    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        depth = outputs.predicted_depth[0].numpy()
        depth = cv2.normalize(depth, None, 0, 255, norm_type=cv2.NORM_MINMAX).astype(np.uint8)
        depth_map = Image.fromarray(depth)

        if depth_map.size != image.size:
            depth_map = depth_map.resize(image.size, Image.LANCZOS)

        return depth_map

def load_furniture_image(item, target_size=(256, 256)):
    """Charge une image de meuble avec transparence en utilisant rembg"""
    try:
        from rembg import remove
        
        if 'image_path' in item and os.path.exists(item['image_path']):
            # Charger l'image originale
            img = Image.open(item['image_path'])

            # Supprimer l'arrière-plan
            with st.spinner("Suppression du fond..."):
                img_no_bg = remove(img)  # Utilisation de rembg pour supprimer le fond

            # S'assurer que l'image est en RGBA
            if img_no_bg.mode != 'RGBA':
                img_no_bg = img_no_bg.convert('RGBA')

            return img_no_bg.resize(target_size, Image.LANCZOS)
        else:
            return Image.new('RGBA', target_size, (0,0,0,0))
    except Exception as e:
        st.warning(f"Erreur de chargement : {str(e)}")
        return Image.new('RGBA', target_size, (0,0,0,0))

def composite_multiple_furniture(room_img, furniture_items):
    """Composite plusieurs meubles sur l'image de la pièce"""
    if room_img is None or not furniture_items:
        return room_img

    try:
        composite = room_img.copy()
        composite = composite.convert("RGBA")

        for item in furniture_items:
            furniture_img = item.get("image")
            if furniture_img is None:
                continue

            # Appliquer la transformation
            rotated = furniture_img.rotate(item.get("rotation", 0), expand=True)
            scaled_width = int(rotated.width * item.get("scale", 0.6))
            scaled_height = int(rotated.height * item.get("scale", 0.6))
            resized = rotated.resize((scaled_width, scaled_height), Image.LANCZOS)

            # Calcul position avec perspective
            x = item.get("position_x", 0) - scaled_width // 2
            y = item.get("position_y", 0) - scaled_height // 2

            # Coller le meuble
            composite.alpha_composite(
                resized,
                dest=(max(0, x), max(0, y)))

        return composite.convert("RGB")

    except Exception as e:
        st.error(f"Erreur de composition : {str(e)}")
        return room_img

def rotate_image(image, angle):
    """Rotation d'une image avec conservation de la transparence"""
    if image is None:
        return None

    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    return image.rotate(angle, resample=Image.BICUBIC, expand=True)

def suggest_furniture_position(room_img, furniture_img, furniture_category, room_type):
    """Suggère une position pour un meuble en fonction de sa catégorie et du type de pièce"""
    if room_img is None or furniture_img is None:
        return (0, 0)

    room_w, room_h = room_img.size
    furniture_w, furniture_h = furniture_img.size

    default_x = (room_w - furniture_w) // 2
    default_y = (room_h - furniture_h) // 2

    position_map = {
        "clock": {"all": (0.8, 0.3)},
        "bed": {"bedroom": (0.5, 0.65), "all": (0.5, 0.65)},
        "sofa": {"living room": (0.5, 0.65), "all": (0.5, 0.65)},
        "table": {"dining room": (0.5, 0.6), "living room": (0.5, 0.7), "all": (0.5, 0.6)},
        "chair": {"dining room": (0.6, 0.6), "office": (0.6, 0.6), "all": (0.5, 0.6)},
        "desk": {"office": (0.7, 0.5), "bedroom": (0.7, 0.5), "all": (0.7, 0.5)},
        "lamp": {"living room": (0.8, 0.5), "bedroom": (0.8, 0.5), "all": (0.8, 0.5)},
        "shelf": {"all": (0.2, 0.5)},
        "rug": {"all": (0.5, 0.8)}
    }

    if furniture_category in position_map:
        if room_type in position_map[furniture_category]:
            x_ratio, y_ratio = position_map[furniture_category][room_type]
        elif "all" in position_map[furniture_category]:
            x_ratio, y_ratio = position_map[furniture_category]["all"]
        else:
            x_ratio, y_ratio = 0.5, 0.5
    else:
        x_ratio, y_ratio = 0.5, 0.5

    x = int(x_ratio * room_w) - (furniture_w // 2)
    y = int(y_ratio * room_h) - (furniture_h // 2)

    x = max(0, min(x, room_w - furniture_w))
    y = max(0, min(y, room_h - furniture_h))

    return (x, y)

def generate_inpainting_prompt(room_type, style, furniture_items):
    """Génère un prompt d'inpainting basé sur le type de pièce, le style et les meubles"""
    room_type_prompts = {
        "living room": "a cozy living room with seating area, rug, coffee table, TV area, bookshelves",
        "bedroom": "a comfortable bedroom with bed, nightstands, wardrobe, dresser, mirror, reading area",
        "dining room": "an elegant dining room with dining table, chairs, sideboard, decorative elements",
        "office": "a productive home office with desk, ergonomic chair, shelving, storage solutions",
        "kitchen": "a functional kitchen with counter space, cooking area, storage cabinets",
        "bathroom": "a clean bathroom with shower/bath, sink, toilet, storage solutions"
    }

    style_prompts = {
        "Scandinave": "Scandinavian style with light woods, minimal design, neutral colors, natural materials",
        "Moderne": "Modern style with clean lines, neutral palette, minimal ornamentation, functional design",
        "Industriel": "Industrial style with raw materials, metal finishes, exposed elements, factory-inspired",
        "Classique": "Classic style with elegant details, symmetry, rich woods, refined details",
        "Minimaliste": "Minimalist style with essential elements, clean design, limited color palette, simple forms"
    }

    room_prompt = room_type_prompts.get(room_type, "a well-decorated room")
    style_prompt = style_prompts.get(style, "contemporary style")

    furniture_categories = list(set([item.get("category", "furniture") for item in furniture_items]))
    furniture_categories_str = ", ".join(furniture_categories)

    complementary_items = []
    if room_type == "living room":
        if "sofa" in furniture_categories and "table" not in furniture_categories:
            complementary_items.append("coffee table")
    elif room_type == "bedroom":
        if "bed" in furniture_categories and "lamp" not in furniture_categories:
            complementary_items.append("bedside lamp")
    elif room_type == "dining room":
        if "table" in furniture_categories and "chair" not in furniture_categories:
            complementary_items.append("matching dining chairs")

    complementary_str = f" with matching {', '.join(complementary_items)}" if complementary_items else ""

    prompt = f"A photorealistic high-resolution image of {room_prompt} in {style_prompt}, containing {furniture_categories_str}{complementary_str}. Interior design by a professional, perfect lighting, cohesive color scheme, impeccable arrangement."

    return prompt

def add_furniture_ai(empty_room_image_pil, prompt_text, model_pipeline, ikea_products=None, ikea_img_desc=None):
    """Ajoute des meubles à une pièce vide en utilisant l'IA"""
    if model_pipeline is None:
        print("AI model pipeline is not loaded. Cannot process image.")
        img_copy = empty_room_image_pil.copy()
        draw = ImageDraw.Draw(img_copy)
        draw.text((10,10), "Error: AI Model Not Loaded in Notebook", fill=(255,0,0))
        return img_copy

    original_size = empty_room_image_pil.size
    # Standard SD input size
    model_input_width, model_input_height = 512, 512
    init_image = empty_room_image_pil.convert("RGB").resize((model_input_width, model_input_height))
    mask_image = generate_inpainting_mask((model_input_width, model_input_height), strategy="center_rect")

    print(f"Running inpainting with prompt: {prompt_text}")
    try:
        # Prépare l'image et génère un masque.
        result_image = model_pipeline(prompt=prompt_text, image=init_image, mask_image=mask_image,
                                      num_inference_steps=50, guidance_scale=7.5).images[0]
        result_image = result_image.resize(original_size)
        print("Inpainting successful.")
    except Exception as e:
        print(f"Error during AI inpainting: {e}")
        result_image = empty_room_image_pil.copy()
        draw = ImageDraw.Draw(result_image)
        draw.text((10, 10), f"AI Error: {str(e)[:100]}...", fill=(255,0,0))
    return result_image

# Dépendances nécessaires
import os
from PIL import Image

import os
import pickle
import json
import random
import glob
import subprocess
import streamlit as st
from config.constants import IKEA_BASE_PATH, IKEA_DATA_PATH, IKEA_DATASET_DIR, IKEA_CATALOG_FILE
from utils.ui_components import show_notification, show_loading_spinner

def load_ikea_metadata():
    """Charge les métadonnées IKEA pour le mode simple"""
    products_dict = None
    img_to_desc = None
    print("Attempting to load IKEA metadata...")
    try:
        # Clone le repo si non présent.
        if not os.path.exists(IKEA_BASE_PATH):
            print(f"IKEA repository not found at {IKEA_BASE_PATH}. Cloning now...")
            subprocess.run(["git", "clone", "https://github.com/IvonaTau/ikea.git", IKEA_BASE_PATH], check=True)
            print("IKEA repository cloned.")
        else:
            print(f"IKEA repository found at {IKEA_BASE_PATH}.")

        with open(os.path.join(IKEA_DATA_PATH, "products_dict.p"), "rb") as f:
            products_dict = pickle.load(f)
        with open(os.path.join(IKEA_DATA_PATH, "img_to_desc.p"), "rb") as f:
            img_to_desc = pickle.load(f)
        print("Successfully loaded IKEA metadata (products_dict, img_to_desc).")
    except FileNotFoundError as fnf_error:
        st.error(f"Error loading IKEA metadata: {fnf_error}. Make sure the IKEA repo is cloned to {IKEA_BASE_PATH} and contains the text_data directory.")
    except Exception as e:
        st.error(f"Error loading IKEA metadata: {e}")
    return products_dict, img_to_desc

def ensure_ikea_dataset():
    """Garantit que le dataset IKEA est disponible, sinon le télécharge"""
    if not os.path.exists(IKEA_DATASET_DIR):
        with st.spinner("Téléchargement du dataset IKEA..."):
            show_loading_spinner("Téléchargement du catalogue IKEA...")
            st.info("Téléchargement du dataset IKEA depuis GitHub...")
            try:
                subprocess.check_call(["git", "clone", "https://github.com/IvonaTau/ikea.git", IKEA_DATASET_DIR])
                show_notification("Dataset IKEA téléchargé avec succès!", "success")
                return True
            except Exception as e:
                st.error(f"Erreur lors du téléchargement du dataset IKEA: {e}")
                os.makedirs(IKEA_DATASET_DIR, exist_ok=True)
                return False
    return True

def scan_ikea_dataset():
    """Analyse le dataset IKEA et crée un catalogue"""
    if not os.path.exists(IKEA_DATASET_DIR):
        return {}

    if os.path.exists(IKEA_CATALOG_FILE):
        try:
            with open(IKEA_CATALOG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            os.remove(IKEA_CATALOG_FILE)

    catalog = {}
    rooms_dir = os.path.join(IKEA_DATASET_DIR, "rooms")
    images_dir = os.path.join(IKEA_DATASET_DIR, "images")

    if not os.path.exists(rooms_dir) and not os.path.exists(images_dir):
        os.makedirs(rooms_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)

    categories = [d for d in os.listdir(images_dir)
                 if os.path.isdir(os.path.join(images_dir, d))]

    if not categories:
        all_images = glob.glob(os.path.join(images_dir, "*.jpg")) + \
                    glob.glob(os.path.join(images_dir, "*.png"))

        default_categories = ["chair", "table", "sofa", "bed", "lamp", "shelf", "clock", "rug", "desk"]

        for category in default_categories:
            cat_dir = os.path.join(images_dir, category)
            os.makedirs(cat_dir, exist_ok=True)

        for img_path in all_images:
            img_name = os.path.basename(img_path)
            category = random.choice(default_categories)
            try:
                os.rename(img_path, os.path.join(images_dir, category, img_name))
            except Exception as e:
                pass

        categories = default_categories

    for category in categories:
        category_path = os.path.join(images_dir, category)

        if not os.path.isdir(category_path):
            continue

        images = glob.glob(os.path.join(category_path, "*.jpg")) + \
                glob.glob(os.path.join(category_path, "*.png"))

        if not images:
            continue

        catalog[category] = []

        for image_path in images:
            filename = os.path.basename(image_path)
            image_id = os.path.splitext(filename)[0]

            catalog[category].append({
                "id": image_id,
                "name": f"IKEA {image_id.upper()}",
                "category": category,
                "description": f"Meuble IKEA de type {category}",
                "image_path": image_path,
                "price": f"{random.randint(49, 499)},99 €"
            })

    os.makedirs(os.path.dirname(IKEA_CATALOG_FILE), exist_ok=True)
    with open(IKEA_CATALOG_FILE, 'w') as f:
        json.dump(catalog, f, indent=2)

    return catalog

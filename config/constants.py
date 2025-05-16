import os
import torch

# Constants
IKEA_DATASET_DIR = "ikea_dataset"
MODELS_DIR = "models"
RESULTS_DIR = "results"
IKEA_CATALOG_FILE = os.path.join(IKEA_DATASET_DIR, "ikea_catalog.json")
IKEA_EMBEDDINGS_FILE = os.path.join(IKEA_DATASET_DIR, "ikea_embeddings.pkl")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IKEA_BASE_PATH = "/content/ikea"
IKEA_DATA_PATH = os.path.join(IKEA_BASE_PATH, "text_data")

# Création des répertoires nécessaires
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Initialisation des états de session
def init_session_state():
    """Initialise tous les états de session nécessaires"""
    if 'selected_furniture_items' not in st.session_state:
        st.session_state.selected_furniture_items = []
    if 'room_img' not in st.session_state:
        st.session_state.room_img = None
    if 'room_type' not in st.session_state:
        st.session_state.room_type = "living room"
    if 'preview_key' not in st.session_state:
        st.session_state.preview_key = 0
    if 'active_furniture_index' not in st.session_state:
        st.session_state.active_furniture_index = 0
    if 'furniture_selection_mode' not in st.session_state:
        st.session_state.furniture_selection_mode = "catalogue"
    if 'last_canvas_img' not in st.session_state:
        st.session_state.last_canvas_img = None
    if 'drag_enabled' not in st.session_state:
        st.session_state.drag_enabled = True
    if 'style_filter' not in st.session_state:
        st.session_state.style_filter = "Tous"
    if 'inpainting_mode' not in st.session_state:
        st.session_state.inpainting_mode = "avec_meubles"
    if 'use_depth_map' not in st.session_state:
        st.session_state.use_depth_map = True
    if 'composited_img' not in st.session_state:
        st.session_state.composited_img = None
    if 'generate_button_clicked' not in st.session_state:
        st.session_state.generate_button_clicked = False
    if 'active_step' not in st.session_state:
        st.session_state.active_step = 1
    if 'show_notification' not in st.session_state:
        st.session_state.show_notification = None
    if 'last_notification_time' not in st.session_state:
        st.session_state.last_notification_time = 0

    # SIMPLE MODE - States
    if 'original_image' not in st.session_state:
        st.session_state.original_image = None
    if 'result_image' not in st.session_state:
        st.session_state.result_image = None
    if 'last_uploaded_filename' not in st.session_state:
        st.session_state.last_uploaded_filename = None
    if 'ikea_products' not in st.session_state or 'ikea_img_desc' not in st.session_state:
        st.session_state.ikea_products = None
        st.session_state.ikea_img_desc = None

# Référence circulaire - importé ici pour éviter les problèmes
import streamlit as st

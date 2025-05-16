import streamlit as st
import time
import uuid
import os
import traceback
import tempfile
from PIL import Image
from io import BytesIO

from models.ikea_data import scan_ikea_dataset, ensure_ikea_dataset
from models.model_loader import load_controlnet_inpaint_pipeline, clear_gpu_memory
from utils.ui_components import (
    show_notification, 
    show_progress_steps, 
    show_loading_spinner,
    show_before_after_comparison, 
    create_styled_upload_area
)
from utils.image_processing import (
    maintain_aspect_ratio,
    get_depth_map,
    generate_smart_mask,
    generate_inpainting_prompt,
    load_furniture_image,
    composite_multiple_furniture,
    suggest_furniture_position
)
from utils.helpers import create_draggable_canvas_alt, display_ikea_furniture, interactive_furniture_control
from config.constants import IKEA_DATASET_DIR

def run_ikea_mode():
    """Exécute le mode IKEA avec sélection de meubles"""
    st.title("🪑 Décorateur de Pièce IKEA avec IA")

    # Présentation améliorée
    st.markdown("""
    <div class="info-card">
        <h3>✨ Transformer votre espace avec l'IA</h3>
        <p>Visualisez comment vos meubles IKEA s'intègreront dans une pièce entièrement décorée. Notre technologie d'IA préserve vos meubles sélectionnés tout en transformant l'espace autour pour créer un design d'intérieur harmonieux et professionnel.</p>
    </div>
    """, unsafe_allow_html=True)

    # Affichage des étapes
    show_progress_steps(st.session_state.active_step)

    with st.sidebar:
        st.header("1. IKEA Dataset")
        if st.button("Initialiser le dataset IKEA"):
            if ensure_ikea_dataset():
                show_notification("Dataset IKEA initialisé avec succès!", "success")

        st.header("2. Type de pièce")
        room_type_map = {
            "Salon": "living room",
            "Chambre": "bedroom",
            "Salle à manger": "dining room",
            "Bureau": "office",
            "Cuisine": "kitchen",
            "Salle de bain": "bathroom"
        }

        room_type_icons = {
            "Salon": "🛋️",
            "Chambre": "🛏️",
            "Salle à manger": "🍽️",
            "Bureau": "💼",
            "Cuisine": "🍳",
            "Salle de bain": "🚿"
        }

        # Afficher les types de pièce avec des icônes
        st.markdown("<div style='display:flex;flex-wrap:wrap;gap:10px;'>", unsafe_allow_html=True)

        room_type_fr = st.selectbox(
            "Type de pièce",
            list(room_type_map.keys()),
            format_func=lambda x: f"{room_type_icons.get(x, '')} {x}",
            index=0
        )
        st.session_state.room_type = room_type_map[room_type_fr]

        st.markdown("</div>", unsafe_allow_html=True)

        st.header("3. Style d'intérieur")
        style = st.select_slider(
            "Style",
            options=["Scandinave", "Moderne", "Industriel", "Classique", "Minimaliste"],
            value="Scandinave"
        )

        st.markdown("### Options de génération")
        # Force l'utilisation de la carte de profondeur
        st.session_state.use_depth_map = st.checkbox("Utiliser la carte de profondeur", value=True)

        # Options avancées dans un expander
        with st.expander("Paramètres Avancés"):
            furniture_density = st.slider("Densité de meubles", 1, 5, 3, 1)
            structure_preservation = st.slider("Préservation de structure", 0.3, 0.9, 0.7, 0.1)
            mask_dilation = st.slider("Protection du meuble (taille)", 10, 50, 25, 5)
            mask_threshold = st.slider("Sensibilité de détection", 10, 50, 30, 5)

        # Liste des meubles sélectionnés
        if st.session_state.selected_furniture_items:
            st.header("Meubles sélectionnés")

            # Création d'une présentation plus visuelle des meubles
            for i, item in enumerate(st.session_state.selected_furniture_items):
                st.markdown(f"""
                <div class="product-card" style="padding:10px;margin:5px 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="font-weight:bold;">{item.get('name', 'Meuble')}</span>
                            <span style="font-size:0.8rem;color:#666;">({item.get('category', 'meuble')})</span>
                        </div>
                        <div>
                            <span style="color:#0051BA;cursor:pointer;" onclick="document.getElementById('edit_{i}').click();">✏️</span>
                            <span style="color:#F44336;cursor:pointer;margin-left:10px;" onclick="document.getElementById('delete_{i}').click();">🗑️</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Boutons cachés pour la fonctionnalité
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Modifier", key=f"edit_{i}"):
                        st.session_state.active_furniture_index = i
                        st.rerun()

                with col2:
                    if st.button("Supprimer", key=f"delete_{i}"):
                        del st.session_state.selected_furniture_items[i]
                        st.session_state.active_furniture_index = max(0, len(st.session_state.selected_furniture_items) - 1)
                        show_notification(f"Meuble supprimé", "info")
                        st.rerun()

            # Bouton pour supprimer tous les meubles
            if st.button("❌ Supprimer tous les meubles", use_container_width=True):
                st.session_state.selected_furniture_items = []
                st.session_state.active_furniture_index = 0
                show_notification("Tous les meubles ont été supprimés", "info")
                st.rerun()

    # ÉTAPE 1: Téléchargement d'image
    if st.session_state.active_step == 1:
        st.header("1. Téléchargez une Pièce")

        # Zone d'upload stylisée
        create_styled_upload_area("Déposez votre image de pièce ici ou cliquez pour parcourir")
        room_file = st.file_uploader("Image de pièce", type=["jpg", "png"], label_visibility="collapsed")

        # Conseils pour de meilleures photos
        st.markdown("""
        <div class="info-card">
            <h4>💡 Conseils pour de meilleurs résultats</h4>
            <ul>
                <li><strong>Utilisez une pièce vide</strong> ou avec peu de meubles</li>
                <li><strong>Assurez-vous d'un bon éclairage</strong> pour une meilleure détection des structures</li>
                <li><strong>Évitez les personnes ou animaux</strong> dans l'image</li>
                <li><strong>Prenez la photo au niveau des yeux</strong> pour une perspective naturelle</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if room_file:
            try:
                room_img_original = Image.open(room_file).convert("RGB")
                target_size = (768, 768)
                room_img = maintain_aspect_ratio(room_img_original, target_size)

                # Afficher l'image téléchargée
                st.success(f"Image chargée avec succès!")
                st.image(room_img, caption="Votre pièce", use_column_width=True)

                # Bouton pour continuer
                if st.button("Continuer vers la sélection de meubles ➡️", use_container_width=True):
                    st.session_state.room_img = room_img
                    st.session_state.active_step = 2
                    show_notification("Image téléchargée avec succès! Passons à la sélection des meubles.", "success")
                    st.rerun()
            except Exception as e:
                st.error(f"Erreur lors du chargement de l'image: {e}")

    # ÉTAPE 2: Sélection des meubles
    elif st.session_state.active_step == 2:
        st.header("2. Sélectionnez vos meubles IKEA")

        # Affichage de l'image de la pièce
        if st.session_state.room_img:
            st.image(st.session_state.room_img, caption=f"Votre {room_type_fr}", use_column_width=True)

        # Onglets pour différentes options de meubles
        input_tab1, input_tab2 = st.tabs(["🛋️ Catalogue IKEA", "📤 Meuble Personnalisé"])

        with input_tab1:
            if os.path.exists(IKEA_DATASET_DIR):
                catalog = scan_ikea_dataset()
                if catalog:
                    display_ikea_furniture(catalog)
            else:
                # Message pour initialiser le dataset
                st.markdown("""
                <div class="info-card" style="text-align:center;">
                    <h3>Catalogue IKEA non initialisé</h3>
                    <p>Pour accéder à notre catalogue de meubles IKEA, veuillez cliquer sur le bouton ci-dessous.</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("📚 Initialiser le catalogue IKEA", use_container_width=True):
                    if ensure_ikea_dataset():
                        show_notification("Catalogue IKEA initialisé avec succès!", "success")
                        st.rerun()

        with input_tab2:
            st.subheader("Télécharger un Meuble Personnalisé")

            # Sélection de catégorie avec icônes
            custom_categories = {"sofa": "🛋️", "chair": "🪑", "table": "🪟", "bed": "🛏️",
                                "desk": "🖥️", "lamp": "💡", "shelf": "📚", "clock": "🕰️", "rug": "🧶"}

            category_cols = st.columns(3)

            for i, (cat, icon) in enumerate(list(custom_categories.items())[:3]):
                with category_cols[i]:
                    if st.button(f"{icon} {cat.capitalize()}", key=f"cat_btn_{cat}", use_container_width=True):
                        st.session_state.custom_category = cat

            category_cols = st.columns(3)
            for i, (cat, icon) in enumerate(list(custom_categories.items())[3:6]):
                with category_cols[i]:
                    if st.button(f"{icon} {cat.capitalize()}", key=f"cat_btn_{cat}", use_container_width=True):
                        st.session_state.custom_category = cat

            category_cols = st.columns(3)
            for i, (cat, icon) in enumerate(list(custom_categories.items())[6:]):
                with category_cols[i]:
                    if st.button(f"{icon} {cat.capitalize()}", key=f"cat_btn_{cat}", use_container_width=True):
                        st.session_state.custom_category = cat

            # Utiliser la catégorie sélectionnée ou définir une valeur par défaut
            custom_category = st.session_state.get('custom_category', 'sofa')

            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

            # Zone d'upload pour le meuble
            create_styled_upload_area(f"Téléchargez une image de {custom_category} (PNG avec fond transparent)", key="furniture_upload")
            furniture_file = st.file_uploader("Image de meuble", type=["png"], key="furniture_uploader", label_visibility="collapsed")

            col1, col2 = st.columns(2)
            with col1:
                furniture_name = st.text_input("Nom du meuble", value=f"Mon {custom_category}")
            with col2:
                furniture_price = st.text_input("Prix (optionnel)", value="", placeholder="ex: 299,99 €")

            if furniture_file and st.button("➕ Ajouter ce meuble au projet", use_container_width=True):
                try:
                    with st.spinner("Préparation du meuble..."):
                        furniture_img = Image.open(furniture_file).convert("RGBA")
                        unique_id = str(uuid.uuid4())
                        furniture_item = {
                            "id": unique_id,
                            "name": furniture_name,
                            "category": custom_category,
                            "description": f"Meuble personnalisé de type {custom_category}",
                            "price": furniture_price if furniture_price else "Prix non spécifié",
                            "image": furniture_img,
                            "position_x": 0,
                            "position_y": 0,
                            "scale": 0.6,
                            "rotation": 0
                        }
                        st.session_state.selected_furniture_items.append(furniture_item)
                        st.session_state.active_furniture_index = len(st.session_state.selected_furniture_items) - 1

                        if st.session_state.room_img:
                            w, h = st.session_state.room_img.size
                            suggested_pos = suggest_furniture_position(
                                st.session_state.room_img,
                                furniture_img,
                                custom_category,
                                st.session_state.room_type
                            )
                            furniture_item["position_x"] = suggested_pos[0]
                            furniture_item["position_y"] = suggested_pos[1]

                        show_notification(f"✅ {furniture_name} ajouté à votre projet!", "success")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors du chargement du meuble: {e}")

        # Navigation entre les étapes
        nav_col1, nav_col2 = st.columns(2)

        with nav_col1:
            if st.button("⬅️ Retour à l'étape précédente", use_container_width=True):
                st.session_state.active_step = 1
                st.rerun()

        with nav_col2:
            # Activation conditionnelle du bouton suivant
            if len(st.session_state.selected_furniture_items) > 0:
                if st.button("Continuer vers le positionnement ➡️", use_container_width=True):
                    st.session_state.active_step = 3
                    show_notification("Passons au positionnement des meubles!", "success")
                    st.rerun()
            else:
                st.button("Continuer vers le positionnement ➡️", disabled=True, use_container_width=True)
                st.info("Veuillez sélectionner au moins un meuble pour continuer.")

    # ÉTAPE 3: Positionnement des meubles
    elif st.session_state.active_step == 3 and st.session_state.room_img and st.session_state.selected_furniture_items:
        st.header("3. Positionnez vos meubles")

        st.markdown("""
        <div class="info-card">
            <h4>🔍 Guide de positionnement</h4>
            <p>Utilisez les contrôles à droite pour ajuster la position, la rotation et l'échelle de chaque meuble.
            Vous pouvez également cliquer sur les positions prédéfinies pour un placement rapide.</p>
        </div>
        """, unsafe_allow_html=True)

        # Interface de positionnement améliorée
        composited_img = interactive_furniture_control(
            st.session_state.room_img,
            st.session_state.selected_furniture_items,
            st.session_state.active_furniture_index,
            st.session_state.room_type
        )

        # Navigation entre les étapes
        nav_col1, nav_col2 = st.columns(2)

        with nav_col1:
            if st.button("⬅️ Retour à la sélection de meubles", use_container_width=True):
                st.session_state.active_step = 2
                st.rerun()

        with nav_col2:
            if composited_img:
                if st.button("🎨 Générer la pièce décorée", use_container_width=True, key="generate_button"):
                    st.session_state.composited_img = composited_img
                    st.session_state.active_step = 4
                    st.session_state.generate_button_clicked = True
                    show_notification("Lancement de la génération IA...", "info")
                    st.rerun()

    # ÉTAPE 4: Génération et affichage des résultats
    elif st.session_state.active_step == 4 and st.session_state.generate_button_clicked:
        st.header("4. Votre design d'intérieur généré par IA")

        # Préparation des masques et cartes de profondeur
        with st.spinner("Préparation des masques et analyse de la profondeur..."):
            try:
                # Utilisation de l'image composite stockée dans session state
                source_img = st.session_state.composited_img

                # Vérifier que source_img est disponible
                if source_img is None:
                    st.error("Image composite non disponible. Veuillez réessayer.")
                    st.session_state.generate_button_clicked = False
                    st.session_state.active_step = 3
                    st.rerun()

                # Génération du masque intelligent
                mask_img = generate_smart_mask(
                    st.session_state.room_img,
                    source_img,
                    dilation_factor=mask_dilation,
                    threshold=mask_threshold,
                    structure_preservation=structure_preservation
                )

                # Génération de la carte de profondeur
                if st.session_state.use_depth_map:
                    depth_map = get_depth_map(source_img)
                else:
                    depth_map = None

                # Affichage des images techniques
                st.subheader("Analyse technique de l'image")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("<h5>Image originale</h5>", unsafe_allow_html=True)
                    st.image(st.session_state.room_img, use_column_width=True)

                with col2:
                    st.markdown("<h5>Masque d'inpainting</h5>", unsafe_allow_html=True)
                    st.image(mask_img, use_column_width=True)

                with col3:
                    if depth_map:
                        st.markdown("<h5>Carte de profondeur</h5>", unsafe_allow_html=True)
                        st.image(depth_map, use_column_width=True)
                    else:
                        st.markdown("<h5>Carte de profondeur</h5>", unsafe_allow_html=True)
                        st.info("Carte de profondeur désactivée")

                # Génération du prompt avancé pour l'IA
                prompt = generate_inpainting_prompt(
                    st.session_state.room_type,
                    style,
                    st.session_state.selected_furniture_items
                )

                with st.expander("Voir le prompt de génération"):
                    st.code(prompt, language="text")

            except Exception as e:
                st.error(f"Erreur lors de la préparation des masques: {e}")
                st.session_state.generate_button_clicked = False
                st.session_state.active_step = 3
                st.rerun()

        # Phase de génération avec l'IA
        with st.spinner("Génération en cours avec IA..."):
            try:
                # Charger le modèle
                pipe = load_controlnet_inpaint_pipeline()

                if pipe is None:
                    st.error("Impossible de charger les modèles d'IA.")
                    st.session_state.generate_button_clicked = False
                    st.session_state.active_step = 3
                    st.rerun()

                # Animation de progression
                st.subheader("Génération en cours...")

                progress_bar = st.progress(0)
                status_text = st.empty()

                steps = ["Analyse de la pièce", "Préparation des textures", "Génération du design", "Ajustement de l'éclairage", "Finalisation"]

                for i, step in enumerate(steps):
                    status_text.markdown(f"<h4>{step}</h4>", unsafe_allow_html=True)
                    for j in range(20):
                        time.sleep(0.05)
                        progress_bar.progress((i * 20 + j + 1) / 100)

                # Vérifier que source_img n'est pas None avant de l'utiliser
                if source_img is None:
                    st.error("Image source non disponible. Veuillez réessayer.")
                    st.session_state.generate_button_clicked = False
                    st.session_state.active_step = 3
                    st.rerun()

                # Génération avec le modèle IA
                negative_prompt = "distorted, poor quality, blur, lowres, bad anatomy, bad proportions, floating furniture, unrealistic layout"

                result = pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    image=source_img,
                    mask_image=mask_img,
                    control_image=depth_map if st.session_state.use_depth_map else None,
                    num_inference_steps=40,
                    guidance_scale=7.5,
                )

                # Libération de la mémoire GPU
                clear_gpu_memory()

                result_img = result.images[0]

                # Affichage des résultats
                st.subheader("🎉 Votre nouvel intérieur")

                # Comparaison avant/après
                st.markdown("<h3>Avant / Après</h3>", unsafe_allow_html=True)
                show_before_after_comparison(st.session_state.room_img, result_img)

                # Image finale haute résolution
                st.markdown("<h3>Résultat final</h3>", unsafe_allow_html=True)
                st.image(result_img, use_column_width=True)

                # Options de téléchargement
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                    result_img.save(tmpfile.name)

                    dl_col1, dl_col2 = st.columns(2)
                    with dl_col1:
                        st.download_button(
                            "📥 Télécharger le résultat HD",
                            data=open(tmpfile.name, "rb"),
                            file_name=f"ikea_design_{int(time.time())}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    with dl_col2:
                        if st.button("🔄 Créer un nouveau design", use_container_width=True):
                            st.session_state.generate_button_clicked = False
                            st.session_state.active_step = 1
                            show_notification("Commençons un nouveau projet!", "success")
                            st.rerun()

                # Suggestions et feedback
                st.markdown("""
                <div class="info-card">
                    <h4>💡 Qu'en pensez-vous?</h4>
                    <p>Votre avis nous aide à améliorer notre IA. Comment évaluez-vous le résultat?</p>
                </div>
                """, unsafe_allow_html=True)

                feedback_col1, feedback_col2, feedback_col3, feedback_col4 = st.columns(4)

                with feedback_col1:
                    if st.button("😍 Parfait!", use_container_width=True):
                        show_notification("Merci pour votre feedback positif!", "success")

                with feedback_col2:
                    if st.button("👍 Pas mal", use_container_width=True):
                        show_notification("Merci pour votre feedback!", "success")

                with feedback_col3:
                    if st.button("😐 Moyen", use_container_width=True):
                        show_notification("Merci pour votre retour. Nous nous améliorons constamment!", "info")

                with feedback_col4:
                    if st.button("👎 À améliorer", use_container_width=True):
                        show_notification("Merci pour votre honnêteté! Nous travaillons à améliorer notre IA.", "info")

                # Suggestions pour aller plus loin
                st.markdown("""
                <div class="info-card">
                    <h4>✨ Et maintenant?</h4>
                    <ul>
                        <li><strong>Partagez votre design</strong> avec vos amis ou votre designer d'intérieur</li>
                        <li><strong>Visitez un magasin IKEA</strong> avec cette image pour trouver des meubles similaires</li>
                        <li><strong>Essayez différents styles</strong> pour voir d'autres possibilités d'aménagement</li>
                        <li><strong>Créez un nouveau design</strong> pour une autre pièce de votre maison</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erreur pendant la génération: {str(e)}")
                st.error(traceback.format_exc())
                show_notification("Une erreur est survenue pendant la génération", "error")

            # Réinitialiser l'état pour éviter des générations répétées
            st.session_state.generate_button_clicked = False

    # Cas où aucune étape n'est active ou manque d'éléments nécessaires
    elif not st.session_state.room_img:
        # Message d'accueil et guide de démarrage
        st.markdown("""
        <div class="info-card">
            <h3>👋 Bienvenue au Décorateur de Pièce IKEA avec IA!</h3>
            <p>Transformez facilement n'importe quelle pièce avec notre outil de design d'intérieur intelligent.</p>
        </div>
        """, unsafe_allow_html=True)

        # Guide visuel des étapes
        st.markdown("<h3>Comment ça fonctionne</h3>", unsafe_allow_html=True)

        steps_col1, steps_col2, steps_col3 = st.columns(3)

        with steps_col1:
            st.markdown("""
            <div class="info-card">
                <h4>1️⃣ Téléchargez votre pièce</h4>
                <p>Commencez par télécharger une photo de votre pièce vide ou peu meublée.</p>
                <img src="https://www.ikea.com/images/un-salon-vide-moderne-avec-mur-blanc-et-plancher-en-bois-pre-fa9a32f2a7c3fb2eb87e5379aebc54b2.jpg" style="width:100%; border-radius:8px; margin-top:10px;">
            </div>
            """, unsafe_allow_html=True)

        with steps_col2:
            st.markdown("""
            <div class="info-card">
                <h4>2️⃣ Sélectionnez vos meubles</h4>
                <p>Parcourez notre catalogue et ajoutez les meubles IKEA que vous souhaitez visualiser.</p>
                <img src="https://www.ikea.com/images/un-canape-modulaire-kivik-gris-clair-avec-une-chaise-longue-c9ef3126b8efd6e1de5f91407eb4dbb7.jpg" style="width:100%; border-radius:8px; margin-top:10px;">
            </div>
            """, unsafe_allow_html=True)

        with steps_col3:
            st.markdown("""
            <div class="info-card">
                <h4>3️⃣ Générez votre design</h4>
                <p>Notre IA transforme votre pièce en un intérieur professionnel avec vos meubles.</p>
                <img src="https://www.ikea.com/images/un-salon-confortable-avec-canape-et-fauteuil-gris-table-bass-4520aa062a6a4b7f54beba71f9e3693e.jpg" style="width:100%; border-radius:8px; margin-top:10px;">
            </div>
            """, unsafe_allow_html=True)

        # Bouton pour commencer
        st.markdown("<div style='text-align:center; margin:30px 0;'>", unsafe_allow_html=True)
        if st.button("🚀 Commencer mon projet", use_container_width=True):
            st.session_state.active_step = 1
            show_notification("C'est parti! Commençons par télécharger une image.", "success")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Information sur le dataset IKEA
        if not os.path.exists(IKEA_DATASET_DIR):
            st.warning("Pour accéder au catalogue IKEA, veuillez d'abord l'initialiser en cliquant sur le bouton dans la barre latérale.")

        # Témoignages utilisateurs
        st.markdown("<h3>Ce que disent nos utilisateurs</h3>", unsafe_allow_html=True)
        testimonial_col1, testimonial_col2 = st.columns(2)

        with testimonial_col1:
            st.markdown("""
            <div class="info-card">
                <p style="font-style:italic;">"J'ai pu visualiser mon salon avant même d'acheter les meubles. L'outil m'a aidé à prendre confiance dans mes choix de design!"</p>
                <p style="text-align:right;"><strong>— Sarah M.</strong></p>
            </div>
            """, unsafe_allow_html=True)

        with testimonial_col2:
            st.markdown("""
            <div class="info-card">
                <p style="font-style:italic;">"Incroyable de voir comment l'IA a transformé ma pièce vide en un espace chaleureux et fonctionnel. Très impressionné!"</p>
                <p style="text-align:right;"><strong>— Thomas K.</strong></p>
            </div>
            """, unsafe_allow_html=True)

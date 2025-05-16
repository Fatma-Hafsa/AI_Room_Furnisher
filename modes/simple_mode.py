import streamlit as st
import time
import io
import requests
from PIL import Image
from io import BytesIO

from models.model_loader import load_inpainting_model
from models.ikea_data import load_ikea_metadata
from utils.image_processing import generate_inpainting_mask, add_furniture_ai
from utils.ui_components import create_styled_upload_area, show_loading_spinner, show_notification

def run_simple_mode():
    """Exécute le mode simple (inpainting direct)"""
    st.title("🛋️ AI Room Furnisher")

    # Introduction améliorée
    st.markdown("""
    <div class="info-card">
        <h3>✨ Meublez votre pièce en un instant</h3>
        <p>Téléchargez simplement une photo de pièce vide, décrivez les meubles que vous souhaitez, et laissez notre IA transformer votre espace.</p>
    </div>
    """, unsafe_allow_html=True)

    # Structure en colonnes principales
    col1, col2 = st.columns(2)

    with col1:
        st.header("1. Votre pièce vide")

        # Zone d'upload stylisée
        create_styled_upload_area("Déposez votre image de pièce vide ici")
        uploaded_file = st.file_uploader("Image de pièce vide", type=["png", "jpg", "jpeg"], key="simple_uploader", label_visibility="collapsed")

        if uploaded_file is not None:
            if st.session_state.last_uploaded_filename != uploaded_file.name:
                st.session_state.original_image = Image.open(uploaded_file)
                st.session_state.result_image = None
                st.session_state.last_uploaded_filename = uploaded_file.name

            # Afficher l'image téléchargée
            st.image(st.session_state.original_image, caption="Pièce vide téléchargée", use_column_width=True)
        else:
            # Exemples de pièces pour démarrage rapide
            st.subheader("Ou essayez un exemple")
            example_col1, example_col2 = st.columns(2)

            examples = [
                {"name": "Salon moderne", "image": "https://www.ikea.com/images/un-salon-vide-avec-murs-blancs-et-sol-en-bois-pret-a-etre-am-f7b7e7df783b81120af65a389512fcc0.jpg"},
                {"name": "Bureau épuré", "image": "https://www.ikea.com/images/une-piece-vide-avec-murs-blancs-et-sol-en-bois-prete-a-etre--fb94ce7a9a9f0e2a16fa41b8273f2ac4.jpg"}
            ]

            with example_col1:
                st.image(examples[0]["image"], caption=examples[0]["name"], use_column_width=True)
                if st.button("Utiliser cet exemple", key="simple_ex1"):
                    try:
                        response = requests.get(examples[0]["image"])
                        st.session_state.original_image = Image.open(BytesIO(response.content))
                        st.session_state.result_image = None
                        st.session_state.last_uploaded_filename = "example_living_room.jpg"
                        show_notification("Exemple chargé avec succès!", "success")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")

            with example_col2:
                st.image(examples[1]["image"], caption=examples[1]["name"], use_column_width=True)
                if st.button("Utiliser cet exemple", key="simple_ex2"):
                    try:
                        response = requests.get(examples[1]["image"])
                        st.session_state.original_image = Image.open(BytesIO(response.content))
                        st.session_state.result_image = None
                        st.session_state.last_uploaded_filename = "example_office.jpg"
                        show_notification("Exemple chargé avec succès!", "success")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")

    with col2:
        st.header("2. Résultat avec meubles")

        # Afficher le résultat s'il existe
        if st.session_state.result_image is not None:
            st.image(st.session_state.result_image, caption="Pièce meublée par l'IA", use_column_width=True)

            # Bouton de téléchargement
            img_byte_arr = io.BytesIO()
            st.session_state.result_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            st.download_button(
                label="💾 Télécharger l'image meublée",
                data=img_byte_arr,
                file_name=f"piece_meublee_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True
            )

            # Feedback rapide
            st.markdown("<h4>Qu'en pensez-vous?</h4>", unsafe_allow_html=True)
            feedback_cols = st.columns(4)
            with feedback_cols[0]:
                if st.button("😍", key="simple_love"):
                    show_notification("Merci pour votre feedback!", "success")
            with feedback_cols[1]:
                if st.button("👍", key="simple_good"):
                    show_notification("Merci pour votre feedback!", "success")
            with feedback_cols[2]:
                if st.button("😐", key="simple_ok"):
                    show_notification("Merci pour votre feedback!", "info")
            with feedback_cols[3]:
                if st.button("👎", key="simple_bad"):
                    show_notification("Merci pour votre feedback!", "info")
        else:
            # Placeholder pour le résultat
            st.markdown("""
            <div style="border:1px dashed #0051BA; padding:40px; text-align:center; border-radius:10px; background-color:#f8f9fa; height:300px; display:flex; flex-direction:column; justify-content:center;">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Ikea_logo.svg/1024px-Ikea_logo.svg.png" width="80px" style="margin:0 auto 20px;">
                <p>Le résultat apparaîtra ici</p>
                <p style="font-size:0.8rem; color:#666;">Téléchargez une image et décrivez les meubles souhaités</p>
            </div>
            """, unsafe_allow_html=True)

    # Chargement du modèle et données en arrière-plan
    if 'model_pipeline' not in st.session_state:
        with st.spinner("Chargement du modèle d'IA..."):
            show_loading_spinner("Préparation du modèle d'IA...")
            st.session_state.model_pipeline = load_inpainting_model()

    if 'ikea_products' not in st.session_state or 'ikea_img_desc' not in st.session_state:
        with st.spinner("Chargement des données IKEA..."):
            show_loading_spinner("Préparation du catalogue IKEA...")
            st.session_state.ikea_products, st.session_state.ikea_img_desc = load_ikea_metadata()

    # Section de description des meubles
    st.header("3. Décrivez les meubles souhaités")

    # Suggestions de descriptions
    st.markdown("<p>Suggestions rapides:</p>", unsafe_allow_html=True)

    suggestions = [
        "Un canapé moderne gris avec table basse en verre et tapis",
        "Un bureau en bois avec chaise ergonomique et lampe design",
        "Une table à manger avec quatre chaises et suspension",
        "Un lit double avec tables de chevet et commode assortie"
    ]

    suggestion_cols = st.columns(2)
    for i, sugg in enumerate(suggestions[:2]):
        with suggestion_cols[i]:
            if st.button(sugg, key=f"sugg_{i}_a"):
                st.session_state.furniture_prompt = sugg
                show_notification("Description ajoutée!", "info")
                st.rerun()

    suggestion_cols = st.columns(2)
    for i, sugg in enumerate(suggestions[2:]):
        with suggestion_cols[i]:
            if st.button(sugg, key=f"sugg_{i}_b"):
                st.session_state.furniture_prompt = sugg
                show_notification("Description ajoutée!", "info")
                st.rerun()

    # Zone de texte pour la description
    furniture_prompt = st.text_area(
        "Description détaillée:",
        value=st.session_state.get('furniture_prompt', ''),
        height=100,
        placeholder="Ex: Un canapé confortable gris avec des coussins colorés, une table basse en bois et une étagère moderne",
        key="furniture_prompt"
    )

    # Options avancées
    with st.expander("Options avancées"):
        style_options = ["Scandinave", "Moderne", "Industriel", "Classique", "Minimaliste"]
        selected_style = st.selectbox("Style d'intérieur", options=style_options, index=0)

        quality_level = st.slider("Qualité de génération", min_value=1, max_value=5, value=3,
                                help="Une qualité plus élevée prend plus de temps mais donne de meilleurs résultats")

        room_type_options = ["salon", "chambre", "salle à manger", "bureau", "cuisine", "salle de bain"]
        room_type = st.selectbox("Type de pièce", options=room_type_options, index=0)

        include_ikea = st.checkbox("Mentionner explicitement IKEA dans le prompt", value=True,
                                help="Ajoute 'IKEA style' à votre description pour des résultats plus proches du style IKEA")

    # Bouton de génération
    submit_button = st.button("✨ Générer l'aménagement", use_container_width=True, key="submit_simple",
                            disabled=st.session_state.original_image is None)

    if submit_button and st.session_state.original_image is not None:
        if not furniture_prompt.strip():
            show_notification("Veuillez entrer une description des meubles", "error")
        else:
            with st.spinner("L'IA imagine votre nouvelle pièce..."):
                show_loading_spinner("Génération en cours...")

                # Construction du prompt enrichi
                ikea_mention = "IKEA style" if include_ikea else ""
                enhanced_prompt = f"Un(e) {room_type} en style {selected_style} avec {furniture_prompt}. {ikea_mention}. Design d'intérieur professionnel, éclairage parfait."

                # Affichage du prompt pour les utilisateurs intéressés
                with st.expander("Voir le prompt utilisé"):
                    st.code(enhanced_prompt)

                try:
                    # Animation de progression
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    steps = ["Analyse de la pièce", "Préparation du design", "Création des meubles", "Intégration", "Finalisation"]

                    for i, step in enumerate(steps):
                        status_text.markdown(f"<h4>{step}</h4>", unsafe_allow_html=True)
                        for j in range(20):
                            time.sleep(0.05)  # Simuler le traitement
                            progress_bar.progress((i * 20 + j + 1) / 100)

                    # Récupération du modèle et des données
                    model_pipeline = st.session_state.model_pipeline
                    ikea_products = st.session_state.ikea_products
                    ikea_img_desc = st.session_state.ikea_img_desc

                    # Génération avec le modèle
                    st.session_state.result_image = add_furniture_ai(
                        st.session_state.original_image,
                        enhanced_prompt,
                        model_pipeline,
                        ikea_products,
                        ikea_img_desc
                    )

                    show_notification("Pièce meublée avec succès!", "success")
                    st.rerun()
                except Exception as e:
                    import traceback
                    st.error(f"Erreur pendant le traitement IA: {e}")
                    traceback.print_exc()
                    show_notification("Une erreur est survenue pendant la génération", "error")

    # Guide d'utilisation et conseils
    st.markdown("""
    <div class="info-card">
        <h4>💡 Conseils pour de meilleurs résultats</h4>
        <ul>
            <li><strong>Soyez spécifique</strong> dans votre description (couleurs, matériaux, styles)</li>
            <li><strong>Utilisez des images de pièces vides</strong> pour des résultats optimaux</li>
            <li><strong>Mentionnez l'emplacement</strong> souhaité des meubles (ex: "canapé contre le mur gauche")</li>
            <li><strong>Limitez-vous à 3-5 meubles</strong> par génération pour plus de cohérence</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

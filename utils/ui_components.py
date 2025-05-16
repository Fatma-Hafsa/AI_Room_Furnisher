import streamlit as st
import time

def show_notification(message, type="info"):
    """Affiche une notification toast"""
    st.session_state.show_notification = {"message": message, "type": type}
    st.session_state.last_notification_time = time.time()

def check_notifications():
    """Vérifie et affiche les notifications"""
    if st.session_state.show_notification and time.time() - st.session_state.last_notification_time < 5:
        notification = st.session_state.show_notification
        background_color = "#0051BA" if notification["type"] == "info" else "#4CAF50" if notification["type"] == "success" else "#F44336"

        st.markdown(f"""
        <div class="toast-notification" style="background-color: {background_color};">
            {notification["message"]}
        </div>
        """, unsafe_allow_html=True)

def show_progress_steps(current_step=1):
    """Affiche un indicateur de progression par étapes utilisant uniquement des composants Streamlit natifs"""
    steps = ["Choisir pièce", "Télécharger image", "Ajouter meubles", "Positionner", "Générer"]

    # Utiliser une rangée de colonnes pour créer les étapes
    cols = st.columns(len(steps))

    for i, step_name in enumerate(steps, 1):
        with cols[i-1]:
            # Déterminer l'état visuel de l'étape
            if i < current_step:
                status = "✅"  # Étape terminée
                color = "#4CAF50"
            elif i == current_step:
                status = "🔵"  # Étape active
                color = "#0051BA"
            else:
                status = "⚪"  # Étape à venir
                color = "#888888"

            # Afficher le numéro et le nom de l'étape avec le style approprié
            st.markdown(f"<div style='text-align:center;'><span style='font-size:24px;color:{color};'>{status}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center;color:{color};font-size:0.9em;'><b>Étape {i}</b><br>{step_name}</div>", unsafe_allow_html=True)

def create_styled_upload_area(text, key="upload_area"):
    """Crée une zone d'upload stylisée"""
    st.markdown(f"""
    <div class="upload-area" id="{key}">
        <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 15V3M12 3L8 7M12 3L16 7" stroke="#0051BA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 15V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V15" stroke="#0051BA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <p style="margin-top:15px; font-weight:600; color:#0051BA;">{text}</p>
        <p style="font-size:0.8rem; color:#666;">Formats supportés: JPG, PNG</p>
    </div>
    <script>
        document.getElementById("{key}").addEventListener("click", function() {{
            document.getElementById("fileUploader").click();
        }});
    </script>
    """, unsafe_allow_html=True)

def show_loading_spinner(text="Chargement en cours..."):
    """Affiche un spinner de chargement personnalisé"""
    st.markdown(f"""
    <div style="text-align:center; margin:30px 0;">
        <div class="loading-spinner"></div>
        <p style="margin-top:15px;">{text}</p>
    </div>
    """, unsafe_allow_html=True)

def show_before_after_comparison(before_img, after_img):
    """Affiche une comparaison avant/après avec un slider"""
    import base64
    import streamlit.components.v1 as components
    from io import BytesIO

    # Assurer que les deux images ont la même taille
    if before_img.size != after_img.size:
        after_img = after_img.resize(before_img.size, Image.LANCZOS)

    # Convertir les images en base64
    buffered_before = BytesIO()
    buffered_after = BytesIO()
    before_img.save(buffered_before, format="PNG")
    after_img.save(buffered_after, format="PNG")
    img_str_before = base64.b64encode(buffered_before.getvalue()).decode()
    img_str_after = base64.b64encode(buffered_after.getvalue()).decode()

    # Créer le HTML pour le comparateur de glissement
    comparison_html = f"""
    <style>
        .comparison-container {{
            position: relative;
            width: 100%;
            overflow: hidden;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}

        .comparison-before {{
            width: 100%;
            display: block;
        }}

        .comparison-after {{
            position: absolute;
            top: 0;
            left: 0;
            width: 50%;
            height: 100%;
            overflow: hidden;
            border-right: 2px solid white;
        }}

        .comparison-after img {{
            position: absolute;
            top: 0;
            left: 0;
            width: 200%; /* Le double de la taille pour qu'il s'aligne correctement */
            max-width: none;
        }}

        .comparison-slider {{
            position: absolute;
            top: 0;
            bottom: 0;
            left: 50%;
            width: 2px;
            background: white;
            cursor: ew-resize;
        }}

        .comparison-slider:before {{
            content: '⟷';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 24px;
            font-weight: bold;
            background: rgba(0, 81, 186, 0.7);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            line-height: 40px;
            text-align: center;
        }}

        /* Étiquettes avant/après */
        .comparison-label {{
            position: absolute;
            bottom: 20px;
            padding: 5px 10px;
            background: rgba(0, 0, 0, 0.6);
            color: white;
            border-radius: 15px;
            font-weight: bold;
        }}

        .label-before {{
            right: 20px;
        }}

        .label-after {{
            left: 20px;
        }}
    </style>

    <div class="comparison-container">
        <img class="comparison-before" src="data:image/png;base64,{img_str_before}" />
        <div class="comparison-after" id="comparison-after">
            <img src="data:image/png;base64,{img_str_after}" />
        </div>
        <div class="comparison-slider" id="comparison-slider"></div>

        <div class="comparison-label label-before">Avant</div>
        <div class="comparison-label label-after">Après</div>
    </div>

    <script>
        // Wait for the DOM to be loaded
        document.addEventListener('DOMContentLoaded', function() {{
            const slider = document.getElementById('comparison-slider');
            const after = document.getElementById('comparison-after');

            // Set initial position
            after.style.width = '50%';
            slider.style.left = '50%';

            // Add mouse events
            let isDown = false;

            slider.addEventListener('mousedown', function() {{
                isDown = true;
            }});

            document.addEventListener('mouseup', function() {{
                isDown = false;
            }});

            document.addEventListener('mousemove', function(e) {{
                if (!isDown) return;

                const container = slider.parentElement;
                const rect = container.getBoundingClientRect();
                const x = e.clientX - rect.left;

                // Calculate percentage
                let percent = (x / rect.width) * 100;
                percent = Math.max(0, Math.min(100, percent));

                // Update elements
                after.style.width = percent + '%';
                slider.style.left = percent + '%';
            }});

            // Add touch events for mobile
            slider.addEventListener('touchstart', function() {{
                isDown = true;
            }});

            document.addEventListener('touchend', function() {{
                isDown = false;
            }});

            document.addEventListener('touchmove', function(e) {{
                if (!isDown) return;

                const container = slider.parentElement;
                const rect = container.getBoundingClientRect();
                const x = e.touches[0].clientX - rect.left;

                // Calculate percentage
                let percent = (x / rect.width) * 100;
                percent = Math.max(0, Math.min(100, percent));

                // Update elements
                after.style.width = percent + '%';
                slider.style.left = percent + '%';

                // Prevent page scrolling
                e.preventDefault();
            }}, {{ passive: false }});
        }});
    </script>
    """

    # Afficher le comparateur
    components.html(comparison_html, height=500)

# Import dépendant en fin de fichier pour éviter les références circulaires
from PIL import Image

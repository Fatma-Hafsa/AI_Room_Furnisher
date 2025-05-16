import streamlit as st
from static.styles import load_styles
from config.constants import init_session_state
from modes.ikea_mode import run_ikea_mode
from modes.simple_mode import run_simple_mode
from utils.ui_components import check_notifications

# Configuration de la page
st.set_page_config(layout="wide", page_title="IKEA AI Room Designer Pro")

def main():
    # Chargement des styles CSS
    load_styles()
    
    # Initialisation des états de session
    init_session_state()
    
    # Vérifier et afficher les notifications
    check_notifications()

    # Barre latérale commune
    with st.sidebar:
        # Logo et titre
        st.markdown("""
        <div style="display:flex;align-items:center;margin-bottom:20px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Ikea_logo.svg/1024px-Ikea_logo.svg.png" width="50px" style="margin-right:10px;">
            <h2 style="margin:0;">IKEA AI Room Designer</h2>
        </div>
        """, unsafe_allow_html=True)

        # Sélection du mode
        st.header("Mode")
        mode_options = ["Mode IKEA (avec sélection de meubles)", "Mode Simple (inpainting direct)"]
        selected_mode = st.radio("Choisissez votre mode:", mode_options)
        st.session_state.inpainting_mode = "avec_meubles" if selected_mode == "Mode IKEA (avec sélection de meubles)" else "inpainting_direct"

    # Exécution du mode sélectionné
    if st.session_state.inpainting_mode == "avec_meubles":
        run_ikea_mode()
    else:
        run_simple_mode()

    # Pied de page commun
    st.markdown("""
    <div class="footer">
        <p>© 2025 IKEA AI Room Designer | Propulsé par l'intelligence artificielle | Fatma Hafsa et Marwa Rizi</p>
        <p>Ce service utilise des modèles de diffusion stables pour créer des designs d'intérieur personnalisés</p>
    </div>
    """, unsafe_allow_html=True)

# Point d'entrée de l'application
if __name__ == "__main__":
    main()

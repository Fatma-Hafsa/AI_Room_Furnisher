import streamlit as st

def load_styles():
    """Charge tous les styles CSS personnalisés pour l'application"""
    st.markdown("""
    <style>
        /* Variables de couleur IKEA */
        :root {
            --ikea-blue: #0051BA;
            --ikea-yellow: #FFDA1A;
            --ikea-hover: #003D8F;
        }

        /* Styles généraux */
        h1, h2, h3 {
            color: var(--ikea-blue);
        }

        h1 {
            font-weight: 800;
            padding-bottom: 10px;
            border-bottom: 4px solid var(--ikea-yellow);
            margin-bottom: 24px;
        }

        h2 {
            border-left: 5px solid var(--ikea-yellow);
            padding-left: 10px;
            margin-top: 30px;
        }

        /* Cartes pour les éléments d'information */
        .info-card {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-left: 4px solid var(--ikea-blue);
            transition: transform 0.2s;
        }

        .info-card:hover {
            transform: translateY(-5px);
        }

        /* Style pour les boutons */
        button, .stButton>button {
            border-radius: 20px !important;
            font-weight: 600 !important;
            padding: 4px 15px !important;
            transition: all 0.3s ease !important;
        }

        .stButton>button:hover {
            background-color: var(--ikea-hover) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }

        /* Style pour boîtes de sélection */
        .stSelectbox>div>div>div {
            background-color: white !important;
            border-radius: 20px !important;
        }

        /* Cartes de produit */
        .product-card {
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }

        .product-card:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-3px);
        }

        .product-card h4 {
            color: var(--ikea-blue);
            margin-top: 0;
        }

        .product-card .price {
            font-weight: bold;
            color: #333;
            background-color: var(--ikea-yellow);
            padding: 2px 8px;
            border-radius: 10px;
            display: inline-block;
        }

        /* Notifications toast */
        @keyframes fadeInOut {
            0% { opacity: 0; transform: translateY(20px); }
            10% { opacity: 1; transform: translateY(0); }
            90% { opacity: 1; transform: translateY(0); }
            100% { opacity: 0; transform: translateY(-20px); }
        }

        .toast-notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 20px;
            background-color: var(--ikea-blue);
            color: white;
            border-radius: 5px;
            z-index: 999;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            animation: fadeInOut 3s forwards;
        }

        /* Animation de chargement */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(0, 81, 186, 0.2);
            border-radius: 50%;
            border-top: 4px solid var(--ikea-blue);
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }

        /* Zones d'upload personnalisées */
        .upload-area {
            border: 2px dashed var(--ikea-blue);
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            background-color: rgba(0, 81, 186, 0.05);
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .upload-area:hover {
            background-color: rgba(0, 81, 186, 0.1);
        }

        /* Étapes de progression */
        .step-progress {
            display: flex;
            justify-content: space-between;
            margin: 20px 0 30px;
            position: relative;
        }

        /* Animation de fade-in */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .fade-in {
            animation: fadeIn 0.5s ease forwards;
        }

        /* Onglets améliorés */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: white;
            border-radius: 5px 5px 0 0;
            border: 1px solid #eee;
            border-bottom: none;
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            background-color: var(--ikea-yellow) !important;
            color: #333 !important;
        }

        /* Footer */
        .footer {
            margin-top: 50px;
            padding: 20px;
            background-color: #333;
            color: white;
            border-radius: 5px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

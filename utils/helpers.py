import streamlit as st
from PIL import Image

def create_draggable_canvas_alt(room_img, furniture_items, active_index=0):
    """Version alternative du canvas sans dépendance à streamlit-drawable-canvas"""
    composite = composite_multiple_furniture(room_img, furniture_items)
    st.image(composite, caption="Vue de la pièce avec meubles", use_column_width=True)

    # Boutons de déplacement améliorés
    st.markdown("<div style='display: flex; gap: 10px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Gauche", key=f"left_{active_index}"):
            furniture_items[active_index]["position_x"] = max(0, furniture_items[active_index]["position_x"] - 20)
            return True
    with col2:
        if st.button("⬆️ Haut", key=f"up_{active_index}"):
            furniture_items[active_index]["position_y"] = max(0, furniture_items[active_index]["position_y"] - 20)
            return True
    with col3:
        if st.button("➡️ Droite", key=f"right_{active_index}"):
            furniture_items[active_index]["position_x"] = min(room_img.width, furniture_items[active_index]["position_x"] + 20)
            return True

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("↕️ Centre V", key=f"center_v_{active_index}"):
            furniture_items[active_index]["position_y"] = room_img.height // 2
            return True
    with col2:
        if st.button("⬇️ Bas", key=f"down_{active_index}"):
            furniture_items[active_index]["position_y"] = min(room_img.height, furniture_items[active_index]["position_y"] + 20)
            return True
    with col3:
        if st.button("↔️ Centre H", key=f"center_h_{active_index}"):
            furniture_items[active_index]["position_x"] = room_img.width // 2
            return True

    st.markdown("</div>", unsafe_allow_html=True)

    # Positions prédéfinies avec grille stylisée
    st.markdown("""
    <div style="margin: 20px 0;">
        <h4 style="margin-bottom: 15px;">👉 Cliquez sur l'un de ces emplacements pour positionner le meuble :</h4>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
    """, unsafe_allow_html=True)

    positions = [
        (0.2, 0.2), (0.5, 0.2), (0.8, 0.2),
        (0.2, 0.5), (0.5, 0.5), (0.8, 0.5),
        (0.2, 0.8), (0.5, 0.8), (0.8, 0.8)
    ]

    position_cols = st.columns(3)
    for i, pos in enumerate(positions):
        col_index = i % 3
        with position_cols[col_index]:
            if st.button(f"Position {i+1}", key=f"pos_{i}_{active_index}"):
                furniture_items[active_index]["position_x"] = int(pos[0] * room_img.width)
                furniture_items[active_index]["position_y"] = int(pos[1] * room_img.height)
                return True

    st.markdown("</div></div>", unsafe_allow_html=True)

    return False

def display_ikea_furniture(catalog, style_filter="Tous"):
    """Affiche les meubles IKEA du catalogue avec filtrage par style"""
    if not catalog or not isinstance(catalog, dict):
        st.warning("Catalogue IKEA indisponible.")
        return None

    categories = list(catalog.keys())

    if not categories:
        st.warning("Aucune catégorie trouvée.")
        return None

    # Sélection de catégorie avec un style amélioré
    st.markdown("<h3>Catégories de meubles</h3>", unsafe_allow_html=True)

    # Affichage des catégories sous forme de boutons stylisés
    category_cols = st.columns(len(categories) if len(categories) < 6 else 5)

    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = categories[0]

    for i, cat in enumerate(categories[:5]):
        with category_cols[i]:
            cat_name = cat.capitalize()
            is_selected = st.session_state.selected_category == cat
            button_style = "primary" if is_selected else "secondary"

            if st.button(cat_name, key=f"cat_{cat}", use_container_width=True, type=button_style):
                st.session_state.selected_category = cat
                from utils.ui_components import show_notification
                show_notification(f"Catégorie {cat_name} sélectionnée", "info")
                st.rerun()

    category = st.session_state.selected_category

    # Filtrage et recherche
    search_col1, search_col2 = st.columns([3, 1])

    with search_col1:
        search_term = st.text_input("🔍 Rechercher un meuble", key="search_furniture", placeholder="Ex: table, chaise...")

    with search_col2:
        st.write("&nbsp;")  # Espacement
        show_in_stock = st.checkbox("En stock uniquement", value=True)

    # Affichage des meubles avec style amélioré
    if category in catalog and catalog[category]:
        # Filtrage par recherche
        filtered_items = catalog[category]
        if search_term:
            search_term = search_term.lower()
            filtered_items = [item for item in catalog[category]
                             if search_term in item.get('name', '').lower()
                             or search_term in item.get('description', '').lower()
                             or search_term in item.get('category', '').lower()]

        st.markdown(f"### Meubles disponibles ({len(filtered_items)} produits)")

        if not filtered_items:
            st.info(f"Aucun meuble trouvé pour la recherche '{search_term}'")

        # Affichage des meubles en grille
        cols = st.columns(3)
        for i, item in enumerate(filtered_items):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="product-card">
                    <h4>{item.get('name', 'Meuble IKEA')}</h4>
                    <p>{item.get('description', '')}</p>
                    <p class="price">{item.get('price', '99,99 €')}</p>
                </div>
                """, unsafe_allow_html=True)

                import os
                if os.path.exists(item.get('image_path', '')):
                    st.image(item['image_path'], use_column_width=True)

                if st.button(f"Ajouter au projet ➕", key=f"add_{item['id']}"):
                    from utils.image_processing import load_furniture_image
                    furniture_img = load_furniture_image(item)
                    import uuid
                    furniture_item = {
                        "id": str(uuid.uuid4()),
                        "name": item.get('name', 'Meuble IKEA'),
                        "category": category,
                        "image": furniture_img,
                        "position_x": 0,
                        "position_y": 0,
                        "scale": 0.6,
                        "rotation": 0,
                        "source": "ikea"
                    }
                    st.session_state.selected_furniture_items.append(furniture_item)
                    st.session_state.active_furniture_index = len(st.session_state.selected_furniture_items) - 1
                    from utils.ui_components import show_notification
                    show_notification(f"✅ {item['name']} ajouté!", "success")
    else:
        st.warning(f"Aucun meuble dans la catégorie {category}.")

    return None

def interactive_furniture_control(room_img, furniture_items, active_index=0, room_type="living room"):
    """Contrôle interactif du positionnement des meubles"""
    if not furniture_items:
        st.warning("Aucun meuble sélectionné.")
        return None

    if active_index >= len(furniture_items):
        active_index = 0

    active_item = furniture_items[active_index]
    furniture_img = active_item.get("image")

    if furniture_img is None:
        st.warning("Image du meuble non disponible.")
        return None

    # Mise en page principale
    col1, col2 = st.columns([3, 1])

    with col2:
        # Carte d'information du meuble actif
        st.markdown(f"""
        <div class="info-card">
            <h3>{active_item.get('name', 'Meuble')}</h3>
            <p>Meuble {active_index + 1} sur {len(furniture_items)}</p>
            <div style="background-color:#F0F0F0; border-radius:15px; padding:3px 10px; display:inline-block; margin-top:5px;">
                {active_item.get('category', 'meuble')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation entre les meubles
        nav_col1, nav_col2 = st.columns(2)
        with nav_col1:
            if st.button("◀ Précédent", disabled=active_index <= 0, use_container_width=True):
                st.session_state.active_furniture_index -= 1
                from utils.ui_components import show_notification
                show_notification(f"Navigation vers le meuble précédent", "info")
                st.rerun()
        with nav_col2:
            if st.button("Suivant ▶", disabled=active_index >= len(furniture_items) - 1, use_container_width=True):
                st.session_state.active_furniture_index += 1
                from utils.ui_components import show_notification
                show_notification(f"Navigation vers le meuble suivant", "info")
                st.rerun()

        # Contrôles de transformation
        st.markdown("<h4>Transformation</h4>", unsafe_allow_html=True)
        rotation = st.slider("Rotation", -180, 180, active_item.get("rotation", 0), key=f"rot_{active_index}")
        scale = st.slider("Échelle", 0.1, 2.0, active_item.get("scale", 0.6), 0.05, key=f"scale_{active_index}")

        st.markdown("<h4>Position</h4>", unsafe_allow_html=True)
        col_x, col_y = st.columns(2)
        with col_x:
            x = st.number_input("X", 0, room_img.width, active_item["position_x"], key=f"x_{active_index}")
        with col_y:
            y = st.number_input("Y", 0, room_img.height, active_item["position_y"], key=f"y_{active_index}")

        # Mise à jour des valeurs
        furniture_items[active_index]["rotation"] = rotation
        furniture_items[active_index]["scale"] = scale
        furniture_items[active_index]["position_x"] = x
        furniture_items[active_index]["position_y"] = y

        # Actions avancées
        st.markdown("<h4>Actions</h4>", unsafe_allow_html=True)
        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button("🎯 Placement auto", use_container_width=True):
                from utils.image_processing import suggest_furniture_position
                category = active_item.get("category", "generic")
                new_pos = suggest_furniture_position(room_img, furniture_img, category, room_type)
                furniture_items[active_index]["position_x"] = new_pos[0]
                furniture_items[active_index]["position_y"] = new_pos[1]
                from utils.ui_components import show_notification
                show_notification("Position optimisée automatiquement", "success")
                st.rerun()

        with action_col2:
            if st.button("🗑️ Supprimer", use_container_width=True):
                removed_name = furniture_items[active_index].get("name", "Meuble")
                del furniture_items[active_index]
                st.session_state.active_furniture_index = max(0, len(furniture_items) - 1)
                from utils.ui_components import show_notification
                show_notification(f"{removed_name} supprimé", "info")
                st.rerun()

    with col1:
        # Canvas pour le positionnement
        st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
        if create_draggable_canvas_alt(room_img, furniture_items, active_index):
            st.rerun()

        # Prévisualisation composite
        from utils.image_processing import composite_multiple_furniture
        composite_img = composite_multiple_furniture(room_img, furniture_items)
        st.markdown("</div>", unsafe_allow_html=True)

    return composite_img

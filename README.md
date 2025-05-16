# AI ROOM FURNISHER

## Présentation

 AI Room FURNISHER est une application avancée de design d'intérieur propulsée par l'intelligence artificielle. Elle permet aux utilisateurs de visualiser comment des meubles IKEA ou leur propre meubles s'intégreront dans une pièce entièrement décorée par l'IA.

## Fonctionnalités

- **Mode IKEA**: Sélectionnez des meubles IKEA ou uploader votre propre meuble et placez-les dans votre pièce
- **Mode Simple**: Générez directement un design d'intérieur à partir d'une description textuelle
- **Placement intelligent**: Positionnez vos meubles avec précision
- **Styles variés**: Choisissez parmi plusieurs styles d'intérieur (Scandinave, Moderne, Industriel, etc.)
- **Comparaison avant/après**: Visualisez facilement la transformation de votre espace

## Installation

1. Clonez ce dépôt
2. Installez les dépendances:
```
pip install -r requirements.txt
```
3. Lancez l'application:
```
streamlit run app.py
```
## Structure 
ia-room-furnisher/
│
├── README.md                 # Documentation du projet avec crédits à votre équipe
├── requirements.txt          # Dépendances du projet
├── app.py                    # Point d'entrée principal
│
├── config/                   # Configuration
│   ├── __init__.py
│   └── constants.py          # Constantes et configuration
│
├── static/                   # Ressources statiques
│   └── styles.py             # Styles CSS
│
├── models/                   # Modèles IA et données
│   ├── __init__.py
│   ├── model_loader.py       # Chargement des modèles IA
│   └── ikea_data.py          # Gestion des données IKEA
│
├── utils/                    # Utilitaires et fonctions
│   ├── __init__.py
│   ├── image_processing.py   # Traitement d'image
│   ├── ui_components.py      # Composants d'interface utilisateur
│   └── helpers.py            # Fonctions utilitaires diverses
│
└── modes/                    # Différents modes de l'application
    ├── __init__.py
    ├── ikea_mode.py          # Mode avec sélection de meubles
    └── simple_mode.py        # Mode inpainting direct
## Modes d'utilisation
![image](https://github.com/user-attachments/assets/06a4b3b3-6dd3-44b6-9a28-ef36dd47f52e)

### Mode IKEA
1. Téléchargez une image de votre pièce
2. Sélectionnez des meubles du catalogue IKEA
3. Positionnez-les dans votre pièce
4. Générez le design final avec l'IA

### Mode Simple
1. Téléchargez une image de votre pièce vide
2. Décrivez les meubles que vous souhaitez
3. Générez le résultat en un clic

## Détails techniques

L'application repose sur une architecture modulaire et utilise des technologies avancées pour créer des designs d'intérieur réalistes:

- **Interface**: Développée avec Streamlit pour une expérience utilisateur interactive et réactive
- **Modèles d'IA**: Utilisation de Stable Diffusion XL avec ControlNet pour un contrôle précis de la génération d'images
- **Techniques de vision par ordinateur**:
  - Cartes de profondeur pour comprendre la structure 3D de la pièce
  - Masques d'inpainting intelligents pour préserver les meubles sélectionnés
  - Détection des éléments structurels (murs, sol) pour un rendu cohérent
- **Traitement d'images**:
  - Suppression automatique des fonds des meubles avec rembg
  - Compositing multi-couches pour la prévisualisation des meubles
  - Algorithmes de suggestion de placement basés sur le type de meuble et la pièce
- **Architecture du projet**:
  - Organisation modulaire (modèles, utils, modes) pour faciliter la maintenance
  - Séparation des responsabilités (interface, traitement, IA)
  - Gestion des états avec Streamlit pour conserver le contexte utilisateur
- **Catalogue de meubles**:
  - Chargement dynamique du catalogue IKEA depuis un dépôt GitHub
  - Système de filtrage et recherche par catégorie et caractéristiques
  - Support pour l'upload de meubles personnalisés

## Pipeline technique

Le processus complet de génération d'un design d'intérieur se déroule en plusieurs étapes clés :

### 1. Préparation des données d'entrée
- **Mode IKEA** : L'utilisateur télécharge une image de pièce et sélectionne des meubles qui sont ensuite composités sur l'image
- **Mode Simple** : L'utilisateur télécharge une image et fournit une description textuelle des meubles souhaités

### 2. Génération du masque intelligent
- Analyse de l'image pour détecter les différences entre l'image originale et l'image avec meubles
- Détection des éléments structurels (murs, sols, coins) à préserver
- Combinaison de ces informations pour créer un masque d'inpainting avancé qui protège les meubles et structure

### 3. Extraction de la carte de profondeur
- Utilisation du modèle DPT (Dense Prediction Transformer) de Intel/Midas
- Conversion de l'image 2D en information de profondeur pour guider le modèle ControlNet
- Normalisation et redimensionnement pour correspondre à l'entrée du modèle

### 4. Pipeline d'IA et inpainting
- Chargement du modèle Stable Diffusion XL et du ControlNet pour la profondeur
- Génération d'un prompt contextuel basé sur le type de pièce, style et meubles sélectionnés
- Exécution du processus d'inpainting avec les paramètres optimisés :
  ```
  - image : Image composée avec meubles
  - mask_image : Masque intelligent généré
  - control_image : Carte de profondeur
  - prompt : Description contextuelle du style d'intérieur
  - negative_prompt : Éléments à éviter dans la génération
  - num_inference_steps : 40 (équilibre qualité/vitesse)
  - guidance_scale : 7.5 (contrôle de l'adhérence au prompt)
  ```

### 5. Post-traitement et présentation
- Libération de la mémoire GPU après génération
- Création d'une visualisation comparative avant/après avec slider interactif
- Préparation de l'image finale en haute résolution pour téléchargement

## Architecture de l'interface

L'interface utilisateur est conçue pour être intuitive et guider l'utilisateur à travers un processus étape par étape :

### Structure principale
- **Barre latérale** : Contient les paramètres et options (type de pièce, style, paramètres avancés)
- **Corps principal** : Interface à étapes progressives avec navigation intuitive
- **Gestion d'état** : Utilisation du système de session Streamlit pour conserver les données entre interactions

### Composants personnalisés
- **Zone d'upload stylisée** : Interface de glisser-déposer améliorée avec icônes et retour visuel
- **Système de notification** : Toasts temporaires pour informer l'utilisateur des actions et résultats
- **Indicateur de progression** : Visualisation des étapes accomplies et restantes
- **Catalogue de meubles** : Interface de navigation avec filtres, recherche et prévisualisations
- **Canvas interactif** : Système de positionnement des meubles avec contrôles directionnels et grille de positions prédéfinies
- **Comparateur avant/après** : Visualisation avec slider pour comparer les résultats

### Flux de données
1. Les images et sélections utilisateur sont stockées dans `st.session_state`
2. Les transformations intermédiaires (masques, cartes de profondeur) sont calculées à la volée
3. Le pipeline IA reçoit toutes les entrées nécessaires pour la génération finale
4. Les résultats sont affichés dans l'interface et rendus disponibles pour téléchargement

Cette architecture permet une expérience fluide où l'utilisateur peut:
- Naviguer librement entre les étapes
- Voir l'impact des changements en temps réel
- Ajuster précisément le positionnement des meubles
- Générer un design d'intérieur personnalisé en quelques clics

## Équipe

Projet développé par:
- Fatma Hafsa
- Marwa Rizi

## Prérequis techniques

- Python 3.8 ou supérieur
- GPU recommandé pour des performances optimales
- Connexion internet pour télécharger les modèles IA et le catalogue IKEA

##  Remerciements
Merci à Ivona Tau pour le dataset IKEA utilisé dans le projet.

import streamlit as st
import json
import requests
from datetime import datetime

###################################### CSS ######################################

# Charger le CSS
css_file_path = 'css/style.css'
with open(css_file_path, "r", encoding="utf-8") as f:
    css = f.read()

# Injecter le CSS dans l'application
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

##################################################################################

################################# BASE DE DONNÉES #################################

# Charger les données JSON
with open('data/data_final_light.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Configuration de l'API
API_KEY = 'dcc19539bb2aad10e600613bd95f3cd5'  # Remplacez par votre clé API
API_BASE_URL = 'https://api.themoviedb.org/3/movie'

##################################################################################

# Fonction pour récupérer les informations d'un film via l'API
def fetch_movie_info(movie_id):
    try:
        url = f"{API_BASE_URL}/{movie_id}"
        params = {"api_key": API_KEY, "language": "fr-FR"}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur lors de la récupération des données pour l'ID {movie_id}")
            return None
    except Exception as e:
        st.error(f"Une erreur s'est produite : {e}")
        return None

# Fonction pour récupérer les acteurs et les réalisateurs (directors)
def get_movie_details(movie_id):
    # URL de base pour les détails du film
    credits_url = f"{API_BASE_URL}/{movie_id}/credits"
    # Paramètres de la requête
    params = {"api_key": API_KEY, "language": "fr-FR"}  # Use api_key parameter
    # Récupération des détails du film
    credits_response = requests.get(credits_url, params=params)
    if credits_response.status_code == 200:
        credits_data = credits_response.json()
        # Extraction des informations demandées
        movie_details = {
            "directors": [
                crew_member["name"]
                for crew_member in credits_data.get("crew", [])
                if crew_member.get("job") == "Director"
            ],
            "actors": [
                actor["name"] for actor in credits_data.get("cast", [])[:10]
            ],  # Top 10 acteurs
        }
        return movie_details
    else:
        raise Exception(f"Erreur lors de la requête à l'API TMDB: {credits_response.status_code}")

# Fonction pour obtenir les titres des films recherchés
def get_search_titles():
    return [item[0]["title_fr"] for item in data]

# Fonction pour obtenir les informations d'un film recherché et de ses recommandations
def get_movie_and_recommandations(search_title):
    for item in data:
        searched_movie = item[0]
        recommandations = item[1]
        if searched_movie["title_fr"].lower() == search_title.lower():
            # Récupérer les infos du film recherché
            movie_info = fetch_movie_info(searched_movie["id_recherche"]) # Tous les éléments sauf acteurs et réalisateurs
            movie_details = get_movie_details(searched_movie['id_recherche']) # Acteurs et réalisateurs
            # Récupérer les infos des films recommandés
            recommandations_info = [
                {
                    "info": fetch_movie_info(rec["id_reco"]),
                    "details": get_movie_details(rec["id_reco"]),
                }
                for rec in recommandations
            ]
            return movie_info, movie_details, recommandations_info
    return None, None, None

from datetime import datetime

# Fonction pour transformer les dates au format date entière en français (2 avril 2024)
def format_date(date_string):
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")  # Convertir la chaîne en objet datetime
        return date_obj.strftime("%d/%m/%Y")  # Retourner la date formatée en JJ/MM/AAAA
    except (ValueError, TypeError):
        return "Date invalide"

##################################################################################
###################################### SITE ######################################
##################################################################################

# Interface utilisateur avec Streamlit
st.title("Qu'est-ce qu'on regarde ce soir ?")
st.write("✨ Cherchez un film **que vous avez aimé**, on se charge de vous trouver quelques recommandations pour ce soir ✨")

# Barre de recherche avec suggestions
movie_titles = get_search_titles()
search_title = st.selectbox(
    "",
    options=["🔍 Quel film avez-vous aimé ?"] + sorted(movie_titles),  # Une option vide par défaut
    format_func=lambda x: '' if x == "" else x
)

# Si un titre est sélectionné
st.info("ℹ️ La recherche se base sur le titre du film uniquement")
if search_title:
    # Recherche du film et de ses recommandations
    if search_title and search_title != "🔍 Quel film avez-vous aimé ?":
        movie_info, movie_details, recommandations_info = get_movie_and_recommandations(search_title)

        # Initialiser l'état dans st.session_state
        if "show_details" not in st.session_state:
            st.session_state.show_details = False  # Les détails sont masqués par défaut

        # Affichage du film recherché
        if movie_info:
            st.subheader('💖 Vous avez aimé')
            full_backdrop_url = f"https://image.tmdb.org/t/p/w1280{movie_info.get('backdrop_path', '')}"
            # Vérification de l'image de fond (backdrop)
            if full_backdrop_url:
                # Ajouter le backdrop en utilisant le CSS depuis le fichier
                st.markdown(
                    f"""
                    <div class="film-background">
                        <div class="background-opacity" style="background-image: url({full_backdrop_url});"></div>
                        <div class="film-title">{movie_info.get('title', 'Titre inconnu')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"## {movie_info.get['title', 'Titre']}")

            # Créer une seule colonne pour centrer le bouton
            col = st.columns(1)[0]
            with col:
                st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                if st.button("Voir les détails du film"):
                    st.session_state.show_details = not st.session_state.show_details
                st.markdown("</div>", unsafe_allow_html=True)

            # Afficher ou masquer les colonnes en fonction de l'état
            if st.session_state.show_details:
                # Afficher les détails du film
                col1, col2 = st.columns([1, 2])  # Deux colonnes pour les détails

                # Affiche du film (à gauche)
                poster_url = movie_info.get('poster_path', '')
                if poster_url:
                    full_poster_url = f"https://image.tmdb.org/t/p/w500{movie_info.get('poster_path', '')}"
                    with col1:
                        # Affiche l'image et ajoute un effet de zoom au clic
                        st.markdown(
                            f'<div style="text-align:center;">'
                            f'<a href="{full_poster_url}" target="_blank">'
                            f'<img src="{full_poster_url}" alt="{search_title}" class="movie-poster" style="width:100%; cursor:pointer;"/>'
                            f'</a>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                # Informations du film (à droite)
                with col2:
                # Affichage des informations du film recherché
                    if movie_info:
                        st.write(f"**🕔 Durée :** {movie_info.get('runtime', 'Inconnue')} minutes")
                        st.write(f"**⭐ Note :** {movie_info.get('vote_average', 'Non notée')}")
                        genre_names = [genre['name'] for genre in movie_info.get('genres', [])]
                        st.write(f"**🎭 Genre·s :** {', '.join(genre_names)}")
                        formatted_date = format_date(movie_info.get('release_date'))
                        st.write(f"**📅 Date de sortie :** {formatted_date}")                        
                        st.write(f"**🎬 Réalisateur·rice·s :** {', '.join(movie_details.get('directors', []))}")
                        st.write(f"**🧑‍🎤 Acteur·rice·s principal·e·s :** {', '.join(movie_details.get('actors', []))}")                     
                        st.write(f"**📖 Résumé :** {movie_info.get('overview', 'Pas de résumé disponible')}")
                    else:
                        st.warning("Aucune information trouvée pour ce film.")

        # Affichage des films recommandés    
        if recommandations_info:
            st.subheader("✨ Nos recommandations")

            cols = st.columns(5)  # Afficher jusqu'à 5 colonnes
            for i, reco in enumerate(recommandations_info):
                reco_info = reco["info"]
                reco_details = reco["details"]
                movie_title = reco_info.get("title", "Titre inconnu")
                poster_url = reco_info.get("poster_path", "")

                with cols[i % 5]:
                    if poster_url:
                        img_html = f"""
                        <div style="text-align:center;">
                            <a href="https://image.tmdb.org/t/p/w500{poster_url}" target="_blank">
                                <img src="https://image.tmdb.org/t/p/w200{poster_url}" class="movie-poster" style="width:100%; cursor:pointer;"/>
                            </a>
                        </div>
                        """
                        # Afficher l'image avec l'effet hover
                        st.markdown(img_html, unsafe_allow_html=True)

                        # Ajouter un peu d'espace avant le bouton (par exemple 10px)
                        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                    else:
                        st.write("Aucune affiche disponible")

                    # Affichage du bouton pour voir les détails
                    if st.button(f"Voir les détails", key=f"btn_{i}"):
                        # Sauvegarder les informations du film sélectionné dans `st.session_state`
                        st.session_state.selected_movie = reco
                        st.session_state.selected_movie_index = i
                        st.rerun()  # Rafraîchir pour afficher les détails

            # Affichage des détails du film sélectionné
            if 'selected_movie' in st.session_state:
                selected_movie = st.session_state.selected_movie
                movie_info = selected_movie["info"]
                movie_details = selected_movie["details"]

                st.subheader(movie_info.get('title', 'Titre inconnu'))

                # Afficher les détails du film sélectionné
                col1, col2 = st.columns([1, 2])  # Crée 2 colonnes pour l'affiche et les détails
                with col1:
                    poster_url = movie_info.get("poster_path", "")
                    if poster_url:
                        full_poster_url = f"https://image.tmdb.org/t/p/w500{poster_url}"
                        img_html = f"""
                        <div style="text-align:center;">
                            <a href="{full_poster_url}" target="_blank">
                                <img src="https://image.tmdb.org/t/p/w200{poster_url}" alt="{movie_info.get('title', 'Affiche du film')}" class="movie-poster" style="width:100%; cursor:pointer;"/>
                            </a>
                        </div>
                        """
                        # Afficher l'image avec le lien
                        st.markdown(img_html, unsafe_allow_html=True)
                    else:
                        st.write("Aucune affiche disponible.")

                with col2:
                    st.write(f"**🕔 Durée :** {movie_info.get('runtime', 'Inconnue')} minutes")
                    st.write(f"**⭐ Note :** {movie_info.get('vote_average', 'Non noté')}")
                    genre_names = [genre['name'] for genre in movie_info.get('genres', [])]
                    st.write(f"**🎭 Genre·s :** {', '.join(genre_names)}")
                    formatted_date = format_date(movie_info.get('release_date'))
                    st.write(f"**📅 Date de sortie :** {formatted_date}")
                    st.write(f"**🎬 Réalisateur·rice·s :** {', '.join(movie_details.get('directors', []))}")
                    st.write(f"**🧑‍🎤 Acteur·rice·s principal·e·s :** {', '.join(movie_details.get('actors', []))}")
                    st.write(f"**📖 Résumé :** {movie_info.get('overview', 'Pas de résumé disponible')}")

                # Bouton pour revenir à la liste des films recommandés
                if st.button("Réduire 🔼"):
                    del st.session_state.selected_movie  # Supprimer l'état du film sélectionné
                    del st.session_state.selected_movie_index
                    st.rerun()  # Rafraîchir la page pour revenir à l'affichage initial
        else:
            st.warning("Aucune recommandation trouvée.")

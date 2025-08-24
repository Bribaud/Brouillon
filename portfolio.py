import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import base64
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, date
import hashlib
import time
import os
from dotenv import load_dotenv

# Configuration de la page
st.set_page_config(
    page_title="Portfolio - Data Scientist",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Charger les variables du fichier .env
load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

# Fichiers et dossiers
CONFIG_FILE = "portfolio_config.json"
ANALYTICS_FILE = "portfolio_analytics.json"
UPLOAD_FOLDER = "uploads"
IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, "images")
VIDEOS_FOLDER = os.path.join(UPLOAD_FOLDER, "videos")

# Créer les dossiers s'ils n'existent pas
for folder in [UPLOAD_FOLDER, IMAGES_FOLDER, VIDEOS_FOLDER]:
    os.makedirs(folder, exist_ok=True)


def get_visitor_id():
    """Générer un ID unique pour chaque visiteur basé sur la session"""
    if 'visitor_id' not in st.session_state:
        # Créer un ID unique basé sur l'heure et un hash
        timestamp = str(datetime.now().timestamp())
        st.session_state.visitor_id = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return st.session_state.visitor_id


def get_current_timestamp():
    """Retourner le timestamp actuel avec date et heure exacte"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate_time_spent(start_time_str, end_time_str):
    """Calculer le temps passé entre deux timestamps"""
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        time_diff = end_time - start_time

        total_seconds = int(time_diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except:
        return "N/A"


def load_analytics():
    """Charger les données d'analytics"""
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "total_visits": 0,
                "unique_visitors": 0,
                "daily_visits": {},
                "page_views": {
                    "portfolio": 0,
                    "project_details": 0
                },
                "project_views": {},
                "visitors": {},
                "sessions": {}  # Nouvelle section pour les sessions détaillées
            }
    return {
        "total_visits": 0,
        "unique_visitors": 0,
        "daily_visits": {},
        "page_views": {
            "portfolio": 0,
            "project_details": 0
        },
        "project_views": {},
        "visitors": {},
        "sessions": {}
    }


def save_analytics(analytics):
    """Sauvegarder les données d'analytics"""
    try:
        with open(ANALYTICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(analytics, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def start_session():
    """Démarrer une nouvelle session pour un visiteur"""
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = get_current_timestamp()
        st.session_state.session_page_views = []
        st.session_state.last_activity = get_current_timestamp()


def update_session_activity(page="portfolio", project_key=None):
    """Mettre à jour l'activité de la session actuelle"""
    current_time = get_current_timestamp()
    st.session_state.last_activity = current_time

    # Ajouter la page visitée avec timestamp
    page_visit = {
        "page": page,
        "timestamp": current_time,
        "project_key": project_key
    }

    if 'session_page_views' not in st.session_state:
        st.session_state.session_page_views = []

    st.session_state.session_page_views.append(page_visit)


def end_session():
    """Terminer la session actuelle et sauvegarder les données"""
    if 'session_start_time' in st.session_state:
        analytics = load_analytics()
        visitor_id = get_visitor_id()
        session_end_time = get_current_timestamp()

        # Calculer la durée de la session
        session_duration = calculate_time_spent(
            st.session_state.session_start_time,
            session_end_time
        )

        # Créer l'ID de session unique
        session_id = f"{visitor_id}_{st.session_state.session_start_time}"

        # Sauvegarder les détails de la session
        analytics["sessions"][session_id] = {
            "visitor_id": visitor_id,
            "start_time": st.session_state.session_start_time,
            "end_time": session_end_time,
            "duration": session_duration,
            "page_views": st.session_state.session_page_views,
            "total_page_views": len(st.session_state.session_page_views)
        }

        save_analytics(analytics)


def track_visit(page="portfolio", project_key=None):
    """Tracker une visite avec timestamps détaillés"""
    analytics = load_analytics()
    visitor_id = get_visitor_id()
    current_timestamp = get_current_timestamp()
    today = str(date.today())

    # Démarrer la session si ce n'est pas fait
    start_session()

    # Mettre à jour l'activité de la session
    update_session_activity(page, project_key)

    # Nouveau visiteur ?
    is_new_visitor = visitor_id not in analytics["visitors"]

    if is_new_visitor:
        analytics["unique_visitors"] += 1
        analytics["visitors"][visitor_id] = {
            "first_visit": current_timestamp,  # Timestamp complet au lieu de juste la date
            "total_visits": 0,
            "pages_visited": [],
            "total_time_spent": "0s",
            "sessions": []
        }

    # Incrémenter les compteurs
    analytics["total_visits"] += 1
    analytics["visitors"][visitor_id]["total_visits"] += 1
    analytics["visitors"][visitor_id]["last_visit"] = current_timestamp  # Timestamp complet

    # Visits quotidiennes
    if today not in analytics["daily_visits"]:
        analytics["daily_visits"][today] = 0
    analytics["daily_visits"][today] += 1

    # Pages vues
    analytics["page_views"][page] = analytics["page_views"].get(page, 0) + 1

    # Projets vus
    if project_key:
        analytics["project_views"][project_key] = analytics["project_views"].get(project_key, 0) + 1

    # Ajouter la page aux pages visitées
    if page not in analytics["visitors"][visitor_id]["pages_visited"]:
        analytics["visitors"][visitor_id]["pages_visited"].append(page)

    save_analytics(analytics)
    return analytics


def calculate_total_time_for_visitor(visitor_id):
    """Calculer le temps total passé par un visiteur sur toutes ses sessions"""
    analytics = load_analytics()
    total_seconds = 0

    for session_id, session_data in analytics.get("sessions", {}).items():
        if session_data.get("visitor_id") == visitor_id:
            duration_str = session_data.get("duration", "0s")
            # Convertir la durée en secondes
            try:
                if "h" in duration_str:
                    parts = duration_str.replace("h", "").replace("m", "").replace("s", "").split()
                    if len(parts) >= 3:
                        total_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif "m" in duration_str:
                    parts = duration_str.replace("m", "").replace("s", "").split()
                    if len(parts) >= 2:
                        total_seconds += int(parts[0]) * 60 + int(parts[1])
                elif "s" in duration_str:
                    seconds = int(duration_str.replace("s", ""))
                    total_seconds += seconds
            except:
                continue

    # Convertir en format lisible
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def save_uploaded_file(uploaded_file, folder):
    """Sauvegarder un fichier uploadé et retourner le chemin"""
    if uploaded_file is not None:
        file_path = os.path.join(folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        # Retourner le chemin relatif pour l'accès web
        return file_path.replace("\\", "/")
    return None


def image_to_base64(image_path):
    """Convertir une image en base64"""
    try:
        with open(image_path, "rb") as img_file:
            return f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode()}"
    except:
        return None


def file_to_base64(file_path):
    """Convertir un fichier en base64 (pour CV PDF)"""
    try:
        with open(file_path, "rb") as f:
            return f"data:application/pdf;base64,{base64.b64encode(f.read()).decode()}"
    except:
        return None


# Configuration par défaut
DEFAULT_CONFIG = {
    "profile": {
        "id_number": "",
        "greeting": "Hello, I am",
        "name": "Naveen",
        "title": "Data Scientist",
        "profile_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
        "resume_link": "#",
        "linkedin_url": "#",
        "github_url": "#"
    },
    "about": {
        "description": "Hello! I'm Naveen, a Data Scientist skilled in Machine Learning, Python, and SQL. I love turning complex data into clear insights that help solve real-world problems.",
        "tools": [
            "🔹 I use Python to handle data and create models that learn from it.",
            "🔹 I'm good with SQL for organizing and retrieving data.",
            "🔹 I also work with tools like Jupyter Notebooks, Pandas, and Matplotlib to analyze and show data clearly."
        ],
        "expertise": [
            "🔹 Building models that predict future trends and improve business decisions.",
            "🔹 Making data tasks faster and more accurate with automation.",
            "🔹 Designing easy-to-understand data visualizations for better decision-making."
        ],
        "conclusion": "I believe in the power of learning from data and constantly improving. I enjoy sharing what I learn and connecting with others interested about how we can use data to make a difference!"
    },
    "skills": ["MACHINE LEARNING", "PYTHON", "SQL", "NUMPY", "PANDAS"],
    "stats": [
        {"number": "1", "label": "Python<br>Project", "icon": "🐍", "background": "#3776ab"},
        {"number": "2", "label": "Machine Learning<br>Projects", "icon": "🤖", "background": "#ff6b6b"},
        {"number": "1", "label": "SQL<br>Project", "icon": "🗃️", "background": "#336791"}
    ],
    "projects": {
        "hotel_analysis": {
            "title": "AtliQ Hotels Data Analysis Project",
            "domain": "Hospitality",
            "badge": "Python Project",
            "description": "AtliQ Grands faced declining market share due to a lack of data analytics capabilities. Tasked with analyzing historical data, I used Pandas in Jupyter Notebook for exploratory analysis, identifying crucial inefficiencies. The insights gained led to a 10% rise in occupancy rates and a 15% increase in satisfaction scores on key platforms, ultimately enhancing AtliQ Grands' competitive standing.",
            "situation": "AtliQ Grands faced declining market share and revenue in a competitive sector without internal data analytics capabilities.",
            "task": "I was tasked to analyze historical data and derive insights to improve market position and revenue.",
            "action": "Using Pandas in Jupyter Notebook, I conducted exploratory data analysis to identify key performance trends and inefficiencies.",
            "result": "The insights led to a 10% increase in occupancy rates and a 15% improvement in satisfaction scores on major booking platforms, effectively enhancing AtliQ Grands' competitive standing.",
            "youtube_id": "xkx7hbKh6Ec",
            "presentation_images": [
                "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=300&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=300&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=400&h=300&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1543286386-713bdd548da4?w=400&h=300&fit=crop&crop=center"
            ],
            "card_gradient": "linear-gradient(45deg, #FFD700, #FFA500)",
            "card_label": "HOTEL BOOKINGS"
        },
        "price_prediction": {
            "title": "Price Range Prediction",
            "domain": "Food & Beverages",
            "badge": "ML Project",
            "description": "Develop a predictive model that will assist in finding a price range that avoids the risks of overpricing or underpricing the product based on various features.",
            "situation": "Need to develop an accurate pricing strategy for food & beverage products.",
            "task": "Create a machine learning model to predict optimal price ranges.",
            "action": "Implemented various ML algorithms and performed feature engineering.",
            "result": "Achieved high accuracy in price prediction, helping optimize pricing strategies.",
            "youtube_id": "dQw4w9WgXcQ",
            "presentation_images": [
                "https://images.unsplash.com/photo-1518186285589-2f7649de83e0?w=400&h=300&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=300&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1590736969955-71cc94901144?w=400&h=300&fit=crop&crop=center"
            ],
            "card_gradient": "linear-gradient(45deg, #4169E1, #1E90FF)",
            "card_label": "Price Range Prediction"
        },
        "healthcare_prediction": {
            "title": "Healthcare Premium Prediction - Regression",
            "domain": "Healthcare",
            "badge": "ML Project",
            "description": "Developed a high accuracy predictive model to estimate healthcare insurance premiums based on factors such as age, smoking habits, BMI, and other relevant variables.",
            "situation": "Healthcare insurance companies need accurate premium estimation.",
            "task": "Build a regression model to predict insurance premiums.",
            "action": "Used advanced regression techniques and feature selection.",
            "result": "Created a highly accurate model for premium prediction.",
            "youtube_id": "dQw4w9WgXcQ",
            "presentation_images": [
                "https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=400&h=300&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&h=300&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=400&h=300&fit=crop&crop=center"
            ],
            "card_gradient": "linear-gradient(45deg, #87CEEB, #4682B4)",
            "card_label": "Healthcare Insurance Premium Prediction - Regression"
        }
    }
}


def load_config():
    """Charger la configuration depuis le fichier"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG


def save_config(config):
    """Sauvegarder la configuration dans le fichier"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        margin: -1rem -1rem 2rem -1rem;
        color: white;
    }

    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 3rem 2rem;
        max-width: 1200px;
        margin: 0 auto;
        min-height: 400px;
    }

    .intro-text {
        flex: 1;
        max-width: 500px;
    }

    .intro-text .id-number {
        color: #999;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .intro-text .greeting {
        color: #666;
        font-size: 1.2rem;
        font-style: italic;
        margin-bottom: 0.5rem;
    }

    .intro-text h1 {
        font-size: 3.5rem;
        margin: 0;
        color: #333;
        font-weight: bold;
        line-height: 1.2;
    }

    .intro-text h2 {
        font-size: 1.5rem;
        color: #667eea;
        margin: 0.5rem 0 1.5rem 0;
        font-weight: normal;
    }

    .resume-button {
        background: white;
        border: 2px solid #667eea;
        color: #667eea;
        padding: 0.7rem 1.5rem;
        border-radius: 5px;
        cursor: pointer;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
        display: inline-block;
        text-decoration: none;
    }

    .resume-button:hover {
        background: #667eea;
        color: white;
    }

    .profile-image-container {
        flex-shrink: 0;
        margin-left: 2rem;
    }

    .profile-image {
        width: 350px;
        height: 350px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #667eea;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .stats-bar {
        background: white;
        padding: 2rem 0;
        margin: 3rem 0;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .stats-bar:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }

    .stats-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 4rem;
        max-width: 800px;
        margin: 0 auto;
        padding: 0 2rem;
    }

    .stat-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        color: #333;
    }

    .stat-icon {
        width: 45px;
        height: 45px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
    }

    .stat-content {
        display: flex;
        flex-direction: column;
    }

    .stat-number {
        font-size: 1.6rem;
        font-weight: bold;
        color: #333;
        line-height: 1;
    }

    .stat-label {
        font-size: 0.85rem;
        color: #666;
        line-height: 1.2;
    }

    .about-section {
        background: #f8f9fa;
        padding: 3rem 2rem;
        margin: 3rem 0;
        border-radius: 15px;
    }

    .skills-container {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0;
        flex-wrap: wrap;
    }

    .skill-badge {
        background: #667eea;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.9rem;
    }

    .project-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
        transition: transform 0.3s ease;
    }

    .project-card:hover {
        transform: translateY(-5px);
    }

    .project-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 0.5rem;
    }

    .project-domain {
        color: #667eea;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }

    .social-icons {
        display: flex;
        gap: 0.8rem;
        margin-top: 1rem;
    }

    .social-icon {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        text-decoration: none;
        font-size: 1.1rem;
    }

    .linkedin {
        background: #0077b5;
    }

    .github {
        background: #333;
    }

    .admin-section {
        background: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def admin_login():
    """Page de connexion admin"""
    st.title("🔐 Espace Administration")
    st.markdown("---")

    with st.form("login_form"):
        password = st.text_input("Mot de passe administrateur", type="password")
        submitted = st.form_submit_button("Se connecter")

        if submitted:
            if password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("✅ Connexion réussie !")
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")


def admin_panel():
    """Panel d'administration avec analytics détaillés"""
    config = load_config()

    st.title("⚙️ Administration du Portfolio")

    # Boutons de navigation
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("👤 Voir le Portfolio"):
            st.session_state.current_page = "main"
            st.rerun()
    with col2:
        if st.button("🚪 Déconnexion"):
            st.session_state.admin_logged_in = False
            st.rerun()

    st.markdown("---")

    # Onglets d'administration avec Analytics améliorés
    tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["📊 Analytics", "⏱️ Sessions Détaillées", "👤 Profil", "📊 Statistiques", "📝 À propos", "🛠️ Compétences",
         "📁 Projets"])

    with tab0:
        st.markdown("### 📈 Tableau de bord Analytics")

        analytics = load_analytics()

        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="🌍 Visites totales",
                value=analytics["total_visits"],
                delta=f"+{analytics['daily_visits'].get(str(date.today()), 0)} aujourd'hui"
            )

        with col2:
            st.metric(
                label="👥 Visiteurs uniques",
                value=analytics["unique_visitors"]
            )

        with col3:
            portfolio_views = analytics["page_views"].get("portfolio", 0)
            st.metric(
                label="🏠 Vues Portfolio",
                value=portfolio_views
            )

        with col4:
            project_views = analytics["page_views"].get("project_details", 0)
            st.metric(
                label="📁 Vues Projets",
                value=project_views
            )

        st.markdown("---")

        # Graphiques
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("**📅 Visites par jour (7 derniers jours)**")
            if analytics["daily_visits"]:
                # Prendre les 7 derniers jours
                recent_days = list(analytics["daily_visits"].items())[-7:]
                if recent_days:
                    days = [day for day, _ in recent_days]
                    visits = [visits for _, visits in recent_days]

                    # Créer un graphique simple
                    chart_data = {"Date": days, "Visites": visits}
                    st.bar_chart(chart_data, x="Date", y="Visites")
                else:
                    st.info("Pas encore de données")
            else:
                st.info("Aucune visite enregistrée")

        with col_chart2:
            st.markdown("**📊 Projets les plus vus**")
            if analytics["project_views"]:
                project_stats = []
                config_projects = config.get("projects", {})

                for project_key, views in analytics["project_views"].items():
                    project_title = config_projects.get(project_key, {}).get("title", project_key)
                    project_stats.append({
                        "Projet": project_title[:20] + "..." if len(project_title) > 20 else project_title,
                        "Vues": views
                    })

                # Trier par nombre de vues
                project_stats.sort(key=lambda x: x["Vues"], reverse=True)

                if project_stats:
                    st.bar_chart(project_stats, x="Projet", y="Vues")
                else:
                    st.info("Aucune vue de projet")
            else:
                st.info("Aucun projet consulté")

        st.markdown("---")

        # Détails des visiteurs avec timestamps exacts
        st.markdown("**👥 Détails des visiteurs (avec temps exact)**")
        if analytics["visitors"]:
            visitor_data = []
            for visitor_id, data in list(analytics["visitors"].items())[-15:]:  # 15 derniers
                # Calculer le temps total passé
                total_time = calculate_total_time_for_visitor(visitor_id)

                visitor_data.append({
                    "ID Visiteur": visitor_id,
                    "Première visite": data["first_visit"],  # Maintenant avec heure exacte
                    "Dernière visite": data.get("last_visit", data["first_visit"]),  # Avec heure exacte
                    "Nb visites": data["total_visits"],
                    "Pages vues": len(data.get("pages_visited", [])),
                    "Temps total": total_time
                })

            if visitor_data:
                st.dataframe(visitor_data, use_container_width=True)
            else:
                st.info("Aucun visiteur")
        else:
            st.info("Aucune donnée de visiteur")

        # Bouton de réinitialisation CORRIGÉ
        st.markdown("---")

        # Utiliser un état pour gérer la confirmation
        if "confirm_reset_analytics" not in st.session_state:
            st.session_state.confirm_reset_analytics = False

        # Premier bouton : demander la confirmation
        if not st.session_state.confirm_reset_analytics:
            if st.button("🗑️ Réinitialiser les analytics", type="secondary"):
                st.session_state.confirm_reset_analytics = True
                st.rerun()
        else:
            # Afficher les boutons de confirmation
            st.warning(
                "⚠️ Êtes-vous sûr de vouloir réinitialiser toutes les données d'analytics ? Cette action est irréversible.")

            col_confirm, col_cancel = st.columns(2)

            with col_confirm:
                if st.button("✅ Oui, réinitialiser", type="primary"):
                    empty_analytics = {
                        "total_visits": 0,
                        "unique_visitors": 0,
                        "daily_visits": {},
                        "page_views": {"portfolio": 0, "project_details": 0},
                        "project_views": {},
                        "visitors": {},
                        "sessions": {}
                    }
                    if save_analytics(empty_analytics):
                        st.success("✅ Analytics réinitialisées avec succès !")
                        st.session_state.confirm_reset_analytics = False
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la réinitialisation")
                        st.session_state.confirm_reset_analytics = False

            with col_cancel:
                if st.button("❌ Annuler", type="secondary"):
                    st.session_state.confirm_reset_analytics = False
                    st.rerun()

    with tab1:
        st.markdown("### ⏱️ Sessions Détaillées")

        analytics = load_analytics()
        sessions = analytics.get("sessions", {})

        if sessions:
            st.markdown(f"**📊 Total des sessions : {len(sessions)}**")

            # Tableau détaillé des sessions
            session_data = []
            for session_id, session_info in list(sessions.items())[-20:]:  # 20 dernières sessions
                session_data.append({
                    "Session ID": session_id[-16:],  # Derniers 16 caractères
                    "Visiteur": session_info["visitor_id"],
                    "Début": session_info["start_time"],
                    "Fin": session_info["end_time"],
                    "Durée": session_info["duration"],
                    "Pages vues": session_info["total_page_views"]
                })

            if session_data:
                st.dataframe(session_data, use_container_width=True)

                # Sélecteur pour voir les détails d'une session
                st.markdown("---")
                st.markdown("**🔍 Détails d'une session**")

                session_ids = [s["Session ID"] for s in session_data]
                selected_session = st.selectbox("Sélectionner une session", session_ids)

                if selected_session:
                    # Trouver la session complète
                    full_session_id = None
                    for sid in sessions.keys():
                        if sid.endswith(selected_session):
                            full_session_id = sid
                            break

                    if full_session_id:
                        session_details = sessions[full_session_id]

                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**📋 Informations de session**")
                            st.write(f"**Visiteur :** {session_details['visitor_id']}")
                            st.write(f"**Début :** {session_details['start_time']}")
                            st.write(f"**Fin :** {session_details['end_time']}")
                            st.write(f"**Durée totale :** {session_details['duration']}")
                            st.write(f"**Pages visitées :** {session_details['total_page_views']}")

                        with col2:
                            st.markdown("**🗺️ Parcours détaillé**")
                            if session_details.get("page_views"):
                                for i, page_view in enumerate(session_details["page_views"], 1):
                                    page_name = page_view["page"]
                                    timestamp = page_view["timestamp"]
                                    project = page_view.get("project_key", "")

                                    if project:
                                        st.write(f"**{i}.** {page_name} ({project}) - {timestamp}")
                                    else:
                                        st.write(f"**{i}.** {page_name} - {timestamp}")
            else:
                st.info("Aucune session enregistrée")

            # Statistiques des sessions
            st.markdown("---")
            st.markdown("**📈 Statistiques des sessions**")

            if sessions:
                total_sessions = len(sessions)

                # Calculer durée moyenne
                total_seconds = 0
                valid_sessions = 0

                for session_info in sessions.values():
                    duration_str = session_info.get("duration", "0s")
                    try:
                        if "h" in duration_str:
                            parts = duration_str.replace("h", "").replace("m", "").replace("s", "").split()
                            if len(parts) >= 3:
                                total_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                valid_sessions += 1
                        elif "m" in duration_str:
                            parts = duration_str.replace("m", "").replace("s", "").split()
                            if len(parts) >= 2:
                                total_seconds += int(parts[0]) * 60 + int(parts[1])
                                valid_sessions += 1
                        elif "s" in duration_str:
                            seconds = int(duration_str.replace("s", ""))
                            total_seconds += seconds
                            valid_sessions += 1
                    except:
                        continue

                if valid_sessions > 0:
                    avg_seconds = total_seconds // valid_sessions
                    avg_minutes = avg_seconds // 60
                    avg_seconds_remainder = avg_seconds % 60

                    col_stat1, col_stat2, col_stat3 = st.columns(3)

                    with col_stat1:
                        st.metric("🕐 Durée moyenne", f"{avg_minutes}m {avg_seconds_remainder}s")

                    with col_stat2:
                        avg_pages = sum(s.get("total_page_views", 0) for s in sessions.values()) / len(sessions)
                        st.metric("📄 Pages/session", f"{avg_pages:.1f}")

                    with col_stat3:
                        st.metric("📊 Sessions totales", total_sessions)
        else:
            st.info("Aucune session enregistrée pour le moment")

    with tab2:
        st.markdown("### Configuration du Profil")

        col1, col2 = st.columns(2)
        with col1:
            config["profile"]["id_number"] = st.text_input("Numéro ID", value=config["profile"]["id_number"])
            config["profile"]["greeting"] = st.text_input("Message d'accueil", value=config["profile"]["greeting"])
            config["profile"]["name"] = st.text_input("Nom", value=config["profile"]["name"])
            config["profile"]["title"] = st.text_input("Titre", value=config["profile"]["title"])

        with col2:
            # Upload d'image de profil
            st.markdown("**Image de profil**")
            profile_upload = st.file_uploader(
                "📁 Glissez votre photo de profil ici",
                type=['png', 'jpg', 'jpeg'],
                key="profile_image_upload"
            )

            if profile_upload:
                # Sauvegarder l'image
                saved_path = save_uploaded_file(profile_upload, IMAGES_FOLDER)
                if saved_path:
                    base64_image = image_to_base64(saved_path)
                    if base64_image:
                        config["profile"]["profile_image"] = base64_image
                        st.success("✅ Image sauvegardée !")

            # Option URL alternative
            config["profile"]["profile_image"] = st.text_input(
                "Ou URL de l'image",
                value=config["profile"]["profile_image"],
                help="Laissez vide si vous avez uploadé une image"
            )

        # Section CV
        st.markdown("### Configuration du CV")
        col_cv1, col_cv2 = st.columns(2)

        with col_cv1:
            # Upload de CV
            cv_upload = st.file_uploader(
                "📁 Glissez votre CV ici (PDF)",
                type=['pdf'],
                key="cv_upload"
            )

            if cv_upload:
                saved_cv_path = save_uploaded_file(cv_upload, UPLOAD_FOLDER)
                if saved_cv_path:
                    # Créer un lien vers le fichier local
                    config["profile"]["resume_link"] = saved_cv_path
                    st.success("✅ CV sauvegardé !")

                    # Aperçu du CV
                    with open(saved_cv_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                        st.download_button(
                            label="📄 Télécharger le CV uploadé",
                            data=pdf_bytes,
                            file_name=cv_upload.name,
                            mime="application/pdf"
                        )

        with col_cv2:
            # Option lien alternatif
            config["profile"]["resume_link"] = st.text_input(
                "Ou lien vers le CV",
                value=config["profile"]["resume_link"],
                help="URL externe ou laissez vide si CV uploadé"
            )

        # Section liens sociaux
        st.markdown("### Liens sociaux")
        col_social1, col_social2 = st.columns(2)

        with col_social1:
            st.markdown("**LinkedIn**")
            # Upload d'icône LinkedIn
            linkedin_icon_upload = st.file_uploader(
                "📁 Icône LinkedIn",
                type=['png', 'jpg', 'jpeg', 'svg'],
                key="linkedin_icon_upload"
            )

            if linkedin_icon_upload:
                saved_path = save_uploaded_file(linkedin_icon_upload, IMAGES_FOLDER)
                if saved_path:
                    base64_icon = image_to_base64(saved_path)
                    if base64_icon:
                        config["profile"]["linkedin_icon"] = base64_icon
                        st.success("✅ Icône LinkedIn sauvegardée !")

            # Option URL/émoji alternatif
            config["profile"]["linkedin_icon"] = st.text_input(
                "Ou émoji/URL LinkedIn",
                value=config["profile"].get("linkedin_icon", "💼"),
                help="Émoji (💼) ou URL d'image"
            )

            config["profile"]["linkedin_url"] = st.text_input("URL LinkedIn", value=config["profile"]["linkedin_url"])

            # Aperçu de l'icône LinkedIn
            if config["profile"].get("linkedin_icon"):
                if config["profile"]["linkedin_icon"].startswith("http") or config["profile"][
                    "linkedin_icon"].startswith("data:"):
                    try:
                        st.image(config["profile"]["linkedin_icon"], caption="Aperçu LinkedIn", width=40)
                    except:
                        st.write(f"Icône LinkedIn: {config['profile']['linkedin_icon']}")
                else:
                    st.write(f"Icône LinkedIn: {config['profile']['linkedin_icon']}")

        with col_social2:
            st.markdown("**GitHub**")
            # Upload d'icône GitHub
            github_icon_upload = st.file_uploader(
                "📁 Icône GitHub",
                type=['png', 'jpg', 'jpeg', 'svg'],
                key="github_icon_upload"
            )

            if github_icon_upload:
                saved_path = save_uploaded_file(github_icon_upload, IMAGES_FOLDER)
                if saved_path:
                    base64_icon = image_to_base64(saved_path)
                    if base64_icon:
                        config["profile"]["github_icon"] = base64_icon
                        st.success("✅ Icône GitHub sauvegardée !")

            # Option URL/émoji alternatif
            config["profile"]["github_icon"] = st.text_input(
                "Ou émoji/URL GitHub",
                value=config["profile"].get("github_icon", "🔗"),
                help="Émoji (🔗) ou URL d'image"
            )

            config["profile"]["github_url"] = st.text_input("URL GitHub", value=config["profile"]["github_url"])

            # Aperçu de l'icône GitHub
            if config["profile"].get("github_icon"):
                if config["profile"]["github_icon"].startswith("http") or config["profile"]["github_icon"].startswith(
                        "data:"):
                    try:
                        st.image(config["profile"]["github_icon"], caption="Aperçu GitHub", width=40)
                    except:
                        st.write(f"Icône GitHub: {config['profile']['github_icon']}")
                else:
                    st.write(f"Icône GitHub: {config['profile']['github_icon']}")

        # Aperçu de l'image de profil
        if config["profile"]["profile_image"] and config["profile"][
            "profile_image"] != "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==":
            try:
                st.image(config["profile"]["profile_image"], caption="Aperçu de l'image de profil", width=150)
            except:
                st.warning("⚠️ Image invalide")

    with tab3:
        st.markdown("### Configuration des Statistiques")

        for i, stat in enumerate(config["stats"]):
            st.markdown(f"**Statistique {i + 1}**")
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                config["stats"][i]["number"] = st.text_input(f"Nombre", value=stat["number"], key=f"stat_num_{i}")

            with col2:
                config["stats"][i]["label"] = st.text_input(f"Label", value=stat["label"], key=f"stat_label_{i}")

            with col3:
                # Upload d'icône
                icon_upload = st.file_uploader(
                    f"📁 Icône {i + 1}",
                    type=['png', 'jpg', 'jpeg', 'svg'],
                    key=f"icon_upload_{i}"
                )

                if icon_upload:
                    saved_path = save_uploaded_file(icon_upload, IMAGES_FOLDER)
                    if saved_path:
                        base64_icon = image_to_base64(saved_path)
                        if base64_icon:
                            config["stats"][i]["icon"] = base64_icon
                            st.success("✅ Icône sauvegardée !")

            with col4:
                # Option émoji/URL alternative
                config["stats"][i]["icon"] = st.text_input(
                    f"Ou émoji/URL",
                    value=stat["icon"],
                    key=f"stat_icon_{i}",
                    help="Émoji (🐍) ou URL d'image"
                )

            with col5:
                config["stats"][i]["background"] = st.color_picker(f"Couleur", value=stat["background"],
                                                                   key=f"stat_bg_{i}")

            # Aperçu de l'icône
            if stat["icon"]:
                if stat["icon"].startswith("http") or stat["icon"].startswith("data:"):
                    try:
                        st.image(stat["icon"], caption=f"Aperçu icône {i + 1}", width=50)
                    except:
                        st.write(f"Icône: {stat['icon']}")
                else:
                    st.write(f"Icône: {stat['icon']}")

            st.markdown("---")

        # Ajouter nouvelle statistique
        col_add, col_del = st.columns(2)
        with col_add:
            if st.button("➕ Ajouter une statistique", key="add_stat_btn"):
                config["stats"].append({
                    "number": "0",
                    "label": "Nouveau<br>Projet",
                    "icon": "⭐",
                    "background": "#667eea"
                })
                if save_config(config):
                    st.success("✅ Statistique ajoutée !")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la sauvegarde")

        # Supprimer statistique
        with col_del:
            if len(config["stats"]) > 1:
                if st.button("➖ Supprimer la dernière statistique", key="del_stat_btn"):
                    config["stats"].pop()
                    if save_config(config):
                        st.success("✅ Statistique supprimée !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")

    with tab4:
        st.markdown("### Configuration À propos")

        config["about"]["description"] = st.text_area("Description principale", value=config["about"]["description"],
                                                      height=100)

        st.markdown("**Outils et Technologies**")
        for i, tool in enumerate(config["about"]["tools"]):
            col_tool, col_del = st.columns([4, 1])
            with col_tool:
                config["about"]["tools"][i] = st.text_input(f"Outil {i + 1}", value=tool, key=f"tool_{i}")
            with col_del:
                if st.button("🗑️", key=f"del_tool_{i}"):
                    config["about"]["tools"].pop(i)
                    if save_config(config):
                        st.success("✅ Outil supprimé !")
                        st.rerun()

        if st.button("➕ Ajouter un outil", key="add_tool_btn"):
            config["about"]["tools"].append("🔹 Nouvel outil")
            if save_config(config):
                st.success("✅ Outil ajouté !")
                st.rerun()

        st.markdown("**Domaines d'expertise**")
        for i, exp in enumerate(config["about"]["expertise"]):
            col_exp, col_del = st.columns([4, 1])
            with col_exp:
                config["about"]["expertise"][i] = st.text_input(f"Expertise {i + 1}", value=exp, key=f"exp_{i}")
            with col_del:
                if st.button("🗑️", key=f"del_exp_{i}"):
                    config["about"]["expertise"].pop(i)
                    if save_config(config):
                        st.success("✅ Expertise supprimée !")
                        st.rerun()

        if st.button("➕ Ajouter une expertise", key="add_exp_btn"):
            config["about"]["expertise"].append("🔹 Nouvelle expertise")
            if save_config(config):
                st.success("✅ Expertise ajoutée !")
                st.rerun()

        config["about"]["conclusion"] = st.text_area("Conclusion", value=config["about"]["conclusion"], height=100)

    with tab5:
        st.markdown("### Configuration des Compétences")

        for i, skill in enumerate(config["skills"]):
            col_skill, col_del = st.columns([4, 1])
            with col_skill:
                config["skills"][i] = st.text_input(f"Compétence {i + 1}", value=skill, key=f"skill_{i}")
            with col_del:
                if len(config["skills"]) > 1:  # Garder au moins une compétence
                    if st.button("🗑️", key=f"del_skill_{i}", help="Supprimer cette compétence"):
                        config["skills"].pop(i)
                        if save_config(config):
                            st.success("✅ Compétence supprimée !")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la sauvegarde")

        if st.button("➕ Ajouter une compétence", key="add_skill_btn"):
            config["skills"].append("NOUVELLE COMPETENCE")
            if save_config(config):
                st.success("✅ Compétence ajoutée !")
                st.rerun()
            else:
                st.error("❌ Erreur lors de la sauvegarde")

    with tab6:
        st.markdown("### Gestion des Projets")

        # Liste des projets
        project_names = list(config["projects"].keys())

        if project_names:
            selected_project = st.selectbox("Sélectionner un projet à modifier", project_names)

            if selected_project:
                project = config["projects"][selected_project]

                st.markdown(f"#### Modification: {project['title']}")

                col1, col2 = st.columns(2)
                with col1:
                    project["title"] = st.text_input("Titre du projet", value=project["title"])
                    project["domain"] = st.text_input("Domaine", value=project["domain"])
                    project["badge"] = st.text_input("Badge", value=project["badge"])
                    project["card_gradient"] = st.text_input("Gradient de la carte", value=project["card_gradient"])
                    project["card_label"] = st.text_input("Label de la carte", value=project["card_label"])

                with col2:
                    project["description"] = st.text_area("Description", value=project["description"], height=150)
                    project["youtube_id"] = st.text_input("ID Vidéo YouTube", value=project["youtube_id"])

                st.markdown("**Liens du projet**")
                col_link1, col_link2 = st.columns(2)

                with col_link1:
                    project["github_url"] = st.text_input(
                        "URL GitHub du projet",
                        value=project.get("github_url", ""),
                        help="Lien vers le repository GitHub"
                    )

                with col_link2:
                    project["engagement_url"] = st.text_input(
                        "URL Project Engagement",
                        value=project.get("engagement_url", ""),
                        help="Lien vers la démonstration ou présentation du projet"
                    )

                st.markdown("**Détails du projet**")
                project["project_details"] = st.text_area(
                    "Détails complets du projet",
                    value=project.get("project_details",
                                      f"Situation: {project.get('situation', '')}\n\nTask: {project.get('task', '')}\n\nAction: {project.get('action', '')}\n\nResult: {project.get('result', '')}"),
                    height=300,
                    help="Écrivez librement tous les détails de votre projet. Vous pouvez utiliser la méthode STAR ou votre propre structure."
                )

                st.markdown("**Images de présentation**")

                # Upload multiple d'images
                uploaded_images = st.file_uploader(
                    "📁 Glissez vos images de projet ici",
                    type=['png', 'jpg', 'jpeg'],
                    accept_multiple_files=True,
                    key=f"images_{selected_project}"
                )

                if uploaded_images:
                    for uploaded_img in uploaded_images:
                        saved_path = save_uploaded_file(uploaded_img, IMAGES_FOLDER)
                        if saved_path:
                            base64_img = image_to_base64(saved_path)
                            if base64_img and base64_img not in project["presentation_images"]:
                                project["presentation_images"].append(base64_img)
                    st.success(f"✅ {len(uploaded_images)} image(s) ajoutée(s) !")

                # Gestion des images existantes
                for i, img_url in enumerate(project["presentation_images"]):
                    col_img, col_btn = st.columns([4, 1])
                    with col_img:
                        st.image(img_url, caption=f"Image {i + 1}", width=100)
                    with col_btn:
                        if st.button("🗑️", key=f"del_img_{selected_project}_{i}"):
                            project["presentation_images"].pop(i)
                            save_config(config)
                            st.rerun()

                # Upload de vidéo
                st.markdown("**Vidéo du projet**")

                col_vid1, col_vid2 = st.columns(2)

                with col_vid1:
                    # Option 1: Upload fichier vidéo
                    video_upload = st.file_uploader(
                        "📁 Glissez votre vidéo ici",
                        type=['mp4', 'avi', 'mov', 'wmv'],
                        key=f"video_upload_{selected_project}"
                    )

                    if video_upload:
                        saved_video_path = save_uploaded_file(video_upload, VIDEOS_FOLDER)
                        if saved_video_path:
                            project["local_video"] = saved_video_path
                            st.success("✅ Vidéo sauvegardée !")

                            # Aperçu vidéo locale
                            with open(saved_video_path, "rb") as video_file:
                                video_bytes = video_file.read()
                                st.video(video_bytes)

                with col_vid2:
                    # Option 2: ID YouTube
                    st.markdown("**Ou ID YouTube**")
                    project["youtube_id"] = st.text_input(
                        "ID YouTube (ex: dQw4w9WgXcQ)",
                        value=project["youtube_id"],
                        help="L'ID se trouve dans l'URL après 'watch?v='"
                    )

                    # Aperçu vidéo YouTube si ID fourni
                    if project["youtube_id"]:
                        try:
                            st.video(f"https://www.youtube.com/watch?v={project['youtube_id']}")
                        except:
                            st.warning("⚠️ ID YouTube invalide")

        st.markdown("---")
        col_add_proj, col_del_proj = st.columns(2)
        with col_add_proj:
            if st.button("➕ Ajouter un nouveau projet", key="add_project_btn"):
                new_project_key = f"projet_{len(config['projects']) + 1}"
                config["projects"][new_project_key] = {
                    "title": "Nouveau Projet",
                    "domain": "Domaine",
                    "badge": "Badge Projet",
                    "description": "Description du nouveau projet",
                    "project_details": "Situation: Décrivez le contexte du projet.\n\nTask: Quelle était votre tâche assignée?\n\nAction: Quelles actions avez-vous entreprises?\n\nResult: Quels résultats avez-vous obtenus?",
                    "youtube_id": "",
                    "local_video": "",
                    "presentation_images": ["https://via.placeholder.com/400x300"],
                    "card_gradient": "linear-gradient(45deg, #667eea, #764ba2)",
                    "card_label": "NOUVEAU PROJET"
                }
                if save_config(config):
                    st.success("✅ Projet ajouté !")
                    st.rerun()

        with col_del_proj:
            if len(config["projects"]) > 1 and project_names:
                project_to_delete = st.selectbox(
                    "Projet à supprimer",
                    project_names,
                    key="delete_project_select"
                )
                if st.button("🗑️ Supprimer le projet", key="del_project_btn"):
                    del config["projects"][project_to_delete]
                    if save_config(config):
                        st.success("✅ Projet supprimé !")
                        st.rerun()

    # Bouton de sauvegarde
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💾 Sauvegarder les modifications", type="primary"):
            if save_config(config):
                st.success("✅ Configuration sauvegardée avec succès !")
            else:
                st.error("❌ Erreur lors de la sauvegarde")


def main_page():
    """Page principale du portfolio"""
    config = load_config()
    profile = config["profile"]

    # En-tête principal avec layout exact comme l'image
    linkedin_icon = profile.get("linkedin_icon", "💼")
    github_icon = profile.get("github_icon", "🔗")

    # Gestion des icônes sociales
    if linkedin_icon.startswith("http") or linkedin_icon.startswith("data:"):
        linkedin_display = f'<img src="{linkedin_icon}" style="width: 20px; height: 20px;">'
    else:
        linkedin_display = linkedin_icon

    if github_icon.startswith("http") or github_icon.startswith("data:"):
        github_display = f'<img src="{github_icon}" style="width: 20px; height: 20px;">'
    else:
        github_display = github_icon

    st.markdown(f"""
    <div class="header-container">
        <div class="intro-text">
            <div class="id-number">{profile['id_number']}</div>
            <div class="greeting">{profile['greeting']}</div>
            <h1>{profile['name']}</h1>
            <h2>{profile['title']}</h2>
            <a href="{profile['resume_link']}" class="resume-button"> CV ↓</a>
            <div class="social-icons">
                <a href="{profile['linkedin_url']}" class="social-icon linkedin" title="LinkedIn">{linkedin_display}</a>
                <a href="{profile['github_url']}" class="social-icon github" title="GitHub">{github_display}</a>
            </div>
        </div>
        <div class="profile-image-container">
            <img src="{profile['profile_image']}" class="profile-image" alt="Profile">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Barre de statistiques avec components.html pour garantir le rendu
    stats_items = ""
    for stat in config["stats"]:
        # Gestion des icônes (émoji ou image uploadée)
        if stat["icon"].startswith("http") or stat["icon"].startswith("data:"):
            icon_display = f'<img src="{stat["icon"]}" style="width: 20px; height: 20px;">'
        else:
            icon_display = stat["icon"]

        stats_items += f"""
            <div class="stat-item">
                <div class="stat-icon" style="background: {stat['background']};">
                    {icon_display}
                </div>
                <div class="stat-content">
                    <div class="stat-number">{stat['number']}</div>
                    <div class="stat-label">{stat['label']}</div>
                </div>
            </div>
        """

    # HTML complet avec CSS intégré pour garantir le rendu
    stats_html = f"""
    <style>
        .stats-bar {{
            background: white;
            padding: 2rem 0;
            margin: 3rem 0;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .stats-bar:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}

        .stats-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 4rem;
            max-width: 800px;
            margin: 0 auto;
            padding: 0 2rem;
        }}

        .stat-item {{
            display: flex;
            align-items: center;
            gap: 1rem;
            color: #333;
        }}

        .stat-icon {{
            width: 45px;
            height: 45px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
        }}

        .stat-content {{
            display: flex;
            flex-direction: column;
        }}

        .stat-number {{
            font-size: 1.6rem;
            font-weight: bold;
            color: #333;
            line-height: 1;
        }}

        .stat-label {{
            font-size: 0.85rem;
            color: #666;
            line-height: 1.2;
        }}
    </style>

    <div class="stats-bar">
        <div class="stats-container">
            {stats_items}
        </div>
    </div>
    """

    # Utiliser components.html pour garantir le rendu HTML
    components.html(stats_html, height=200)


def about_section():
    """Section À propos"""
    config = load_config()
    about = config["about"]

    st.markdown('<div class="about-section">', unsafe_allow_html=True)
    st.markdown(
        '<h2 style="text-align: center; color: #333; margin-bottom: 2rem;">À propos <span style="color: #667eea;">De moi</span></h2>',
        unsafe_allow_html=True)
    st.markdown('<div style="max-width: 800px; margin: 0 auto;">', unsafe_allow_html=True)

    st.markdown(f"""
    <p style="text-align: center; color: #666; line-height: 1.6; margin-bottom: 2rem;">
        {about['description']}
    </p>
    """, unsafe_allow_html=True)

    st.markdown('<h3 style="color: #333; margin-bottom: 1rem;">Outils et technologies:</h3>', unsafe_allow_html=True)
    tools_html = '<ul style="color: #666; line-height: 1.8;">'
    for tool in about['tools']:
        tools_html += f'<li>{tool}</li>'
    tools_html += '</ul>'
    st.markdown(tools_html, unsafe_allow_html=True)

    st.markdown('<h3 style="color: #333; margin: 2rem 0 1rem 0;">Domaines d\'expertise:</h3>', unsafe_allow_html=True)
    expertise_html = '<ul style="color: #666; line-height: 1.8;">'
    for exp in about['expertise']:
        expertise_html += f'<li>{exp}</li>'
    expertise_html += '</ul>'
    st.markdown(expertise_html, unsafe_allow_html=True)

    st.markdown(f"""
    <p style="text-align: center; color: #666; line-height: 1.6; margin-top: 2rem; font-style: italic;">
        {about['conclusion']}
    </p>
    """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)


def skills_section():
    """Section compétences"""
    config = load_config()
    skills = config["skills"]

    skills_html = '''
    <h2 style="text-align: center; color: #333; margin: 3rem 0 2rem 0;">Compétences <span style="color: #667eea;">Clés</span> 🎯</h2>
    <div class="skills-container">
    '''
    for skill in skills:
        skills_html += f'<div class="skill-badge">{skill}</div>'
    skills_html += '</div>'

    st.markdown(skills_html, unsafe_allow_html=True)


def projects_section():
    """Section projets"""
    config = load_config()
    projects = config["projects"]

    st.markdown("""
    <h2 style="text-align: center; color: #333; margin: 3rem 0 2rem 0;">Mes <span style="color: #667eea;">Projets</span></h2>
    """, unsafe_allow_html=True)

    # Affichage des projets (3 par ligne)
    project_items = list(projects.items())
    cols = st.columns(3)

    for i, (project_key, project) in enumerate(project_items):
        col_idx = i % 3
        with cols[col_idx]:
            st.markdown(f"""
            <div class="project-card">
                <div style="background: {project['card_gradient']}; height: 150px; border-radius: 10px; margin-bottom: 1rem; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.2rem;">
                    {project['card_label']}
                </div>
                <div class="project-title">{project['title']}</div>
                <div class="project-domain">Domaine/Fonction: {project['domain']}</div>
                <p style="color: #666; font-size: 0.9rem;">
                    {project['description'][:150]}...
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Bouton corrigé avec clé unique et gestion directe
            button_key = f"see_work_{project_key}_{i}"
            if st.button("Voir Mon Travail", key=button_key):
                # Forcer la mise à jour immédiate des états
                st.session_state.current_page = "project_detail"
                st.session_state.selected_project = project_key
                # Forcer le rechargement immédiat
                st.rerun()


def project_detail_page():
    """Page de détail d'un projet"""
    config = load_config()
    projects = config["projects"]

    project_key = st.session_state.get("selected_project", list(projects.keys())[0])
    project = projects[project_key]

    # Initialiser l'index de l'image si ce n'est pas fait
    if f"image_index_{project_key}" not in st.session_state:
        st.session_state[f"image_index_{project_key}"] = 0

    # Bouton retour
    if st.button("← Retour au portfolio"):
        st.session_state.current_page = "main"
        st.rerun()

    # Titre principal
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #333; margin: 0; font-size: 2rem;">{project['title']}</h1>
    </div>
    """, unsafe_allow_html=True)

    # PREMIÈRE LIGNE - Résumé + Images
    col1, col2 = st.columns(2)

    # ZONE HAUT GAUCHE - Résumé du projet
    with col1:
        st.markdown("### Résumé du Projet")

        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <div style="background: #667eea; color: white; padding: 0.5rem 1rem; border-radius: 5px; font-size: 0.8rem;">
                {project['badge']}
            </div>
            <div style="color: #ffb300; font-size: 1.2rem;"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**Domaine/Fonction:** {project['domain']}")
        st.write(project['description'])

        # Afficher seulement le bouton GitHub s'il y a une URL
        github_url = project.get("github_url", "")

        if github_url:
            st.markdown(f"**🔗 Lien du projet :**")
            st.markdown(f"📂 [Voir le Project sur GitHub]({github_url})")
        else:
            # Pas de bouton si pas d'URL GitHub configurée
            st.info("🔗 Configurez l'URL GitHub dans l'admin pour afficher le lien")

    # ZONE HAUT DROITE - Images du projet
    with col2:
        st.markdown("### Version Finale du Projet")
        st.markdown(
            '<div style="text-align: center; color: #999; margin-bottom: 1rem;"><p style="font-size: 0.9rem;"></p></div>',
            unsafe_allow_html=True)

        # Gestion du carrousel
        if project.get("presentation_images"):
            current_index = st.session_state[f"image_index_{project_key}"]
            total_images = len(project["presentation_images"])

            # Image actuelle
            st.image(
                project['presentation_images'][current_index],
                use_container_width=True,
                caption=f"Image {current_index + 1} sur {total_images}"
            )

            # Boutons de navigation
            col_prev, col_info, col_next = st.columns([1, 2, 1])
            with col_prev:
                if st.button("◀ Précédent", key=f"prev_{project_key}"):
                    st.session_state[f"image_index_{project_key}"] = (current_index - 1) % total_images
                    st.rerun()

            with col_info:
                st.markdown(
                    '<div style="text-align: center; color: #999; font-size: 0.8rem; padding-top: 0.5rem;">Interface</div>',
                    unsafe_allow_html=True)

            with col_next:
                if st.button("Suivant ▶", key=f"next_{project_key}"):
                    st.session_state[f"image_index_{project_key}"] = (current_index + 1) % total_images
                    st.rerun()
        else:
            st.info("📊 Ajoutez vos captures d'écran de projet ici")
            st.markdown('<div style="text-align: center; color: #999; font-size: 0.8rem;">Notebook</div>',
                        unsafe_allow_html=True)

    st.markdown("---")  # Séparateur

    # DEUXIÈME LIGNE - Project Details + Vidéo
    col3, col4 = st.columns(2)

    # ZONE BAS GAUCHE - Project Details
    with col3:
        st.markdown("### Details du Projet")

        # Affichage libre des détails du projet
        project_details = project.get("project_details", "")
        if not project_details:
            # Migration depuis l'ancien format STAR si nécessaire
            project_details = f"Situation: {project.get('situation', '')}\n\nTask: {project.get('task', '')}\n\nAction: {project.get('action', '')}\n\nResult: {project.get('result', '')}"

        # Diviser en paragraphes et afficher
        paragraphs = project_details.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                st.write(paragraph.strip())

    # ZONE BAS DROITE - Vidéo
    with col4:
        st.markdown("### Video du Projet")

        # Priorité à la vidéo locale si elle existe
        if project.get("local_video") and os.path.exists(project["local_video"]):
            try:
                with open(project["local_video"], "rb") as video_file:
                    video_bytes = video_file.read()
                    st.video(video_bytes)
            except:
                st.error("⚠️ Erreur lors du chargement de la vidéo locale")
        # Sinon afficher YouTube si disponible
        elif project.get("youtube_id") and project["youtube_id"].strip():
            youtube_url = f"https://www.youtube.com/embed/{project['youtube_id']}"
            st.markdown(f"""
            <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 10px;">
                <iframe src="{youtube_url}" 
                        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; border-radius: 10px;"
                        allowfullscreen>
                </iframe>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("🎥 Uploadez une vidéo ou ajoutez un ID YouTube dans l'admin")


# Initialisation de la session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "main"

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# Navigation principale
if st.session_state.current_page == "main":
    # Bouton d'accès admin (discret)
    if st.sidebar.button("🔐 Admin"):
        st.session_state.current_page = "admin"
        st.rerun()

    # Tracker la visite de la page principale
    track_visit("portfolio")

    main_page()
    about_section()
    skills_section()
    projects_section()

elif st.session_state.current_page == "project_detail":
    # Bouton d'accès admin (discret)
    if st.sidebar.button("🔐 Admin"):
        st.session_state.current_page = "admin"
        st.rerun()

    # Tracker la visite de la page projet
    selected_project = st.session_state.get("selected_project")
    track_visit("project_details", selected_project)

    project_detail_page()

elif st.session_state.current_page == "admin":
    if not st.session_state.admin_logged_in:
        admin_login()
    else:
        admin_panel()

# Hook pour terminer la session quand l'utilisateur quitte (optionnel)
# Note: Ce code s'exécute à chaque interaction, mais la session se termine naturellement
# quand l'utilisateur ferme l'onglet ou navigue ailleurs
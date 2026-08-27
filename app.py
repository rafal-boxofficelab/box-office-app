import streamlit as st
import requests
from supabase import create_client

# --- 1. KONFIGURACJA STRONY & STYLE CINEMAGHOST MAGENTA ---
st.set_page_config(page_title="Liga Box Office", page_icon="🎬", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
TMDB_KEY = st.secrets.get("TMDB_API_KEY", "")

supabase = create_client(URL, KEY)

# Pełny CSS: kinowe tło magenty/burgundu, stylizowane karty, inputy i przyciski
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Główne tło aplikacji - kinowa magenta z winietą */
    .stApp {
        background: radial-gradient(circle at center, #240a17 0%, #12030b 60%, #080105 100%) !important;
        color: #FFFFFF !important;
    }

    /* Sidebar - spójny ciemnomagentowy odcień */
    section[data-testid="stSidebar"] {
        background-color: #15050f !important;
        border-right: 1px solid #3d0d24 !important;
    }

    /* Nagłówki */
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }

    /* Karty kontenerów (st.container border=True) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(180deg, rgba(38, 12, 26, 0.75) 0%, rgba(20, 5, 13, 0.9) 100%) !important;
        border: 1px solid #4a122e !important;
        border-radius: 12px !important;
        padding: 16px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #B81D4C !important;
        box-shadow: 0 0 20px rgba(184, 29, 76, 0.35);
    }

    /* Przyciski CinemaGhost (gradient malinowa magenta) */
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 700;
        font-size: 14px;
        letter-spacing: 0.3px;
        background: linear-gradient(135deg, #C2185B 0%, #9C1540 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #D81B60 !important;
        padding: 0.6rem 1rem;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #E22D68 0%, #B81D4C 100%) !important;
        box-shadow: 0 0 16px rgba(226, 45, 104, 0.6) !important;
        transform: translateY(-1px);
    }

    /* Wartości i etykiety metryk */
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #E22D68 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #D1A3B8 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Rozwijane dropdowny (st.expander) w tabeli */
    div[data-testid="stExpander"] {
        background-color: rgba(26, 7, 18, 0.8) !important;
        border: 1px solid #4a122e !important;
        border-radius: 8px !important;
        margin-bottom: 8px;
    }
    div[data-testid="stExpander"]:hover {
        border-color: #B81D4C !important;
    }

    /* Inputy formularzy */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: #12030b !important;
        color: #FFFFFF !important;
        border: 1px solid #4a122e !important;
        border-radius: 6px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #E22D68 !important;
        box-shadow: 0 0 10px rgba(226, 45, 104, 0.4) !important;
    }
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

# --- FUNKCJE POMOCNICZE TMDB ---
def search_tmdb_movie(title_query):
    if not TMDB_KEY:
        return None
    
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={title_query}&language=pl-PL"
    res = requests.get(search_url).json()
    
    results = res.get("results", [])
    if not results:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={title_query}&language=en-US"
        res = requests.get(search_url).json()
        results = res.get("results", [])
        if not results:
            return None
            
    movie = results[0]
    movie_id = movie["id"]
    
    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&append_to_response=credits&language=pl-PL"
    details = requests.get(details_url).json()
    
    poster_path = details.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
    
    genres = ", ".join([g["name"] for g in details.get("genres", [])])
    
    crew = details.get("credits", {}).get("crew", [])
    directors = [c["name"] for c in crew if c.get("job") == "Director"]
    director_str = ", ".join(directors) if directors else "Brak danych"
    
    cast = details.get("credits", {}).get("cast", [])
    top_cast = ", ".join([a["name"] for a in cast[:4]]) if cast else "Brak danych"
    
    return {
        "title": details.get("title") or movie.get("title"),
        "original_title": details.get("original_title", ""),
        "poster_url": poster_url,
        "director": director_str,
        "cast_members": top_cast,
        "genres": genres
    }

# --- 2. EKRAN LOGOWANIA / REJESTRACJI ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("<div style='text-align: center; margin-bottom: 24px;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='color: #E22D68 !important; margin-bottom: 4px;'>🎬 LIGA BOX OFFICE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #D1A3B8; font-size: 15px;'>Ekspercki Portal Typowania Widzów w Kinach</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            tab1, tab2 = st.tabs(["🔒 Logowanie Eksperta", "📝 Dołącz do Ligi"])
            
            with tab1:
                email = st.text_input("Adres Email", placeholder="ekspert@kino.pl")
                password = st.text_input("Hasło", type="password")
                if st.button("Zaloguj się do panelu", type="primary"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.rerun()
                    except Exception:
                        st.error("Błędny email lub hasło.")
                        
            with tab2:
                name = st.text_input("Imię i Nazwisko / Pseudonim")
                reg_email = st.text_input("Adres Email", key="reg_e")
                reg_pass = st.text_input("Hasło (min. 6 znaków)", type="password", key="reg_p")
                if st.button("Zarejestruj konto Eksperta"):
                    try:
                        res = supabase.auth.sign_up({
                            "email": reg_email, 
                            "password": reg_pass,
                            "options": {"data": {"full_name": name}}
                        })
                        st.success("Konto utworzone! Możesz się teraz zalogować.")
                    except Exception as e:
                        st.error(f"Błąd rejestracji: {e}")

# --- 3. PANEL DLA ZALOGOWANEGO UŻYTKOWNIKA ---
else:
    st.sidebar.image("https://img.icons8.com/color/96/clapperboard.png", width=55)
    st.sidebar.markdown("### **Panel Eksperta**")
    st.sidebar.caption(f"Zalogowany: `{st.session_state.user.email}`")
    
    if st.sidebar.button("🚪 Wyloguj"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()
        
    st.sidebar.write("---")
    menu = st.sidebar.radio("Nawigacja", [
        "🎯 Głosowanie Tygodnia", 
        "🏆 Tabela Ligi", 
        "👤 Swój Profil",
        "🛠️ Panel Admina (Filmy i TMDB)"
    ])

    # === ZAKŁADKA 1: GŁOSOWANIE NA WIDZÓW ===
    if menu == "🎯 Głosowanie Tygodnia":
        st.title("🎯 Typowanie Otwarć Kinowych")
        st.caption("Wprowadź szacowaną **liczbę widzów** w weekend premierowy (piątek - niedziela).")
        st.write("---")
        
        movies = supabase.table("movies").select("*").eq("voting_open", True).order("release_date").execute().data
        
        if not movies:
            st.info("🍿 Brak aktywnych filmów do typowania w tym tygodniu.")
        else:
            for m in movies:
                with st.container(border=True):
                    col_img, col_info, col_form = st.columns([1.1, 2.4, 1.8])
                    
                    with col_img:
                        if m.get("poster_url"):
                            st.image(m["poster_url"], use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/300x450?text=Brak+Plakatu", use_container_width=True)
                            
                    with col_info:
                        st.subheader(m["title"])
                        if m.get("original_title") and m["original_title"] != m["title"]:
                            st.caption(f"Tytuł oryginalny: *{m['original_title']}*")
                        
                        st.write(f"📅 **Data premiery:** `{m['release_date']}`")
                        if m.get("genres"):
                            st.write(f"🎭 **Gatunek:** {m['genres']}")
                        if m.get("director"):
                            st.write(f"🎬 **Reżyseria:** {m['director']}")
                        if m.get("cast_members"):
                            st.write(f"👥 **Obsada:** {m['cast_members']}")

                    with col_form:
                        st.markdown("#### **Twój Szacunek**")
                        existing = supabase.table("predictions").select("*")\
                            .eq("user_id", st.session_state.user.id)\
                            .eq("movie_id", m['id']).execute().data
                        
                        current_val = int(existing[0]['estimated_opening']) if existing else 50000
                        
                        with st.form(key=f"form_{m['id']}"):
                            val = st.number_input(
                                "Szacowana liczba widzów:", 
                                min_value=0, 
                                value=current_val, 
                                step=5000,
                                format="%d"
                            )
                            submit = st.form_submit_button("Zapisz typ" if not existing else "Zaktualizuj typ", type="primary")
                            
                            if submit:
                                if existing:
                                    supabase.table("predictions").update({"estimated_opening": val})\
                                        .eq("id", existing[0]['id']).execute()
                                    st.toast("Zaktualizowano Twój typ!", icon="✅")
                                else:
                                    supabase.table("predictions").insert({
                                        "user_id": st.session_state.user.id,
                                        "movie_id": m['id'],
                                        "estimated_opening": val
                                    }).execute()
                                    st.toast("Zapisano Twój typ!", icon="🚀")

    # === ZAKŁADKA 2: TABELA LIGI Z ODZNAKAMI I DROPDOWNAMI ===
    elif menu == "🏆 Tabela Ligi":
        st.title("🏆 Klasyfikacja Ligi Box Office")
        
        data = supabase.table("predictions")\
            .select("user_id, points, error_margin, estimated_opening, movies(id, title, release_date, official_bo_result), profiles(full_name)")\
            .not_.is_("points", "null")\
            .execute().data
        
        if not data:
            st.warning("Tabela jest jeszcze pusta. Poczekaj na podliczenie pierwszych wyników!")
        else:
            all_release_dates = [
                row["movies"]["release_date"] 
                for row in data 
                if row.get("movies") and row["movies"].get("release_date")
            ]
            latest_date = max(all_release_dates) if all_release_dates else None

            view_mode = st.radio(
                "Wybierz widok rankingu:",
                ["🌐 Cały Sezon (Klasyfikacja Generalna)", "🔥 Ostatnia Kolejka (Ostatni Weekend)"],
                horizontal=True
            )
            st.write("---")

            if view_mode == "🔥 Ostatnia Kolejka (Ostatni Weekend)" and latest_date:
                filtered_data = [row for row in data if row.get("movies", {}).get("release_date") == latest_date]
                st.info(f"📅 Wyniki z ostatniego weekendu premierowego: **{latest_date}**")
            else:
                filtered_data = data

            user_totals = {}
            user_payouts = {}
            user_names = {}
            user_badges = {}
            user_details = {}

            for row in filtered_data:
                uid = row["user_id"]
                name = row.get("profiles", {}).get("full_name") if row.get("profiles") else "Ekspert"
                pts = row.get("points") or 0
                err = row.get("error_margin")
                est = row.get("estimated_opening")
                movie = row.get("movies", {})
                movie_title = movie.get("title", "Film") if movie else "Film"
                bo_res = movie.get("official_bo_result") if movie else None
                
                # Reguła Super Strzału (<= 1% = 100 zł bonusu)
                if err is not None and err <= 1.00:
                    cash_for_movie = 100.0
                    is_super_shot = True
                else:
                    cash_for_movie = pts * 0.5
                    is_super_shot = False

                user_names[uid] = name
                user_totals[uid] = user_totals.get(uid, 0) + pts
                user_payouts[uid] = user_payouts.get(uid, 0.0) + cash_for_movie
                
                if is_super_shot:
                    user_badges[uid] = user_badges.get(uid, 0) + 1
                
                if uid not in user_details:
                    user_details[uid] = []
                
                est_formatted = f"{int(est):,} widzów".replace(",", " ") if est is not None else "-"
                bo_formatted = f"{int(bo_res):,} widzów".replace(",", " ") if bo_res is not None else "-"
                
                if is_super_shot:
                    est_display = f"⭐ {est_formatted} (Super Strzał)"
                    pts_display = f"{int(pts)} pkt (💰 100,00 zł)"
                else:
                    est_display = est_formatted
                    pts_display = f"{int(pts)} pkt ({cash_for_movie:.2f} zł)"
                    
                user_details[uid].append({
                    "Film": movie_title,
                    "Typ eksperta": est_display,
                    "Oficjalna widownia": bo_formatted,
                    "Błąd %": f"{err:.1f}%" if err is not None else "-",
                    "Punkty i Nagroda": pts_display
                })

            sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)

            def get_badge_str(user_id):
                count = user_badges.get(user_id, 0)
                if count == 0:
                    return ""
                elif count == 1:
                    return " 🎯"
                else:
                    return f" 🎯x{count}"

            # Podium TOP 3
            c1, c2, c3 = st.columns(3)
            if len(sorted_users) >= 1:
                with c1:
                    with st.container(border=True):
                        st.markdown("### 🥇 1. Miejsce")
                        u1 = sorted_users[0][0]
                        st.write(f"**{user_names[u1]}**{get_badge_str(u1)}")
                        st.metric("Suma", f"{int(sorted_users[0][1])} pkt", f"{user_payouts[u1]:.2f} PLN")
            if len(sorted_users) >= 2:
                with c2:
                    with st.container(border=True):
                        st.markdown("### 🥈 2. Miejsce")
                        u2 = sorted_users[1][0]
                        st.write(f"**{user_names[u2]}**{get_badge_str(u2)}")
                        st.metric("Suma", f"{int(sorted_users[1][1])} pkt", f"{user_payouts[u2]:.2f} PLN")
            if len(sorted_users) >= 3:
                with c3:
                    with st.container(border=True):
                        st.markdown("### 🥉 3. Miejsce")
                        u3 = sorted_users[2][0]
                        st.write(f"**{user_names[u3]}**{get_badge_str(u3)}")
                        st.metric("Suma", f"{int(sorted_users[2][1])} pkt", f"{user_payouts[u3]:.2f} PLN")

            st.write("---")
            st.subheader("📊 Ranking Ekspertów")

            for rank, (uid, total_pts) in enumerate(sorted_users, start=1):
                name = user_names[uid]
                payout = user_payouts[uid]
                badge_str = get_badge_str(uid)
                
                label = f"#{rank} | {name}{badge_str} — 🎯 {int(total_pts)} pkt | 💰 {payout:.2f} PLN"
                
                with st.expander(label):
                    st.write(f"**Szczegóły typów dla:** {name}")
                    if user_badges.get(uid, 0) > 0:
                        st.caption(f"⭐ **Super Strzały ($\le$ 1% / 100 zł):** {user_badges[uid]}")
                    st.dataframe(user_details[uid], use_container_width=True, hide_index=True)
            
            st.write("---")
            with st.expander("ℹ️ Legenda punktacji i nagród"):
                st.markdown("""
                * ⭐ **Super Strzał (Błąd $\le$ 1.0%):** **100 pkt + 100,00 zł nagrody** (oraz odznaka 🎯)
                * **Błąd 1.1% – 5.0%:** 100 pkt *(50,00 zł)*
                * **Błąd 5.1% – 20.0%:** 40 pkt *(20,00 zł)*
                * **Błąd 20.1% – 50.0%:** 10 pkt *(5,00 zł)*
                * **Błąd > 50.0%:** 0 pkt
                """)

    # === ZAKŁADKA 3: PROFIL EKSPERTA ===
    elif menu == "👤 Swój Profil":
        st.title("👤 Profil Eksperta")
        st.write("---")
        
        my_preds = supabase.table("predictions")\
            .select("*, movies(title, official_bo_result)")\
            .eq("user_id", st.session_state.user.id)\
            .execute().data
        
        total_pts = sum([p.get('points') or 0 for p in my_preds])
        total_cash = 0.0
        for p in my_preds:
            err = p.get('error_margin')
            pts = p.get('points') or 0
            if err is not None and err <= 1.00:
                total_cash += 100.0
            else:
                total_cash += pts * 0.5
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Wszystkie Oddane Typy", len(my_preds))
        m2.metric("Suma Punktów", f"{int(total_pts)} pkt")
        m3.metric("Wygrana Łącznie", f"{total_cash:.2f} PLN")
        
        st.write("### 📜 Historia Twoich Typów")
        if my_preds:
            history = []
            for p in my_preds:
                movie_title = p.get('movies', {}).get('title', 'Film') if p.get('movies') else 'Film'
                err = p.get('error_margin')
                pts = p.get('points')
                est = p.get('estimated_opening')
                
                if err is not None and err <= 1.00:
                    pts_str = f"⭐ {int(pts)} pkt (100,00 zł)"
                elif pts is not None:
                    pts_str = f"{int(pts)} pkt ({pts * 0.5:.2f} zł)"
                else:
                    pts_str = "Oczekuje na BO"
                
                history.append({
                    "Film": movie_title,
                    "Twój Typ": f"{int(est):,} widzów".replace(",", " ") if est is not None else "-",
                    "Błąd %": f"{err:.1f}%" if err is not None else "W trakcie",
                    "Status / Punkty": pts_str
                })
            st.dataframe(history, use_container_width=True, hide_index=True)
        else:
            st.info("Nie oddałeś jeszcze żadnych typów.")

    # === ZAKŁADKA 4: PANEL ADMINA (ZARZĄDZANIE FILMY & TMDB) ===
    elif menu == "🛠️ Panel Admina (Filmy i TMDB)":
        st.title("🛠️ Panel Zarządzania Filmami")
        st.write("---")
        
        tab_add, tab_sync = st.tabs(["➕ Dodaj Nowy Film z TMDB", "🔄 Uzupełnij Brakujące Dane (Stare Filmy)"])
        
        with tab_add:
            st.subheader("Wyszukaj i dodaj premierę")
            col_search, col_preview = st.columns([1, 1.2])
            
            with col_search:
                movie_search = st.text_input("Wpisz tytuł filmu do wyszukania w TMDB:", placeholder="np. Diuna 2, Joker 2")
                search_btn = st.button("🔍 Pobierz dane z TMDB")
                
                if "tmdb_data" not in st.session_state:
                    st.session_state.tmdb_data = None
                    
                if search_btn and movie_search:
                    with st.spinner("Szukanie filmu w bazie TMDB..."):
                        res = search_tmdb_movie(movie_search)
                        if res:
                            st.session_state.tmdb_data = res
                            st.success("Znaleziono film!")
                        else:
                            st.error("Nie znaleziono takiego filmu w TMDB. Sprawdź pisownię lub klucz API.")
                            
            with col_preview:
                if st.session_state.tmdb_data:
                    data = st.session_state.tmdb_data
                    with st.container(border=True):
                        st.markdown(f"### **{data['title']}**")
                        if data.get("poster_url"):
                            st.image(data["poster_url"], width=160)
                        st.write(f"🎭 **Gatunek:** {data['genres']}")
                        st.write(f"🎬 **Reżyseria:** {data['director']}")
                        st.write(f"👥 **Obsada:** {data['cast_members']}")
                        
                        st.write("---")
                        rel_date = st.date_input("Wybierz datę polskiej premiery:")
                        
                        if st.button("🚀 Dodaj do Aktywnych Typowań", type="primary"):
                            supabase.table("movies").insert({
                                "title": data["title"],
                                "original_title": data["original_title"],
                                "poster_url": data["poster_url"],
                                "director": data["director"],
                                "cast_members": data["cast_members"],
                                "genres": data["genres"],
                                "release_date": str(rel_date),
                                "voting_open": True
                            }).execute()
                            st.session_state.tmdb_data = None
                            st.toast("Film dodany pomyślnie!", icon="🎬")
                            st.rerun()

        with tab_sync:
            st.subheader("Uzupełnianie brakujących metryczek")
            st.caption("Pobiera plakaty, reżyserów, obsadę i gatunki dla istniejących filmów, które mają w bazie wartość NULL.")
            
            if st.button("⚡ Rozpocznij pobieranie metryczek dla braków", type="primary"):
                with st.spinner("Pobieranie i synchronizacja danych..."):
                    missing_movies = supabase.table("movies").select("*").is_("poster_url", "null").execute().data
                    
                    if not missing_movies:
                        st.info("Wszystkie filmy w bazie mają już kompletne metryczki!")
                    else:
                        updated_count = 0
                        for m in missing_movies:
                            movie_info = search_tmdb_movie(m["title"])
                            if movie_info:
                                supabase.table("movies").update({
                                    "original_title": movie_info["original_title"],
                                    "poster_url": movie_info["poster_url"],
                                    "director": movie_info["director"],
                                    "cast_members": movie_info["cast_members"],
                                    "genres": movie_info["genres"]
                                }).eq("id", m["id"]).execute()
                                updated_count += 1
                                
                        st.success(f"Zaktualizowano pomyślnie {updated_count} filmów!")
                        st.rerun()

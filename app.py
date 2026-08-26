import streamlit as st
from supabase import create_client

# Konfiguracja Supabase
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

st.title("🎬 Ligowy Box Office - Test MVP")

# Sesja użytkownika
if "user" not in st.session_state:
    st.session_state.user = None

# LOGOWANIE / REJESTRACJA
if not st.session_state.user:
    tab1, tab2 = st.tabs(["Logowanie", "Rejestracja"])
    
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Hasło", type="password")
        if st.button("Zaloguj"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.error("Błąd logowania. Sprawdź dane.")
                
    with tab2:
        name = st.text_input("Imię i Nazwisko")
        reg_email = st.text_input("Email ", key="reg_e")
        reg_pass = st.text_input("Hasło ", type="password", key="reg_p")
        if st.button("Zarejestruj się"):
            try:
                res = supabase.auth.sign_up({
                    "email": reg_email, 
                    "password": reg_pass,
                    "options": {"data": {"full_name": name}}
                })
                st.success("Konto utworzone! Możesz się zalogować.")
            except Exception as e:
                st.error(f"Błąd rejestracji: {e}")

else:
    # PANEL ZALOGOWANEGO UŻYTKOWNIKA
    st.sidebar.write(f"Zalogowano jako: **{st.session_state.user.email}**")
    if st.sidebar.button("Wyloguj"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()
        
    menu = st.sidebar.radio("Nawigacja", ["Obstawiaj Filmy", "Tabela Ligi"])
    
    if menu == "Obstawiaj Filmy":
        st.subheader("🎯 Wytypuj otwarcia na najbliższy weekend")
        
        # Pobierz aktywne filmy
        movies = supabase.table("movies").select("*").eq("voting_open", True).execute().data
        
        if not movies:
            st.info("Brak aktywnych filmów do typowania w tym tygodniu.")
        else:
            for m in movies:
                with st.form(key=f"movie_{m['id']}"):
                    st.write(f"### {m['title']} (Premiera: {m['release_date']})")
                    val = st.number_input("Twoja estymacja (w PLN):", min_value=0, step=10000, key=f"val_{m['id']}")
                    
                    if st.form_submit_button("Zapisz typ"):
                        # Sprawdź czy już typował
                        existing = supabase.table("predictions").select("*")\
                            .eq("user_id", st.session_state.user.id)\
                            .eq("movie_id", m['id']).execute().data
                            
                        if existing:
                            supabase.table("predictions").update({"estimated_opening": val})\
                                .eq("id", existing[0]['id']).execute()
                            st.success("Zaktualizowano Twój typ!")
                        else:
                            supabase.table("predictions").insert({
                                "user_id": st.session_state.user.id,
                                "movie_id": m['id'],
                                "estimated_opening": val
                            }).execute()
                            st.success("Zapisano Twój typ!")

    elif menu == "Tabela Ligi":
        st.subheader("🏆 Tabela Wyników")
        
        # Pobierz podsumowanie punktów
        data = supabase.table("predictions").select("user_id, points, profiles(full_name)").execute().data
        
        # Proste zsumowanie w Pythonie
        scores = {}
        for row in data:
            name = row.get('profiles', {}).get('full_name', 'Nieznany') if row.get('profiles') else 'Ekspert'
            scores[name] = scores.get(name, 0) + (row.get('points') or 0)
            
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for idx, (player, pts) in enumerate(sorted_scores, start=1):
            st.write(f"**{idx}. {player}** — {pts} pkt ({pts * 0.5} PLN)")

import streamlit as st
import requests
from streamlit_chat import message

# Konfiguriere die Rasa API-URL
RASA_SERVER_URL = "http://localhost:5005/webhooks/rest/webhook"

# Systemnachricht für den Bot (nicht relevant für Bot, nur zur Ansicht für Entwickler)
system_prompt = """Du bist ein Handball-Trainingsbot. Du hilfst Nutzern bei der Auswahl von Übungen
und Trainingsprogrammen. Beispiele für Fragen:
- Welche Übungen gibt es für Schnelligkeit?
- Was sind gute Abwehrübungen für Kinder?
- Welche Übungen passen zu Anfängern im Bereich Werfen?
"""

# Session-State initialisieren für Nachrichten
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Seitenlayout
st.set_page_config(page_title="Handball-Trainingsbot", layout="centered")

# Titel mit Handball-Emoji
st.markdown("<h1 style='text-align: center;'>🤾‍♂️ Handball-Trainingsbot 🤾‍♀️</h1>", unsafe_allow_html=True)


# Nachrichten senden und empfangen
def generate_response(prompt):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    try:
        # Anfrage an den Rasa-Server senden
        response = requests.post(RASA_SERVER_URL, json={"sender": "streamlit_user", "message": prompt})
        if response.status_code == 200:
            rasa_responses = response.json()
            # Füge alle Antworten des Bots der Nachrichtenliste hinzu
            for rasa_response in rasa_responses:
                bot_response = rasa_response.get("text", "Ich konnte keine Antwort finden.")
                st.session_state["messages"].append({"role": "assistant", "content": bot_response})
        else:
            bot_response = "Fehler beim Abrufen der Antwort vom Rasa-Server."
            st.session_state["messages"].append({"role": "assistant", "content": bot_response})
    except Exception as e:
        bot_response = f"Fehler: {str(e)}"
        st.session_state["messages"].append({"role": "assistant", "content": bot_response})

# Konversation zurücksetzen
def reset_conversation():
    st.session_state["messages"] = []  # Nachrichtenverlauf zurücksetzen
    try:
        # Sende einen speziellen Reset-Intent an den Rasa-Server
        requests.post(RASA_SERVER_URL, json={"sender": "streamlit_user", "message": "/custom_restart"})
    except Exception as e:
        st.error(f"Fehler beim Zurücksetzen der Konversation: {str(e)}")

# Eingabefeld und Antworten anzeigen
response_container = st.container()
input_container = st.container()

# Reset-Button in der Sidebar
st.sidebar.title("⚙️ Optionen")
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reset Chat"):
    reset_conversation()
st.sidebar.markdown("**Weitere Einstellungen folgen bald!**")
st.sidebar.subheader("ℹ️ Über den Bot")
st.sidebar.info("""
Dieser **Handball-Trainingsbot** hilft dir dabei, gezielte Trainingsübungen für verschiedene **Ziele**, **Altersgruppen** und **Leistungsklassen** zu finden.

**Du kannst fragen:**
- Welche Übungen gibt es für die Abwehr?
- Zeige mir Passen Übungen für Anfänger.
- Ich brauche ein Wurftraining für unter 16 jährige.

Probiere es aus und lass uns loslegen! 🤾‍♂️
""")

# Eingabefeld für den Nutzer
with input_container:
    with st.form(key="user_input_form", clear_on_submit=True):
        user_input = st.text_input("Du:", placeholder="Stelle deine Trainingsfrage hier...")
        submit_button = st.form_submit_button(label="Senden")

# Antwort generieren und Verlauf aktualisieren
if submit_button and user_input:
    generate_response(user_input)

# Chatverlauf anzeigen
if st.session_state["messages"]:
    with response_container:
        for i, msg in enumerate(st.session_state["messages"]):
            if msg["role"] == "user":
                message(msg["content"], is_user=True, key=f"user_{i}")
            else:
                message(msg["content"], key=f"bot_{i}")


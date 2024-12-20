from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pandas as pd
from rasa_sdk.forms import FormValidationAction



# Eine globale Variable oder Sitzungstracker, um Übungen zu speichern
ALREADY_SUGGESTED_EXERCISES = {}

class ActionProvideExercise(Action):
    def name(self) -> Text:
        return "action_provide_exercise"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Pfad zur Excel-Datei
        excel_path = "/Users/nicohofmann/StudiumWI/ChatBot2/SecondTry/trainings.xlsx"

        # Slots abrufen
        goal = tracker.get_slot("goal")
        age_group = tracker.get_slot("age_group")
        skill_level = tracker.get_slot("skill_level")

        # Sitzungsspezifischer Schlüssel erstellen
        user_session_id = tracker.sender_id
        session_key = f"{user_session_id}_{goal}_{age_group}_{skill_level}"

        # Übungen aus der Excel-Datei laden
        try:
            data = pd.read_excel(excel_path)
            data.columns = ["age_group", "goal", "skill_level", "exercise", "equipment", "duration", "exercise_long"]
        except Exception as e:
            dispatcher.utter_message(text=f"Fehler beim Laden der Excel-Datei: {e}")
            return []

        # Filterlogik anwenden
        filtered_data = data[
            (data["goal"].str.strip().str.lower() == goal.strip().lower()) &
            (data["age_group"].str.strip().str.lower() == age_group.strip().lower()) &
            (data["skill_level"].str.strip().str.lower() == skill_level.strip().lower())
        ]

        # Speichern oder Initialisieren bereits vorgeschlagener Übungen
        if session_key not in ALREADY_SUGGESTED_EXERCISES:
            ALREADY_SUGGESTED_EXERCISES[session_key] = []

        suggested_exercises = ALREADY_SUGGESTED_EXERCISES[session_key]

        # Neue Übung suchen, die noch nicht vorgeschlagen wurde
        new_exercises = filtered_data[~filtered_data["exercise"].isin(suggested_exercises)]

        if not new_exercises.empty:
            exercise = new_exercises.iloc[0]
            suggested_exercises.append(exercise["exercise"])  # Übung zur Liste hinzufügen

            # Erste Nachricht zur Übung
            dispatcher.utter_message(
                text=f"Hier ist eine neue Übung für dich: {exercise['exercise']}\n"
                     f"Ausrüstung: {exercise['equipment']}\n"
                     f"Dauer: {exercise['duration']}\n\n"
                     f"{exercise['exercise_long']}\n\n"
                     f"Wenn du noch eine weitere Übung der gleichen Kategorie möchtest, dann schreibe dies einfach.\n\n"
                     f"Wenn du von vorne starten möchtest, dann schreibe einfach `reset`."
            )

        else:
            dispatcher.utter_message(
                text="Ich habe dir bereits alle passenden Übungen gezeigt.\n"
                     "Gebe einfach `reset` ein und du kannst nochmal von vorne starten."

            )

        ALREADY_SUGGESTED_EXERCISES[session_key] = suggested_exercises  # Update speichern
        return []

class ActionRestartConversation(Action):
    def name(self) -> Text:
        return "action_restart_custom"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Slots zurücksetzen
        events = [
            SlotSet("goal", None),
            SlotSet("age_group", None),
            SlotSet("skill_level", None)
        ]

        # Neustartnachricht senden
        dispatcher.utter_message(text="Kein Problem! Lass uns von vorne anfangen. Was möchtest du trainieren?")

        # Rückgabe der Standard-Reset-Aktion
        events.append({"event": "restart"})
        return events


class ValidateExerciseForm(FormValidationAction):
    def name(self) -> str:
        return "validate_exercise_form"

    def validate_age_group(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Synonyme für U12, U16 und Erwachsene
        synonym_mapping = {
            # U12 Synonyme
            "u9": "U12", "u10": "U12", "u11": "U12", "u12": "U12",
            "unter 9": "U12", "unter 10": "U12", "unter 11": "U12", "unter 12": "U12",
            "9 jahre alte kinder": "U12", "10 jahre alte kinder": "U12", "11 jahre alte kinder": "U12",
            "9-jährige": "U12", "10-jährige": "U12", "11-jährige": "U12", "12-jährige": "U12",
            "kleine kinder": "U12", "kinder": "U12", "grundschulkinder": "U12",
            "schulkinder": "U12", "junge kinder": "U12", "kinder bis 12 jahre": "U12",
            "kinder im grundschulalter": "U12", "grundschüler": "U12", "unter 12 jährige": "U12",
            "unter 11 jährige": "U12", "unter 10 jährige": "U12", "unter 9 jährige": "U12",

            # U16 Synonyme
            "u13": "U16", "u14": "U16", "u15": "U16", "u16": "U16",
            "unter 13": "U16", "unter 14": "U16", "unter 15": "U16", "unter 16": "U16",
            "13 jahre alte jugendliche": "U16", "14 jahre alte jugendliche": "U16",
            "15 jahre alte jugendliche": "U16", "16 jahre alte jugendliche": "U16",
            "13-jährige": "U16", "14-jährige": "U16", "15-jährige": "U16", "16-jährige": "U16",
            "jugendliche": "U16", "teenager": "U16", "heranwachsende": "U16",
            "jugendspieler": "U16", "schüler": "U16", "jugendmannschaft": "U16",
            "junge erwachsene": "U16", "jugendliche ab 13 jahren": "U16", "unter 16 jährige": "U16",
            "unter 15 jährige": "U16", "unter 14 jährige": "U16", "unter 13 jährige": "U16",

            # Erwachsene Synonyme
            "u17": "Erwachsene", "u18": "Erwachsene", "ü18": "Erwachsene", "unter 17": "Erwachsene",
            "unter 18": "Erwachsene", "erwachsene": "Erwachsene", "senioren": "Erwachsene",
            "ü20": "Erwachsene", "ab 20 jahre": "Erwachsene",
            "20 jahre alte spieler": "Erwachsene", "erwachsene spieler": "Erwachsene",
            "erwachsene mannschaft": "Erwachsene", "training für erwachsene": "Erwachsene",
            "volljährige": "Erwachsene", "menschen über 18": "Erwachsene",
            "seniorenspieler": "Erwachsene", "ab 18": "Erwachsene"
        }

        # Eingabe bereinigen und zuordnen
        cleaned_value = slot_value.strip().lower()
        mapped_value = synonym_mapping.get(cleaned_value)

        # Allgemeine Meldung bei unbekanntem Wert
        if not mapped_value:
            dispatcher.utter_message(
                text="Das habe ich leider nicht verstanden. Bitte gib eine der folgenden Altersgruppen an: "
                     "`unter 12`, `unter 16` oder `Erwachsene`."
            )
            return {"age_group": None}

        # Rückmeldung bei erfolgreichem Mapping
        dispatcher.utter_message(f"Du möchtest Übungen für die Altersgruppe '{mapped_value}' haben.")
        return {"age_group": mapped_value}

    def validate_goal(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    #) -> Dict[Text, Any]:
    ) -> List[Dict[Text, Any]]:
        # Synonyme für die Ziele (goal)
        synonym_mapping = {
            # Fangen
            "fangübungen": "Fangen", "ballfangen": "Fangen", "bälle fangen": "Fangen",
            "fangtraining": "Fangen", "übungen zum ballfangen": "Fangen",
            "übungen für ballannahme": "Fangen", "Fangen": "Fangen", "fangen": "Fangen",

            # Kondition
            "ausdauer": "Kondition", "fitness": "Kondition", "konditionstraining": "Kondition",
            "lauftraining": "Kondition", "schnelligkeit": "Kondition",
            "intervalltraining": "Kondition", "zirkeltraining": "Kondition",
            "laufübungen": "Kondition", "ausdauertraining": "Kondition",
            "sprinttraining": "Kondition", "kondition": "Kondition",

            # Passen
            "passübungen": "Passen", "passspiel": "Passen", "pässe trainieren": "Passen",
            "passkombinationen": "Passen", "passgenauigkeit": "Passen", "passen": "Passen",

            # Werfen
            "wurfkraft": "Werfen", "kraft beim werfen": "Werfen", "starkes werfen": "Werfen",
            "wurftechnik": "Werfen", "stärke beim werfen": "Werfen", "ballwurf": "Werfen",
            "wurftraining": "Werfen", "würfe üben": "Werfen", "werftraining": "Werfen",
            "werfen": "Werfen",

            # Abwehr
            "abwehrarbeit": "Abwehr", "verteidigungsübungen": "Abwehr", "defensive": "Abwehr",
            "abwehrtraining": "Abwehr", "abwehrtechniken": "Abwehr", "blockarbeit": "Abwehr",
            "verteidigungstraining": "Abwehr", "defensivarbeit": "Abwehr", "Abwehr": "Abwehr",
            "abwehr": "Abwehr"
        }

        # Eingabe bereinigen und Synonym prüfen
        cleaned_value = slot_value.strip().lower()
        mapped_value = synonym_mapping.get(cleaned_value)

        if mapped_value:
            dispatcher.utter_message(f"Du möchtest also Übungen für den Schwerpunkt '{mapped_value}' haben.")
            return {"goal": mapped_value}
        else:
            dispatcher.utter_message(
                text="Das habe ich leider nicht verstanden. Bitte gib eines der folgenden Ziele an: "
                     "`Fangen`, `Kondition`, `Passen`, `Werfen` oder `Abwehr`."
            )
            return {"goal": None}

    def validate_skill_level(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        # Synonyme für skill_level
        synonym_mapping = {
            # Synonyme für Anfänger
            "anfaenger": "Anfänger", "anfänger": "Anfänger", "einsteiger": "Anfänger",
            "neulinge": "Anfänger", "amateure": "Anfänger", "anfängerlevel": "Anfänger",
            "nicht gut": "Anfänger", "nicht sehr gut": "Anfänger", "unerfahren": "Anfänger",
            "nicht sehr gute spieler": "Anfänger", "grundkenntnisse": "Anfänger",
            "wenig erfahrung": "Anfänger", "spieler ohne erfahrung": "Anfänger", "schlechte spieler": "Anfänger",

            # Synonyme für Fortgeschrittene
            "fortgeschrittene": "Fortgeschrittene", "geübte": "Fortgeschrittene",
            "fortgeschrittenenlevel": "Fortgeschrittene", "spieler mit erfahrung": "Fortgeschrittene",
            "mittleres niveau": "Fortgeschrittene", "spieler mit übung": "Fortgeschrittene",
            "solide spieler": "Fortgeschrittene", "semi-professionell": "Fortgeschrittene",
            "durchschnittlich": "Fortgeschrittene", "fortgeschrittenes niveau": "Fortgeschrittene",
            "erfahrene spieler": "Fortgeschrittene", "geübte spieler": "Fortgeschrittene",
            "fortgeschrittene spieler": "Fortgeschrittene",

            # Synonyme für Profis
            "profis": "Profis", "experten": "Profis", "spitzenspieler": "Profis",
            "top-spieler": "Profis", "profi-niveau": "Profis", "profispieler": "Profis",
            "höchstes niveau": "Profis", "professionelle spieler": "Profis", "erfahrene profis": "Profis",
            "expertenlevel": "Profis", "liga-niveau": "Profis", "spieler auf profiniveau": "Profis",
            "sehr gut": "Profis", "meisterschaftsniveau": "Profis", "nachwuchsprofis": "Profis"
        }

        # Eingabe bereinigen und zuordnen
        cleaned_value = slot_value.strip().lower()
        mapped_value = synonym_mapping.get(cleaned_value)

        # Wenn der Wert zugeordnet werden kann
        if mapped_value:
            dispatcher.utter_message(f"Du hast das Leistungsniveau '{mapped_value}' ausgewählt.")
            return {"skill_level": mapped_value}
        else:
            # Ungültiger Wert -> Slot zurücksetzen und Rückfrage
            dispatcher.utter_message(
                text="Das habe ich nicht verstanden. Bitte gib eines der folgenden Leistungsniveaus an: "
                     "`Anfänger`, `Fortgeschrittene` oder `Profis`."
            )
            return {"skill_level": None}

# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

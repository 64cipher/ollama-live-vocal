import speech_recognition as sr
from gtts import gTTS
import os
import playsound
import ollama
import threading
import re
import time

class AssistantVocal:
    def __init__(self, model="llama3.2", trigger_phrase="ok lama"):
        self.r = sr.Recognizer()
        self.model = model
        self.trigger_phrase = trigger_phrase
        self.is_listening = False
        self.stop_listening_event = threading.Event()
        self.audio_source = None
        self.audio_stream = None

    def speak(self, text):
         # Nettoyage du texte avant la synthèse vocale
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s.,?!;:\çàâäéèêëîïôöûüÿœ]', '', text) # Ajout des accents français
        tts = gTTS(text=cleaned_text, lang='fr')
        tts.save("response.mp3")
        playsound.playsound("response.mp3")
        os.remove("response.mp3")


    def listen(self):
        print("En attente de 'ok lama'...")
        self.r.adjust_for_ambient_noise(self.audio_stream)
        while not self.stop_listening_event.is_set():
            try:
                audio = self.r.listen(self.audio_stream, phrase_time_limit=5)
                text = self.r.recognize_google(audio, language="fr-FR")
                print(f"Vous avez dit : {text}")
                if self.trigger_phrase in text.lower():
                    self.process_command()
            except sr.WaitTimeoutError:
              continue
            except sr.UnknownValueError:
              continue
            except sr.RequestError:
                print("Erreur de connexion au service de reconnaissance vocale")
                break

    def process_command(self):
        print("En écoute...")
        self.is_listening = True
        self.speak("Dites-moi tout")  # Réponse vocale
        try:
            audio = self.r.listen(self.audio_stream, phrase_time_limit=5)
            text = self.r.recognize_google(audio, language="fr-FR")
            print(f"Requête : {text}")
            self.handle_query(text)
        except sr.WaitTimeoutError:
            print("Aucune requête détectée.")
        except sr.UnknownValueError:
            print("Je n'ai pas compris votre requête.")
        except sr.RequestError:
            print("Erreur de connexion au service de reconnaissance vocale")
        finally:
           self.is_listening = False

    def handle_query(self, query):
      try:
          response_chunks = []
          full_response = ""

          for part in ollama.chat(model=self.model, messages=[{'role': 'user', 'content': query}], stream=True):
              if 'content' in part['message']:
                response_chunks.append(part['message']['content'])
          full_response = "".join(response_chunks)
          print(f"Llama3.2: {full_response}")
          self.speak(full_response)
      except Exception as e:
          print(f"Une erreur s'est produite lors de la communication avec le LLM : {e}")


    def run(self):
        self.audio_source = sr.Microphone()
        with self.audio_source as source:
            self.audio_stream = source
            self.stop_listening_event.clear()
            listen_thread = threading.Thread(target=self.listen, daemon=True)
            listen_thread.start()
            try:
                listen_thread.join()
            except KeyboardInterrupt:
                print("\nArrêt de l'assistant.")
                self.stop_listening_event.set()
            finally:
              if self.audio_stream:
                 self.audio_stream.stream.close()


if __name__ == "__main__":
    assistant = AssistantVocal()
    assistant.run()
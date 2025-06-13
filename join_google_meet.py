from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv
from record_audio import AudioRecorder
from speech_to_text import SpeechToText
import tempfile

load_dotenv()


class GoogleMeetBot:
    def __init__(self):
        # Cargar configuración
        self.email = os.getenv("EMAIL_ID")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.meet_name = os.getenv("MEET_NAME", "Bot Usuario")

        if not self.email or not self.password:
            raise ValueError("Credenciales faltantes en .env")

        # Configurar Chrome con perfil persistente
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-blink-features=AutomationControlled")

        # IMPORTANTE: Usar un perfil de usuario para mantener la sesión
        options.add_argument("--user-data-dir=/tmp/chrome_profile")

        options.add_experimental_option(
            "prefs",
            {
                "profile.default_content_setting_values.media_stream_mic": 1,
                "profile.default_content_setting_values.media_stream_camera": 1,
                "profile.default_content_setting_values.notifications": 1,
            },
        )

        service = Service("/usr/bin/chromedriver")
        self.driver = webdriver.Chrome(service=service, options=options)

    def login(self):
        """Iniciar sesión en Google"""
        # Primero verificar si ya estamos logueados
        self.driver.get("https://myaccount.google.com/")
        time.sleep(3)

        # Si no estamos logueados, hacer login
        if "accounts.google.com" in self.driver.current_url:
            print("Iniciando sesión...")

            # input Gmail
            self.driver.find_element(By.ID, "identifierId").send_keys(self.email)
            self.driver.find_element(By.ID, "identifierNext").click()
            time.sleep(3)

            # input Password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input')
                )
            )
            password_field.send_keys(self.password)
            self.driver.find_element(By.ID, "passwordNext").click()
            time.sleep(5)

        print("✓ Sesión activa")

    def turn_off_mic_cam(self):
        """Desactivar micrófono y cámara antes de unirse"""
        print("Desactivando micrófono y cámara...")

        # Buscar y clickear el botón de micrófono
        try:
            # El botón de micrófono suele tener estos atributos
            mic_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        '[data-is-muted="false"][aria-label*="microphone" i],'
                        '[data-is-muted="false"][aria-label*="mic" i]',
                    )
                )
            )
            mic_button.click()
            print("✓ Micrófono desactivado")
        except:
            # Si no lo encuentra, buscar por otras formas
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, '[role="button"]')
                for button in buttons:
                    aria_label = button.get_attribute("aria-label") or ""
                    if (
                        "microphone" in aria_label.lower()
                        or "mic" in aria_label.lower()
                    ):
                        if (
                            "turn off" in aria_label.lower()
                            or not "turn on" in aria_label.lower()
                        ):
                            button.click()
                            print("✓ Micrófono desactivado")
                            break
            except:
                print("⚠ No se pudo desactivar el micrófono")

        time.sleep(1)

        # Buscar y clickear el botón de cámara
        try:
            # El botón de cámara suele tener estos atributos
            cam_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        '[data-is-muted="false"][aria-label*="camera" i],'
                        '[data-is-muted="false"][aria-label*="cam" i]',
                    )
                )
            )
            cam_button.click()
            print("✓ Cámara desactivada")
        except:
            # Si no lo encuentra, buscar por otras formas
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, '[role="button"]')
                for button in buttons:
                    aria_label = button.get_attribute("aria-label") or ""
                    if "camera" in aria_label.lower() or "cam" in aria_label.lower():
                        if (
                            "turn off" in aria_label.lower()
                            or not "turn on" in aria_label.lower()
                        ):
                            button.click()
                            print("✓ Cámara desactivada")
                            break
            except:
                print("⚠ No se pudo desactivar la cámara")

    def join_meet(self, meet_link):
        """Unirse a la reunión"""
        # IMPORTANTE: Ir primero a meet.google.com para establecer contexto
        self.driver.get("https://meet.google.com/")
        time.sleep(3)

        # Ahora sí ir al link de la reunión
        self.driver.get(meet_link)
        time.sleep(5)

        # Manejar posible recarga si hay error de credenciales
        if "reload" in self.driver.page_source.lower():
            print("Recargando página...")
            self.driver.refresh()
            time.sleep(5)

        # Desactivar micrófono y cámara ANTES de ingresar el nombre
        self.turn_off_mic_cam()

        # Ingresar nombre
        try:
            name_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@placeholder='Your name']")
                )
            )
            name_field.click()
            name_field.clear()
            name_field.send_keys(self.meet_name)
            print(f"✓ Nombre ingresado: {self.meet_name}")
        except Exception as e:
            print(f"✗ Error al ingresar nombre: {e}")

        # Click en Ask to join
        time.sleep(2)
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if "Ask to join" in button.text or "join" in button.text.lower():
                    button.click()
                    print("✓ Solicitando unirse")
                    break
        except Exception as e:
            print(f"✗ Error al hacer click en join: {e}")

    def record_meeting(self, duration=60):
        """Grabar la reunión"""
        time.sleep(10)

        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "recording.wav")

        print(f"✓ Grabando por {duration} segundos...")
        AudioRecorder().get_audio(audio_path, duration)

        print("✓ Transcribiendo...")
        SpeechToText().transcribe(audio_path)

    def close(self):
        """Cerrar navegador"""
        self.driver.quit()
        print("✓ Navegador cerrado")


def main():
    bot = None
    try:
        meet_link = os.getenv("MEET_LINK")
        duration = int(os.getenv("RECORDING_DURATION", 60))

        if not meet_link:
            raise ValueError("MEET_LINK faltante en .env")

        bot = GoogleMeetBot()
        bot.login()
        bot.join_meet(meet_link)
        bot.record_meeting(duration)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if bot:
            bot.close()


if __name__ == "__main__":
    main()

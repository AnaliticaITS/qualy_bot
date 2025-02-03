import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from icecream import ic
from pythonjsonlogger.json import JsonFormatter

#=========================================== Logs Config =============================================
formatter = JsonFormatter()
json_handler = logging.FileHandler("./logs/bot_backlog_diario.json")
json_handler.setFormatter(formatter)
logging.basicConfig(
    level = logging.INFO,
    handlers = [
        json_handler,
        logging.StreamHandler()
    ]
)


#============================================ Variables =============================================
username = os.getenv("USERNAME_SERVICE")
password = os.getenv("PASSWORD_SERVICE")
chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service)


try:
    # Abrir pagina de service manager
    driver.get("https://servicio.triara.co/index.do")
    
    # Esperar a que los campos esten disponibles
    wait = WebDriverWait(driver, 10)
    username_field = wait.until(EC.presence_of_element_located((By.ID, "LoginUsername")))
    password_field = wait.until(EC.presence_of_element_located((By.ID, "LoginPassword")))
    
    # Ingresar credenciales
    username_field.send_keys(username)
    password_field.send_keys(password)
    
    # Click en boton "Conexion"
    login_button = driver.find_element(By.ID, "loginBtn")
    login_button.click()
    
    time.sleep(40)
    
    # Validar si el login fue exitoso
    login_success = wait.until(EC.presence_of_element_located((By.ID, "cwcAccordionNav")))
    ic(login_success)
    if login_success:  
        logging.info(f"Inicio de sesión exitoso")
    else:
        logging.info(f"Error al iniciar sesión.")
    
    
    
    # CLick en "Gestion de incidentes"
    gestion_incidentes = driver.find_element(By.XPATH, "//*[@id='ROOT/Gestión de incidentes']") 
    gestion_incidentes.click()
    logging.info(f"Click exitoso en 'Gestion de incidentes'")
    time.sleep(10)
    
    # Click en "Buscar incidentes"
    buscar_incidente = driver.find_element(By.XPATH, "//*[@id='ROOT/Gestión de incidentes/Buscar incidentes']")
    buscar_incidente.click()
    logging.info(f"Click exitoso en 'Buscar incidentes'")
    time.sleep(10)    


except Exception as e:
    logging.error(f"Error de ejecucion: {e}")
            
finally:
    # Cerrar el navegador
    driver.quit()



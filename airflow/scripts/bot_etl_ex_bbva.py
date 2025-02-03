import os
import traceback
import logging
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from icecream import ic

#=================================================== Configuración De Logs ========================================================
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers = [
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("bot_etl_ex_bbva")

#======================================================= Variables  ======================================================
user_etl = os.getenv("USER_ETL_BBVA")
password_etl = os.getenv("PASSWORD_ETL_BBVA")
url_etl = os.getenv("URL_ETL_BBVA")
file = os.path.join(os.getenv("DOWNLOAD_DIR"), "Cerrados.xlsx")
bot_token = os.getenv("BOT_TOKEN")
id_chat = os.getenv("ID_CHAT")
url_api_telegram = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id_chat}&text="

#========================================================== Logic Developed ============================================================

def custom_exception(e, message:str):
    '''
    Funcion para personalizar Error Exception
    
    * Parametro:

        * ***e***: exception generada por error de ejecucion
        * ***message***(str): mensaje para mostrar
    '''
    error_type = type(e).__name__
    error_message = str(e)
    traceback_details = traceback.format_exc()
    custom_alert = f"{message}:\n***Error type:*** {error_type}\n***Error message:*** {error_message}\n***Full Traceback:*** {traceback_details}"
    return custom_alert
    

def main():
    '''
    Bot para cargar la data transformada para los proyectos Exito, Tuya, BBVA, SODIMAC a traves del frontend creado por I+D 
    '''
    try:
        logger.info("Bot ETL Exito-BBVA started")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--ignore-ssl-errors=yes")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        
        try:
            driver = webdriver.Remote(command_executor='http://selenium-hub:4444', options=chrome_options)
            logger.info("Conexión al Selenium Hub establecida correctamente")
        except Exception as e:
            message = custom_exception(e,"Error al conectar al Selenium Hub")
            logger.error(message)
        
        # Open ETL Url
        driver.get(url_etl)
        
        #Wait to fields availability
        wait = WebDriverWait(driver, 30)
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        
        # Input credentials for access
        username_field.send_keys(user_etl)
        password_field.send_keys(password_etl)
        logger.info("Credentials input success")
        
        # Click in "Ingresar"
        login_button = driver.find_element(By.XPATH, "//*[@id='auth-container']/form/button")
        login_button.click()
        logger.info("Click in login button")
        time.sleep(10)
        
        login_success = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='card-cargue']/div/div[2]/button")))
        if login_success:  
            logger.info(f"Loging success")
        else:
            logger.info(f"Error begining session.")
        
        # Input path file Cerrados.xlsx
        load_file_button = driver.find_element(By.XPATH, "//*[@id='card-cargue']/div/div[2]/button")
        load_file_button.click()
        file_input = wait.until(EC.presence_of_element_located((By.ID, "formFile")))
        file_input.send_keys(file)
        
                
        #Click in "Subir"
        up_button = driver.find_element(By.XPATH, "//*[@id='exampleModalCenter']/div/div/form/div[2]/button[2]")
        up_button.click()
        logger.info("Input file succes")
        time.sleep(5)
        
        #Click in "Cargar"
        load_button = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/main/div/div/div[3]/div/div/form/button")))
        load_button.click()
        logger.info("Click in Cargar")
        time.sleep(5)
        
        error_text = driver.execute_script("return document.querySelector('.alert-danger')?.textContent;")
        
        if error_text:
            message = f"{'*'*40}\n\nETL EX-TY-BBVA-SODIMAC\n\n❌Error de Ejecución❌\n\n{error_text.strip()}\n\n{'*'*40}"
            requests.get(f"{url_api_telegram}{message}")
        else:
            message = f"{'*'*40}\n\nETL EX-TY-BBVA-SODIMAC\n\n✅Ejecucion Exitosa✅\n\narchivo Cerrados.xlsx cargado con exito\n\n{'*'*40}"
            requests.get(f"{url_api_telegram}{message}")                     
    
    except Exception as e:
        message = custom_exception(e, "Error Loading Cerrados.xlsx to ETL")
        logger.error(message)
        driver.quit()
        
    finally:
        logger.info("bot_etl_ex_bbva finish execution")
        driver.quit()
        return
        
        
if __name__=="__main__":
    main()
    
    
    
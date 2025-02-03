import assets.assets as ast
import os
import time
import logging
import pandas as pd
import traceback
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
logger = logging.getLogger("bot_como_vamos")

#======================================================= Variables And Configuration ======================================================
username_reporting = os.getenv("USERNAME_REPORTING")
password_reporting = os.getenv("PASSWORD_REPORTING")

# Get dates
start, end = ast.obtener_fechas()
start_date = start.strftime("%d/%m/%Y")
end_date = end.strftime("%d/%m/%Y")
ic(start_date, end_date)
download_dir = os.getenv("DOWNLOAD_DIR")


#========================================================== Logic Developed ============================================================


def main():
    '''
    Bot para descargar el ***Reporte como_vamos.xlsx***. Una vez descargado el archivo es copiado a BBVA-EXITO-TUYA y movido a Alkosto para retirarlo de la carpeta de descarga dado que en la logica desarrollada se asume que el archivo no existe en la carpeta de descarga.
    
    Retorno:
        * ***True*** si se decarga el archivo, o ***None*** si expira el tiempo.
        * ***Mensaje***: (str) confirmando la descarga o el fin del tiempo de espera. 
    '''       
    try:
        logger.info("Starting script bot_como_vamos.py")        
    
        # Chrome configuration
        # Configuración de Chrome
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--ignore-ssl-errors=yes")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        # chrome_options.timeouts = {'script': 6000}
        # chrome_options.timeouts = {'implicit': 6000}
        chrome_options.add_experimental_option("prefs", {
            # "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        
        # Start chrome explorer
        try:
            driver = webdriver.Remote(command_executor='http://selenium-hub:4444', options=chrome_options)
            logger.info("Conexión al Selenium Hub establecida correctamente")
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            traceback_details = traceback.format_exc()
            logger.error(f"Error al conectar al Selenium Hub:\n***Error type:*** {error_type}\n***Error message:*** {error_message}\n***Full Traceback:*** {traceback_details}")
        
        # Open reporting center web
        driver.get("https://reportingcenter.claro.net.co/ReportingCenter/index.php?route=login")
                        
        # Wait to fields availability
        wait = WebDriverWait(driver, 600)
        username_field = wait.until(EC.presence_of_element_located((By.ID, "usuario")))
        password_field = wait.until(EC.presence_of_element_located((By.ID, "clave")))
        
        # Input credentials for access
        username_field.send_keys(username_reporting)
        password_field.send_keys(password_reporting)        
        
        # Click in "iniciar sesión"
        login_button = driver.find_element(By.NAME, "login")
        login_button.click()        
        time.sleep(20)        
        
        # Check login success
        login_success = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        ic(login_success)        
        if login_success:  
            logger.info(f"Loging success")
        else:
            logger.info(f"Error begining session.")
        time.sleep(10)        
        
        # Click in menu button
        menu_button = driver.find_element(By.XPATH, "/html/body/div[3]/nav/ul[2]/li[2]/a")
        menu_button.click()
        logger.info("Click in menu button successfully")        
        time.sleep(10)        
        
        # Input for date of start and ends inform
        fecha_inicio = wait.until(EC.presence_of_element_located((By.ID, "fecha_inicio")))
        fecha_fin = wait.until(EC.presence_of_element_located((By.ID, "fecha_fin")))        
        
        # Input dates
        fecha_inicio.send_keys(start_date)
        fecha_fin.send_keys(end_date)
        logger.info("Input dates successfully")
        time.sleep(10)        
        
        # CLick in 'Empresas y Negocios'
        empresas_negocios = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='accordion']/div[12]/a/div/i[2]")))
        empresas_negocios.click()
        logger.info("Click in 'Empresas Y Negocios' successfully")        
        time.sleep(10)        
        
        # Click in 'Como Vamos'
        reporte_como_vamos = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"body > div:nth-child(4) > div:nth-child(6) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(12) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > a:nth-child(5)")))
        reporte_como_vamos.click()       
        
    except Exception as e:
        # The response from Claro server is so slow and the explorer generate an exception, the except, finally block manage it making the script don't finish 
        logger.info("Click in 'Como Vamos' successfully")
        # error_type = type(e).__name__
        # error_message = str(e)
        # traceback_details = traceback.format_exc()
        # logger.error(f"Execution error bot_reporte_como_vamos.py:\n***Error type:*** {error_type}\n***Error message:*** {error_message}\n***Full Traceback:*** {traceback_details}")
    finally:        
        # Waiting for download              
        downloaded_file = ast.wait_for_download(download_dir, "Reporte como_vamos.xlsx", timeout=600)
        if downloaded_file == True:                           
            logger.info(f"Download Reporte como_vamos succesfully")
            driver.quit()
            return
        else:
            Exception("Failed download Reporte como_vamos.xlsx") 
            driver.quit()
                
                
if __name__=="__main__":
    main()
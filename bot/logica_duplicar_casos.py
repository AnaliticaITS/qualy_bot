import os
import requests
import pandas as pd
import re
import datetime as dt
import logging
from dateutil.relativedelta import relativedelta
from assets.assets import conexion_db, engine, ejecutar_consulta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from icecream import ic
from pythonjsonlogger.json import JsonFormatter

#=================================================== Configuración De Logs ========================================================

formatter = JsonFormatter()
json_handler = logging.FileHandler("./logs/duplicar_casos.json")
json_handler.setFormatter(formatter)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        json_handler,
        logging.StreamHandler()
    ]
)

# ================================================ Conexion a base de datos alkostocdc =================================================
conexion_db = conexion_db()
engine = engine()
esquema = "tableros_mensuales"

#====================================================== Declaración de Variables =======================================================
path_data_service = os.getenv("PATH_DATA_SERVICE")
path_dicc_enlaces = os.getenv("PATH_DICC_ENLACES")
hoja_dicc_enlaces = os.getenv("NOMBRE_HOJA_DICCIONARIO")
bot_token = os.getenv("BOT_TOKEN")
id_chat_analista = os.getenv("ID_CHAT_DEV") # Id usuario para confirmaciones al analista encargado   
 
    
#======================================================= Logica desarrollada ===========================================================

# Función para enviar mensaje de confirmación de inicio del bot al desarrolador encargado
if conexion_db:
    url_api_telegram = "https://api.telegram.org/bot" + bot_token + "/sendMessage?chat_id=" + id_chat_analista + "&text="
    mensaje = "Qualy's on line"
    requests.get(url_api_telegram + mensaje)


def obtener_fechas():
    """
    Función para obtener la fecha del primer y ultimo dia del mes anterior

    Retorno:
        fecha_inicio (date)
        fecha_fin (date)
        
    """ 
    hoy = dt.date.today()
    fecha_inicio = hoy - relativedelta(days=60)
    fecha_fin = hoy - relativedelta(days=1)

    return fecha_inicio, fecha_fin


def duplicar_enlaces_error_service():
    """
    Función que crea una fila para cada enlace secundario afectado,
    tomando como base los datos del IM del caso que se encuentran
    en la base de datos y reemplaza el valor de id_enlace por el enlace
    afectado que no fue reportado o duplicado por reporting center.   
                

    Retorno: 
        data_duplicada (dataframe): dataframe listo para cargar a la base de datos
    """
    
    try:
        fecha_inicio, fecha_fin = obtener_fechas()
        data_service = pd.read_excel(path_data_service)
        # Cargue de data necesaria 
        data_service["fecha_creacion"] = data_service['Fecha/hora de apertura'].dt.date
        data_service_filtrada = data_service.loc[data_service['fecha_creacion'].between(fecha_inicio, fecha_fin)]
        data_service_filtrada = data_service_filtrada.loc[data_service_filtrada['Servicios afectados secundarios'].notnull()]                         
        query = """SELECT * FROM alkostocdc.tableros_mensuales.incidentes_eventos WHERE id_caso IN %s;"""    
        lista_casos = tuple(
            data_service_filtrada["ID de incidente"].to_list()
        )# Creación de tupla que contenga los IM a consultar en la base para pasarla como parametro a la query
        data_bd = ejecutar_consulta(conexion_db, query, lista_casos)
        
        data_duplicada = pd.DataFrame()
        
        for index, row in data_service_filtrada.iterrows():
            enlaces_afectados = row.get("Servicios afectados secundarios")
            enlaces_afectados = str(enlaces_afectados).split(" ")

            for enlace in enlaces_afectados:
                check = data_bd[(data_bd['id_caso'] == row.get('ID de incidente')) & (data_bd['id_enlace'] == enlace)].empty
                print(check)
                if check:                
                    fila = data_bd.loc[data_bd["id_caso"] == row["ID de incidente"]].copy()
                    fila.drop("incrementador", axis=1, inplace=True)
                    fila["id_enlace"] = enlace
                    fila["duplicado"] = 'SI'
                    fila["motivo_duplicado"] = 'Error Service Manager'
                    data_duplicada = pd.concat([data_duplicada, fila], ignore_index=True)        
                                            
                else:
                    print(f"enlace {enlace} ya esta en base de datos") 
                           
        check = data_duplicada.empty
        if not check:        
            data_duplicada.to_sql("incidentes_eventos", con=engine, index=False, if_exists="append", schema=esquema)
            resumen = f"Se cargaron a la base de datos los siguientes enlaces:\n {data_duplicada.loc[:,['id_caso', 'id_enlace']]}"
        else:
            resumen = f'No se duplicó nada'
    
    except Exception as e:
        mensaje = f"🚫🚫 No se pudo ralizar la operación por un error interno en la ejecución 🚫🚫\n🚨 informe al analista de datos encargado 🚨\n❗ No se cargo nada a la base de datos ❗ \n\n {e}"
        print(f"Error de ejecucion\n\nMensaje de error:\n{e}")
        return mensaje
    else:
        mensaje = f"✅ Ejecución exitosa ✅\n\n🎯 Resultado de la operacion 🎯\n{resumen}"        
        print(f"Cargue a base de datos exitoso\n\nEjecución de Bot exitosa\n\nFin de ejecución")
        print(data_duplicada)
        return mensaje


def duplicar_enlaces_error_noc(im_caso):
    '''
    Función para buscar los enlaces afectados en el diccionario de enlaces 
    cuando se debe duplicar por error del NOC.
    
    
    Parámetros:        
        im_caso (str): IM del caso a duplicar por error del NOC        
    
    
    Retorna:
        lista_enlaces_sede (dataframe): dataframe con filas duplicadas por cada enlace
    '''
    try:
        # Cargue de data necesaria
        data_service = pd.read_excel(path_data_service)         
        diccionario_enlaces = pd.read_excel(path_dicc_enlaces
                , sheet_name=hoja_dicc_enlaces
            )
        query = """SELECT * FROM alkostocdc.tableros_mensuales.incidentes_eventos WHERE id_caso = %s;"""
        data_bd = ejecutar_consulta(conexion_db, query, im_caso)       
        data_bd.drop("incrementador", axis=1, inplace=True)
                    
        # Definición de variables necesarias
        id_enlace_principal = data_bd.loc[data_bd['id_caso']==im_caso, 'id_enlace'].values[0]        
        sede_afectada = diccionario_enlaces.loc[
            diccionario_enlaces["ID_ENLACE"] == id_enlace_principal, "NEGOCIO-SEDE"
        ].values[0]
        print(f"Enlace Principal {id_enlace_principal} \n Sede Afectada {sede_afectada}")
        regex_sdw1 = r"(?i)\bS[D]*WAN\s*1\b|MASIVA"
        regex_sdw2 = r"(?i)\bS[D]*WAN\s*1\s*[,y Y.]\s*2|\bSDWAN\s*2\b|MASIVA"
        regex_lan = r"LAN"
        regex_wifi = r"WIFI"
        regex_pbx = r"PBX"
        regex_tel = r"TELEFONIA"
        texto = str(
            data_service.loc[data_service["ID de incidente"] == im_caso, "Descripción"].values[0]
        )
        match_1 = re.search(regex_sdw1, texto, re.IGNORECASE)
        match_2 = re.search(regex_sdw2, texto, re.IGNORECASE)
        match_3 = re.search(regex_lan, texto, re.IGNORECASE)
        match_4 = re.search(regex_wifi, texto, re.IGNORECASE)
        match_5 = re.search(regex_pbx, texto, re.IGNORECASE)
        match_6 = re.search(regex_tel, texto, re.IGNORECASE)
        dict = {
            "SDWAN 1": match_1,
            "SDWAN 2": match_2,
            "LAN": match_3,
            "WIFI": match_4,
            "PBX": match_5,
            "TELEFONIA": match_6,
        }
        data_duplicada = pd.DataFrame()    
        for servicio in dict:
            lista_enlaces_sede = []
            match = dict[servicio]
            print(f"Match {servicio}:{match}")
            
            if match:           
                enlaces_servicio = diccionario_enlaces.loc[
                    diccionario_enlaces["NEGOCIO-SEDE"] == sede_afectada
                ]            
                enlaces_servicio = enlaces_servicio.loc[
                    enlaces_servicio["SUBTIPO_SERVICIO"] == servicio
                ]     
                print(f"Enlaces Sede {enlaces_servicio}")
                for index, row in enlaces_servicio.iterrows():
                    enlace = row.get("ID_ENLACE")
                    print(f"Enlace {enlace}")
                    if data_bd.loc[data_bd['id_caso']==im_caso, 'id_enlace'].values[0] != enlace:
                        lista_enlaces_sede.append(enlace)
                        for enlace in lista_enlaces_sede:
                            fila = data_bd       
                            fila["id_enlace"] = enlace
                            fila["duplicado"] = 'SI'
                            fila["motivo_duplicado"] = 'Error NOC'
                            data_duplicada = pd.concat([data_duplicada, fila], ignore_index=True)
                    else:
                        print(f"enlace {enlace} ya esta en base de datos")
                        continue      
        # print(data_duplicada)
        check = data_duplicada.empty
        if not check:        
            data_duplicada.to_sql("incidentes_eventos", con=engine, index=False, if_exists="append", schema=esquema)
            resumen = f"Se cargaron a la base de datos los siguientes enlaces:\n {data_duplicada.loc[:,['id_caso', 'id_enlace']]}"
        else:
            resumen = f'No se duplicó nada'
                
            
    except Exception as e:
        mensaje = f"🚫🚫 Verifique que el IM esté correcto 🚫🚫\n🚨 De lo contrario informe al analista de datos encargado 🚨\n❗ No se cargo nada a la base de datos ❗ \n\n {e}"
        print(f"Error de ejecucion\n\nMensaje de error:\n{e}")
        
    else:
        mensaje = f"✅ Ejecución exitosa ✅\n🎯 Resultado de la operacion 🎯\n{resumen}"        
        print(f"Cargue a base de datos exitoso\n\nEjecución de Bot exitosa\n\nFin de ejecución")
        
    return mensaje




    
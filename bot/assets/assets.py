import datetime
import os
import pandas as pd
import time
import shutil
import logging
import mysql.connector
import psycopg2 as psy
from icecream import ic
from pythonjsonlogger.json import JsonFormatter
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine, exc
from dateutil.relativedelta import relativedelta
# import helpfiles.parametros as parametros

#========================================== Logs Config ==========================================
rotating_handler = RotatingFileHandler(
    "./logs/assets.json", maxBytes = 5 * 1024 * 1024, backupCount = 5
)
json_formatter = JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
)
rotating_handler.setFormatter(json_formatter)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        rotating_handler,
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("assets")

def obtener_fechas():
    """
    Función para obtener la fecha del primer dia del mes anterior y el dia actual
    
    return: fecha_inicio, hoy
    """
    hoy = datetime.date.today()
    fecha_inicio = datetime.date.today().replace(day=1)
    # fecha_fin = hoy.replace(day=1) - datetime.timedelta(days=1)
    return fecha_inicio, hoy


def wait_for_download(directory:str, file_name:str, timeout=600):
    """
    Espera hasta que se descargue un archivo en el directorio especificado.
    
    Parametros:
        * directory: Ruta del directorio de descargas.
        * nombre_archivo: Nombre del archivo que se debe rastrear
        * timeout: Tiempo máximo para esperar (en segundos) default=600 (10 minutos).
    
    Retorno:
        * True si se decarga el archivo, o None si expira el tiempo.
    """
    seconds = 0
    while seconds < timeout:
        files = os.listdir(directory)        
        for file in files:
            ic(file)
            if file == file_name:  # Archivo en progreso
                return True
        time.sleep(5)  # Espera 5 segundos antes de volver a verificar
        seconds += 5
    return None


def conexion_db():
    """
    Función para conectarse a PostgreSQL.    
    
    Retorno:
        * conexion(objeto psycopg2)
    """
    
    try:
          
        # Crear un diccionario con los parámetros
        params = {
            'host': os.getenv("HOST_DB_ALKOSTO"),
            'port': os.getenv("PORT_DB_ALKOSTO"),
            'database': os.getenv("DB_ALKOSTO"),
            'user': os.getenv("USER_DB_ALKOSTO"),
            'password': os.getenv("PASSWORD_DB_ALKOSTO")
        }
        ic(params)   

        # Establecer la conexión
        conexion = psy.connect(**params)
            

    except psy.OperationalError as e:
        print(f"Error al conectarse a la base de datos: {params['database']}")
        print(e)
    else:
        print(f"Conexión exitosa a la base de datos: {params['database']}")
        return conexion
        
  
def ejecutar_consulta(conexion, query:str, *args):
    '''
    Función que realiza querys a la base de datos postgres.

    Parametros: 
        * conexion (any): retorno de la función conexion_db
        * query(string): sql query 
        *args(any): parametros que se deben pasar a la query    
        
    Retorno: dataframe    
    '''
    
    cursor = conexion.cursor()
    cursor.execute(query, args)
    df = pd.DataFrame(data=cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    conexion.commit()
    cursor.close()
    return df


def engine():
    '''
    Función para crear motor de conexion para to_sql()
    
    Retorno:
        engine  
    '''
    try:
        
        # Crear un diccionario con los parámetros
        params = {
            'host': os.getenv("HOST_DB_ALKOSTO"),
            'port': os.getenv("PORT_DB_ALKOSTO"),
            'database': os.getenv("DB_ALKOSTO"),
            'user': os.getenv("USER_DB_ALKOSTO"),
            'password': os.getenv("PASSWORD_DB_ALKOSTO")
        }
        ic(params)
        

        # Establecer la conexión
        connecting_string = f"postgresql+psycopg2://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
        engine = create_engine(connecting_string)
        
        

    except exc.SQLAlchemyError as e:
        print(f"Error al conectarse a la base de datos: {params['database']}")
        print(e)
    else:
        print(f"Conexión exitosa a la base de datos: {params['database']}")
        return engine
    
    
def mover_archivo(origen: str, destino: str, nombre_archivo: str):
    '''
    Función para cortar y pegar archivos
    
    Parametros:
        * origen: path donde se encuentra alojado el archivo a mover
        * destino: path de destino del archivo a mover
        * nombre_archivo: nombre completo del archivo incluyendo su extención(xmls, pdf, etc)
        
    Retorno:
    '''
    try:
        ruta_origen = os.path.join(origen, nombre_archivo)
        nuevo_origen = os.replace(ruta_origen, destino)
        logger.info(f"Archvio{nombre_archivo} movido a: {nuevo_origen}")
        return nuevo_origen
    except Exception as e:
        logger.error(f"Error al mover el archivo {nombre_archivo} a {destino}: {e}")


def copiar_archivo(origen: str, destino: str, nombre_archivo: str):
    '''
    Función para copiar y pegar archivos
    
    Parametros:
        * origen: path donde se encuentra alojado el archivo a copiar
        * destino: path de destino del archivo a copiar
        * nombre_archivo: nombre completo del archivo incluyendo su extención(xmls, pdf, etc)
        
    Retorno:
    '''
    try:
        ruta_origen = os.path.join(origen, nombre_archivo)
        nuevo_origen = shutil.copy(ruta_origen, destino)
        logger.info(f"Archvio{nombre_archivo} copiado a: {nuevo_origen}")
        return nuevo_origen
    except Exception as e:
        logger.error(f"Error al copiar el archivo {nombre_archivo} a {destino}:{e}")

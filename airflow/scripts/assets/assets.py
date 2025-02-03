import datetime
import os
import pandas as pd
import time
import shutil
import logging
import psycopg2 as psy
import mysql.connector
import traceback
from icecream import ic
from sqlalchemy import create_engine, exc
from pythonjsonlogger.json import JsonFormatter


#========================================== Logs Config ==========================================
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers = [
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("assets")

#========================================================== Logic Developed ============================================================

def obtener_fechas():
    """
    Función para obtener la fecha del primer dia del mes y el dia actual
    
    Retorno: 
        * fecha_inicio(date): primer dia del mes actual
        * hoy(date): fecha del dia en que se ejecuta la funcion
    """
    hoy = datetime.date.today()
    fecha_inicio = hoy.replace(day=1)
    ic(hoy, fecha_inicio)
    # fecha_fin = hoy.replace(day=1) - datetime.timedelta(days=1) ## Fecha del ultimo dia del mes anterior
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
    logger.info(f"Waiting for download file...............")
    seconds = 0
    while seconds < timeout:
        files = os.listdir(directory)        
        for file in files:
            ic(file)
            if file == file_name:
                return True
        time.sleep(5)  
        seconds += 5
    return None


def conexion_db(params:dict, type:str='postgres'):
    ''' 
    Función para conectarse a bases de datos PostgreSQL o MySQL.
    
    Parametros:
        * ***params***(dict): 
                params {
                    'host':'host_value',
                    'port': 'port_value',
                    'user': 'user_value',
                    'database': 'database_value',
                    'password': 'password_value'
                    }
        * ***type***(str): string que define el tipo de base de datos ***'postgres'*** o ***'mysql'***, por defecto ***'postgres'***

    Retorno:
        * ***conexion***(objeto psycopg2) 
    '''
    try:
        if type == 'mysql':
            ic(params)
            conexion = mysql.connector.connect(
                user=(params["user"]),
                password=params["password"],
                host=params["host"],
                port=params["port"],
                database=params["database"],
            )              
            print(f"Conexión exitosa a la base de datos: {params['database']}")
        elif type == 'postgres':            
            ic(params)
            conexion = psy.connect(**params)
            logger.info(f"Conexión exitosa a la base de datos: {params['database']}")
        return conexion
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        full_traceback = traceback.format_exc()
        logger.error(f"Error al conectarse a la base de datos: {params['database']}:\n***Error type:*** {error_type}\n***Error message:*** {error_message}\n***Full Traceback:*** {full_traceback}")
        
        
        
        
  
def ejecutar_consulta(conexion, query: str, *args):
    '''
    Función que realiza consultas a una base de datos (PostgreSQL o MySQL).

    Parámetros:
        * conexion (any): Retorno de la función de conexión a la base de datos.
        * query (str): Consulta SQL.
        * args (any): Parámetros que se deben pasar a la consulta.

    Retorno: DataFrame de pandas.
    '''
    cursor = conexion.cursor()
    try:
        cursor.execute(query, args)
        
        # Obtener los nombres de las columnas
        columnas = [desc[0] for desc in cursor.description]
        
        # Obtener los datos y convertirlos en un DataFrame
        datos = cursor.fetchall()
        df = pd.DataFrame(data=datos, columns=columnas)
        
        # Confirmar la transacción (si es necesario)
        conexion.commit()
        logger.info("SQL query succesfully executed")
        return df
    except Exception as e:
        # Revertir la transacción en caso de error
        conexion.rollback() 
    finally:
        # Cerrar el cursor
        cursor.close()


def engine_to_sql(params:dict, type:str='postgres'):
    '''
    Función para crear motor de conexion para to_sql()
    
    Parametros:
        * ***params***(dict): diccionario {
                'host':'host_value',
                'port': 'port_value',
                'user': 'user_value',
                'database': 'database_value',
                'password': 'password_value'
                }
        * ***type***(str): string que define el tipo de base de datos ***'postgres'*** o ***'mysql'***, por defecto ***'postgres'***.
    
    Retorno:
        * ***engine***  
    '''
    try:        
        if type == 'mysql':
            connecting_string = f"mysql+mysqldb://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
            engine = create_engine(connecting_string)
        elif type == 'postgres':
            connecting_string = f"postgresql+psycopg2://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
            engine = create_engine(connecting_string)
        logger.info(f"Engine para base de datos: {params['database']} creado exitosamente")
        return engine
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        full_traceback = traceback.format_exc()
        logger.error(f"Error al crear engine para base de datos: {params['database']}:\n***Error type:*** {error_type}\n***Error message:*** {error_message}\n***Full Traceback:*** {full_traceback}")
        
    
    
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

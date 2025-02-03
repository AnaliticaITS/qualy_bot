import os
import pandas as pd
import numpy as np
import logging
import requests
from assets.titulos_bbva import titulos
from assets.assets import conexion_db, engine_to_sql, ejecutar_consulta, obtener_fechas
from icecream import ic

#========================================== Logs Config ==========================================
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers = [
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("etl_ex_bbva")

#============================================== Variables ============================================================
params = {
    'host': os.getenv("HOST_DB_BBVA"),
    'port': os.getenv("PORT_DB_BBVA"),
    'user': os.getenv("USER_DB_BBVA"),
    'database': os.getenv("DB_BBVA") ,
    'password': os.getenv("PASSWORD_DB_BBVA")
}
ic(params)
conn = conexion_db(params=params, type='mysql')
engine = engine_to_sql(params=params, type='mysql')
fecha_inicio, fecha_fin = obtener_fechas()
ic(fecha_inicio, fecha_fin)
download_dir = os.getenv("DOWNLOAD_DIR")
query = '''
SELECT * FROM calidad_etl.sm_cerrado
    WHERE "INSERTAR_DT" >= %s;
'''
ic(query)
schema = params['database']
ims_mes_actual = ejecutar_consulta(conn, query, fecha_inicio)
#================================================== Logica Desarrollada ==============================================

def validar_columnas(df_RC, df_BD):
    # df_BD = df_BD.drop(
    #     "id_fact_sm_cerrado", axis=1
    # )  # para no tener en cuenta la columna "id_fact_sm_cerrado" en la validación
    if len(df_RC.columns) == len(df_BD.columns):
        return "Columnas Iguales"
    else:
        # Encuentra las columnas no coincidentes
        no_coincidentes = list(set(df_RC.columns) ^ set(df_BD.columns))
        return no_coincidentes

def cruzar_casos(data, dataBD):
    # Cruzar Tablas
    data["check"] = data.ID_ATENCION_ONYX.isin(dataBD.ID_ATENCION_ONYX)
    data = data[data["check"] == False]
    data = data.drop("check", axis=1)
    data.reset_index(drop=True, inplace=True)
    return data

def main():
    try:
        logger.info("Start ETL Exito Tuya BBVA")
        #Cargar Excel
        try:
            df = pd.read_excel(f"{download_dir}/Reporte como_vamos.xlsx")
            logger.info("Reporte como_vamos.xlsx successfully load")
        except Exception as e:
            logger.error(f"Error reading Reporte como_vamos.xlsx: {e}")
            
        #Filtro clientes
        df=df[df["nombre_cliente"].isin(["ALMACENES EXITO S.A.","TUYA S.A","BBVA COLOMBIA","SODIMAC COLOMBIA S.A."])]

        #print(df.columns) = comando de pruba

        #Eliminar columnas
        Columnas_a_eliminar=[
            "nuevo_director", 
            "cumplimiento_reto", 
            "mes", 
            "proceso", 
            "direccion", 
            "servicio_ftt", 
            "anio",
            "numero_lls",
            "fecha_hora_cier_lls",
            "fecha_hora_calc",
            "resolucion_5",
            "tecnologia",
            "fecha_fin_olas" ,
            "conveniencia",
            "estacion_base_afectada",
            "equipo_afectado",
            "tiempo_ola",
            "cumplimiento_ola",
            "rango_sla_horas_calc",
            "clasif_n_sla_horas_calc",
            "rango_sla_dt_conciliado",
            "clasif_n_sla_dt_conciliado",
            "es_cli320",
            "intradia_fecha_creacion",
            "intradia_fecha_ingreso_estado"
        ]
        df.drop(columns=Columnas_a_eliminar,inplace = True)

        #Renombrar columnas
        df.rename(columns=titulos, inplace = True)        
        #print(df.columns) = comando de pruba

        #Crear columnas adicionales concatenadas

        df["ID_ENLACE"] = df["ID_ENLACE"].astype(str)
        df["llave reincidencia"] = df["ID_ENLACE"].str.cat([df["RESOLUCION_4"],df["Reclasificacion_atencion_Calc"]], sep = "/")
        df["llave recurrencia"] = df["ID_ENLACE"].str.cat(df["Reclasificacion_atencion_Calc"], sep = "/")

        #  Conteo de cuantas veces aparecen las llaves

        df["cantidad reincidencias"] = (df['llave reincidencia'].map(df['llave reincidencia'].value_counts())).fillna(0)
        df["cantidad recurrencias"] = (df["llave recurrencia"].map(df["llave recurrencia"].value_counts())).fillna(0)

        # Convertir la columna cantidad reincidencias y recurrencias a tipo de dato entero

        df["cantidad reincidencias"] =df["cantidad reincidencias"].astype(int)
        df["cantidad recurrencias"] =df["cantidad recurrencias"].astype(int)

        # Diligenciamiento de columna recurrencia y reincidencia con si o no con valores mayores a 2 de las columnas cantidad reincidencias y cantidad recurrencias

        df["Reincidencia_Calc"] = np.where((df["Reclasificacion_atencion_Calc"] == "Incidente") & (df["cantidad reincidencias"]>= 2),"SI", "NO")
        df["Recurrencia_Calc"] = np.where((df["Reclasificacion_atencion_Calc"] == "Incidente") & (df["cantidad recurrencias"]>= 2),"SI", "NO")

        #Creación de Columnas Reclasificación reincidencia calcuada

        df["Reclasificacion_Reinc_Calc"] = df["Reclasificacion_atencion_Calc"]

        #Eliminar columnas creadas 
        Columnas_a_eliminar=["llave reincidencia", "llave recurrencia", "cantidad reincidencias", "cantidad recurrencias"]
        df.drop(columns=Columnas_a_eliminar,inplace = True)
        
        #exportar resultado a excel
        df.to_excel(f"{download_dir}/Cerrados.xlsx", index = False)
       
        logger.info(f"etl_ex_bbva.py success execution")
        return
    except Exception as e:
        logger.error(f"Execution error etl_ex_bbva.py: {e}")        


if __name__=="__main__":
    main()
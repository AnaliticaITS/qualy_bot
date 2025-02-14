# Script original del proyecto alkosto, se encuentra en la ruta
# OneDrive - ITS InfoCom\ANALITICA ITS\POWER AUTOMATE\ALKOSTO-CDC\Python_ETL_Alkosto_CDC\SCRIPTS
import os
import pandas as pd
import numpy as np
import sys
import sqlalchemy
import re, requests
from datetime import datetime, timedelta
from icecream import ic

download_dir = os.getenv("DOWNLOAD_DIR")

# Configuración conexion Telegram
token = os.getenv("BOT_TOKEN")
id_Chat = os.getenv("ID_CHAT")
urlBase = (
    "https://api.telegram.org/bot"
    + token
    + "/sendMessage?chat_id="
    + id_Chat
    + "&text="
)
texto = ""

# Organizar Formatos De Fecha
fechaHoy = datetime.now()  # Obtener Fecha Actual
filtroFecha = fechaHoy - timedelta(days=(fechaHoy.day))
if filtroFecha.month <= 9:
    mes = "0" + str(filtroFecha.month)
else:
    mes = str(filtroFecha.month)
FechaFiltro = "'" + str(filtroFecha.year) + "-" + str(mes) + "-01'"

# Credenciales para ingresar a la BD -PostgreSQL-
user2 = os.getenv("USER_DB_ALKOSTO")
passwd2 = os.getenv("PASSWORD_DB_ALKOSTO")
server2 = os.getenv("HOST_DB_ALKOSTO")
port = os.getenv("PORT_DB_ALKOSTO")
db2 = os.getenv("DB_ALKOSTO")

# Parámetros De Conexion A -PostgreSQL-
connPG = "postgresql://" + user2 + ":" + passwd2 + "@" + server2 + ":" + port + "/" + db2
enginePG = sqlalchemy.create_engine(connPG)
Esquema = "tableros_mensuales"

consulta_usuarios = """
SELECT * FROM tableros_mensuales.usuarios_noc_alkosto
"""
consulta_IMs_BD = (
    """
SELECT * FROM tableros_mensuales.incidentes_eventos
WHERE fecha_cierre >= """
    + FechaFiltro
    + """
"""
)
consulta_RFs_BD = (
    """
SELECT id_caso, fecha_cierre FROM tableros_mensuales.requerimientos
WHERE fecha_cierre >= """
    + FechaFiltro
    + """
"""
)
consulta_Cs_BD = (
    """
SELECT id_caso, fecha_cierre FROM tableros_mensuales.cambios
WHERE fecha_cierre >= """
    + FechaFiltro
    + """
"""
)


def TransformacionColumnas(df):
    # Filtrar Por Cliente "Colombiana De Comercio"
    df = df[df["nombre_cliente"] == "COLOMBIANA DE COMERCIO S.A."]
    df.reset_index(drop=True, inplace=True)

    # Renombrar columnas
    df = df.rename(
        columns={
            "id_atencion_onyx": "id_caso",
            "atencion": "tipo_caso_sm",
            "prioridad_atencion": "prioridad_sm",
            "descripcion": "titulo",
            "resolucion_1": "categoria_tipo_caso",
            "resolucion_2": "subcategoria_falla",
            "resolucion_3": "area_problema_falla",
            "resolucion_4": "km_causa_falla",
            "usuario_insertado": "usuario_creacion",
            "grupo_insertado": "grupo_creacion",
            "familia": "codigo_cierre",
            "fecha_ingreso_estado": "fecha_cierre",
            "reclasificacion_atencion_calc": "tipo_caso_claro",
            "tiempo_horas_sla_calc": "tiempo_sla_calculado",
            "cumplimiento_calc": "cumplimiento_sla_claro",
            "nueva_prioridad_calc": "prioridad_claro",
            "dt_conciliado": "tiempo_interrupcion_dt_concil",
            "dt_ajustado": "tiempo_sla_dt_ajust",
            "eyn_ofensor": "ofensor",
            "eyn_problema": "problema",
            "eyn_causa": "causa",
        }
    )

    # Cambiar a formato a columnas
    df = df.astype(
        {
            "tiempo_interrupcion_dt_concil": "float",
            "tiempo_sla_dt_ajust": "float",
            "origen_atencion": "str",
        }
    )

    # Dar formato de fecha
    df["fecha_creacion"] = pd.to_datetime(
        df["fecha_creacion"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )
    df["fecha_solucion"] = pd.to_datetime(
        df["fecha_solucion"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )
    df["fecha_cierre"] = pd.to_datetime(
        df["fecha_cierre"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )
    df["inicio_interrupcion"] = pd.to_datetime(
        df["inicio_interrupcion"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )
    df["fin_interrupcion"] = pd.to_datetime(
        df["fin_interrupcion"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )
    df["fecha_cargue"] = pd.to_datetime(
        df["fecha_cargue"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )

    """
    df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'], format='%d/%m/%Y %I %p' , errors='coerce')
    df['fecha_solucion'] = pd.to_datetime(df['fecha_solucion'], format='%d/%m/%Y %I %p' , errors='coerce')
    df['fecha_cierre'] = pd.to_datetime(df['fecha_cierre'], format='%d/%m/%Y %I %p' , errors='coerce')
    reemplazos = {'AM': 'a. m.', 'PM': 'p. m.'} # Definir un diccionario de reemplazo
    df['inicio_interrupcion'] = df['inicio_interrupcion'].replace(reemplazos , regex=True)
    df['fin_interrupcion']= df['fin_interrupcion'].replace(reemplazos ,regex=True)
    df['inicio_interrupcion'] = pd.to_datetime(df['inicio_interrupcion'], format='mixed', errors='coerce')
    df['fin_interrupcion'] = pd.to_datetime(df['fin_interrupcion'], format='mixed' , errors='coerce')
    """
    columnas_eliminar = [
        "nit",
        "id_cliente_onyx",
        "resumen",
        "grupo_objetivo",
        "mayor_incident",
        "nit_sin_cod_calc",
        "sistema_calc",
        "consecutivo_calc",
        "meta_individual_calc",
        "meta_presidencia_calc",
        "meta_ifi_calc",
        "calc_3g",
        "tmx_minutos_calc",
        "tmx_calc",
        "reincidencia_calc",
        "recurrencia_calc",
        "llave_general_calc",
        "llave_reincidencia_calc",
        "reclasificacion_reinc_calc",
        "cluster_actual_calc",
        "celula_comercial_calc",
        "tipo_ticket",
        "contacto_destino",
        "tiempo_incidente",
        "rango_hora",
        "director",
        "nodo",
        "agrupacion_especiales",
        "nuevo_director",
        "mes",
        "proceso",
        "direccion",
        "servicio_ftt",
        "anio",
        "clasif_por_ivr_calc",
        "clasif_por_cliente_calc",
        "g_segmento",
        "g_clasif_por_ivr_calc",
        "palabra_clave",
        "clasif_por_servicio_calc",
        "alias_enlace",
        "tiposervicio",
        "numero_lls",
        "fecha_hora_cier_lls",
        "fecha_hora_calc",
        "resolucion_5",
        "tecnologia",
        "fecha_fin_olas",
        "conveniencia",
        "estacion_base_afectada",
        "equipo_afectado",
        "tiempo_ola",
        "cumplimiento_ola",
        'rango_sla_horas_calc',
        'clasif_n_sla_horas_calc',
        'rango_sla_dt_conciliado',
        'clasif_n_sla_dt_conciliado',
        'es_cli320',
        'intradia_fecha_creacion',
        'intradia_fecha_ingreso_estado'       
    ]

    # Eliminar columnas innecesarias
    df = df.drop(columnas_eliminar, axis=1)

    # Reemplazar valores de columnas
    df["origen_atencion"] = df["origen_atencion"].replace(
        [
            "1 - Usuario",
            "3 - Evento",
            "4 - Chat",
            "5 - Correo electrónico",
            "6 - Teléfono",
            "10",
        ],
        ["Usuario", "Evento", "Chat", "Correo Electrónico", "Teléfono", "Web"],
    )
    df["presenta_interrupcion_ci"] = np.where(
        df[["inicio_interrupcion", "fin_interrupcion"]].notnull().all(axis=1),
        "Si",
        "No",
    )
    df["autogestion"] = df["autogestion"].replace(["t", np.nan], ["Si", "No"])
    df["id_enlace"] = df["id_enlace"].replace(np.nan, "CI Genérico")
    df["subcategoria_falla"] = df["subcategoria_falla"].replace("failure", "Falla")
    df["duplicado"] = ""
    df["motivo_duplicado"] = ""
    print(df)
    return df


def reemplazar_espacios(texto):
    # Reemplazar espacios de no separación en una cadena
    espacios_no_separacion = re.compile(r"[\u00A0\u202F]")
    return espacios_no_separacion.sub(" ", texto)


def reemplazar_cod_usuarios(df):
    # Extraer Data Usuarios De BD
    c_SQL_POSTGRESQL = enginePG.connect()
    tabla_usuarios = pd.read_sql(consulta_usuarios, c_SQL_POSTGRESQL)
    c_SQL_POSTGRESQL.close()

    # Repisar tipo string a columnas a realizar el cambio de codigo por nombre_usuario
    columnas_convertir = [
        "usuario_creacion",
        "usuario_asignado",
        "usuario_solucion",
        "usuario_cerrado",
    ]
    df.loc[:, columnas_convertir] = df.loc[:, columnas_convertir].astype(str)

    for i in range(len(tabla_usuarios)):
        df["usuario_creacion"] = df["usuario_creacion"].replace(
            tabla_usuarios["usuario_red"].iloc[i],
            tabla_usuarios["nombre_completo"].iloc[i],
        )
        df["usuario_asignado"] = df["usuario_asignado"].replace(
            tabla_usuarios["usuario_red"].iloc[i],
            tabla_usuarios["nombre_completo"].iloc[i],
        )
        df["usuario_solucion"] = df["usuario_solucion"].replace(
            tabla_usuarios["usuario_red"].iloc[i],
            tabla_usuarios["nombre_completo"].iloc[i],
        )
        df["usuario_cerrado"] = df["usuario_cerrado"].replace(
            tabla_usuarios["usuario_red"].iloc[i],
            tabla_usuarios["nombre_completo"].iloc[i],
        )

    # Aplicar str.capitalize() a las columnas seleccionadas utilizando .apply
    df[columnas_convertir] = df[columnas_convertir].apply(lambda x: x.str.upper())
    # reemplazar espacios de no separación en una cadena
    df[columnas_convertir] = df[columnas_convertir].map(reemplazar_espacios)
    return df


def cruzar_casos(data, dataBD):
    # Cruzar Tablas
    data["check"] = data.id_caso.isin(dataBD.id_caso)
    data = data[data["check"] == False]
    data = data.drop("check", axis=1)
    data.reset_index(drop=True, inplace=True)
    return data


def validar_columnas(df_RC, df_BD):
    df_BD = df_BD.drop(
        "incrementador", axis=1
    )  # para no tener en cuenta la columna "incrementador" en la validación
    if len(df_RC.columns) == len(df_BD.columns):
        return "Columnas Iguales"
    else:
        # Encuentra las columnas no coincidentes
        no_coincidentes = list(set(df_RC.columns) ^ set(df_BD.columns))
        return no_coincidentes


# INICIO CODIGO
def main():
    try:
        # Lectura de tabla en excel
        try:
            data = pd.read_excel(
                f"{download_dir}/Reporte como_vamos.xlsx"
            )  # Ruta Escritorio
        except:
            data = pd.read_excel(
                "/temp/Reporte como_vamos.xlsx"
            )  # Ruta Servidor

        # Lectura de casos en BD
        c_SQL_POSTGRESQL = enginePG.connect()
        IMsMesEnCurso = pd.read_sql(consulta_IMs_BD, c_SQL_POSTGRESQL)
        RFsMesEnCurso = pd.read_sql(consulta_RFs_BD, c_SQL_POSTGRESQL)
        CsMesEnCurso = pd.read_sql(consulta_Cs_BD, c_SQL_POSTGRESQL)
        c_SQL_POSTGRESQL.close()
        print(IMsMesEnCurso)

        # Procesamiento De La Data
        dataTransformada = TransformacionColumnas(data)
        dataTransformada = reemplazar_cod_usuarios(dataTransformada)

        retorno = validar_columnas(dataTransformada, IMsMesEnCurso)
        if retorno == "Columnas Iguales":
            # Segmentación De Tablas Por Tipo De Caso
            data_incidentes_eventos = dataTransformada[
                dataTransformada["tipo_caso_claro"].isin(["Evento", "Incidente"])
            ].copy()
            data_requerimientos = dataTransformada[
                dataTransformada["tipo_caso_claro"] == "Requerimiento"
            ].copy()
            data_cambios = dataTransformada[
                dataTransformada["tipo_caso_claro"] == "Cambios"
            ].copy()

            # Cruce de casos (Extracción de Casos Mes actual y Mes Anterior)
            data_incidentes_eventos = cruzar_casos(data_incidentes_eventos, IMsMesEnCurso)
            data_requerimientos = cruzar_casos(data_requerimientos, RFsMesEnCurso)
            data_cambios = cruzar_casos(data_cambios, CsMesEnCurso)
            texto = ""

            # CARGAR DATAS A BD
            c_SQL_POSTGRESQL = enginePG.connect()
            print(len(data_incidentes_eventos), len(data_requerimientos), len(data_cambios))
            if len(data_incidentes_eventos):
                data_incidentes_eventos.to_sql(
                    "incidentes_eventos",
                    c_SQL_POSTGRESQL,
                    if_exists="append",
                    index=False,
                    schema=Esquema,
                )
                texto += "\nIncidentes Cargados: " + str(len(data_incidentes_eventos))
                print("Incidentes Cargados: ", len(data_incidentes_eventos))
            if len(data_requerimientos):
                data_requerimientos.to_sql(
                    "requerimientos",
                    c_SQL_POSTGRESQL,
                    if_exists="append",
                    index=False,
                    schema=Esquema,
                )
                print("Requerimientos Cargados: ", len(data_requerimientos))
                texto += "\nRequerimientos Cargados: " + str(len(data_requerimientos))
            if len(data_cambios):
                data_cambios.to_sql(
                    "cambios",
                    c_SQL_POSTGRESQL,
                    if_exists="append",
                    index=False,
                    schema=Esquema,
                )
                print("Cambios Cargados: ", len(data_cambios))
                texto += "\nCambios Cargados: " + str(len(data_requerimientos))

            c_SQL_POSTGRESQL.close()

            if (len(data_incidentes_eventos) or len(data_requerimientos)) or len(data_cambios):
                textofinal = "\n\nDatos Cargados A BD" + texto
            else:
                textofinal = "\n\nNo se ha cargado ningun registro a la Base De Datos"

            mensaje = (
                "ETL ALKOSTO CDC\n\n"
                + "✅"
                + "Ejecución Exitosa"
                + "✅"
                + textofinal
                + "\n\nMensaje Generado De Forma Automática Desde Analítica ITS"
            )
            requests.get(urlBase + mensaje)
            print("Ejecucion Exitosa")

        else:
            textofinal = (
                "\n\nSe han agregado nuevas columnas al excel exportado de Reporting Center: "
                + str(retorno)
            )
            mensaje = (
                "ETL ALKOSTO CDC\n\n"
                + "❌"
                + "Ejecución Errónea"
                + "❌"
                + textofinal
                + "\n\nMensaje Generado De Forma Automática Desde Analítica ITS"
            )
            requests.get(urlBase + mensaje)
            print("Ejecucion Erronea")

    except Exception as e:
        textofinal = (
            "\n\nCodigo de error: " + type(e).__name__ + "\nMensaje Error: " + str(e)
        )
        mensaje = (
            "ETL ALKOSTO CDC\n\n"
            + "🚨"
            + "Ejecución Errónea"
            + "🚨"
            + textofinal
            + "\n\nMensaje Generado De Forma Automática Desde Analítica ITS"
        )
        requests.get(urlBase + mensaje)
        print("Ejecucion Erronea")


if __name__=="__main__":
    main()
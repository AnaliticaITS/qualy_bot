import os
import subprocess
import logging
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
from icecream import ic

#========================================== Logs Config ==========================================
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers = [
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DAG_como_vamos")


#========================================================== Logic Developed ============================================================

def clear_files():
    try:
        os.remove("/opt/airflow/downloads/Reporte como_vamos.xlsx")
        os.remove("/opt/airflow/downloads/Cerrados.xlsx")
        return
    except Exception as e:
        logger.error(f"Error cleaning files: {e}")    
    

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'start_date':pendulum.datetime(2025, 2, 5, tz="America/Bogota"),  # Usa Bogotá como zona horaria,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    
}

with DAG(
    dag_id = 'etl_reporte_como_vamos',
    default_args = default_args,
    description = 'DAG that executes the python ETL to download Reporte como_vamos.xlsx',
    schedule_interval = '30 6 * * *',
    catchup = False, # Indispensable False si se usa 'start_date: days_ago(1)'
) as dag:
    
    # Task 1
    task_bot_como_vamos = BashOperator(
        task_id = "task_bot_como_vamos",
        bash_command = "python /opt/airflow/scripts/bot_reporte_como_vamos.py"
    )
    
    # # Task 2
    etl_cdc = BashOperator(
        task_id = "etl_cdc",
        bash_command = "python /opt/airflow/scripts/etl_cdc.py"
    )
    
    # Task 3
    etl_ex_bbva = BashOperator(
        task_id = "etl_ex_bbva",
        bash_command = "python /opt/airflow/scripts/etl_ex_bbva.py"
    )
    
    # Task 4
    bot_ex_bbva = BashOperator(
        task_id = 'bot_ex_bbva',
        bash_command = "python /opt/airflow/scripts/bot_etl_ex_bbva.py"
    )
    
    # Task 5
    remove_files = PythonOperator(
        task_id = "clean_files",
        python_callable=clear_files
    )
    
    task_bot_como_vamos >> [etl_cdc, etl_ex_bbva] >> bot_ex_bbva >> remove_files
    # etl_ex_bbva >> bot_ex_bbva >> remove_files
    # bot_ex_bbva
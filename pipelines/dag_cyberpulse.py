# CyberPulse -- DAG Airflow
# Pipeline : acquisition -> cleaning -> load_to_db -> dbt run
# Frequence : toutes les heures

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys

sys.path.insert(0, '/opt/airflow/src')
sys.path.insert(0, '/opt/airflow/db')

from acquisition import main as run_acquisition
from cleaning import main as run_cleaning
from load_to_db import main as run_load

with DAG(
    dag_id="cyberpulse_daily_pipeline",
    description="Collecte, nettoyage, chargement PostgreSQL et transformation dbt",
    start_date=datetime(2026, 3, 24),
    schedule_interval="0 * * * *",
    catchup=False,
    tags=["cyberpulse", "etl"],
    default_args={
        "owner": "cyberpulse",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
) as dag:

    t1 = PythonOperator(
        task_id="acquisition",
        python_callable=run_acquisition,
    )

    t2 = PythonOperator(
        task_id="cleaning",
        python_callable=run_cleaning,
    )

    t3 = PythonOperator(
        task_id="load_to_db",
        python_callable=run_load,
    )

    # --profiles-dir explicite pour eviter l'erreur "Could not find profile"
    t4 = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt && dbt run --profiles-dir .",
    )

    t1 >> t2 >> t3 >> t4
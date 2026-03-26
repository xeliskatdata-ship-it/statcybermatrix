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
    start_date=datetime(2026, 3, 24),
    schedule_interval="0 * * * *",   # toutes les heures
    catchup=False,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5)
    }
) as dag:

    t1 = PythonOperator(
        task_id="acquisition",
        python_callable=run_acquisition
    )

    t2 = PythonOperator(
        task_id="cleaning",
        python_callable=run_cleaning
    )

    t3 = PythonOperator(
        task_id="load_to_db",
        python_callable=run_load
    )

    t4 = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt && dbt run"
    )

    t1 >> t2 >> t3 >> t4
import pytest
import sys
import os
from airflow.models import DagBag, Variable
from airflow.utils.dag_cycle_tester import check_cycle
from unittest.mock import patch


airflow_variables = {
    'key': 'value',  # 예시 변수
}


@pytest.fixture(scope="session", autouse=True)
def set_airflow_test_environment():
    # AIRFLOW_HOME 경로를 현재 작업 디렉토리로 가정합니다.
    airflow_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    plugins_dir = os.path.join(airflow_home, 'airflow', 'plugins')

    # Python 모듈 검색 경로에 `plugins` 디렉토리 추가
    if plugins_dir not in sys.path:
        sys.path.insert(0, plugins_dir)


@pytest.fixture(scope="session")
def dag_bag():
    return DagBag(dag_folder='airflow/dags/', include_examples=False)


def test_dag_loaded(dag_bag):
    assert len(dag_bag.import_errors) == 0, "DAGs loading errors: {}".format(dag_bag.import_errors)


def test_dag_integrity(dag_bag):
    # Airflow variables mock patch
    with patch.object(Variable, "get", side_effect=lambda key: airflow_variables.get(key)):
        for dag_id, dag in dag_bag.dags.items():
            check_cycle(dag)  # 순환 종속성 검사
            assert dag.default_args is not None, f"DAG {dag_id}의 default_args가 설정되지 않았습니다."
            for task in dag.tasks:
                assert task.owner is not None, f"DAG {dag_id}의 Task {task.task_id}에 owner가 설정되지 않았습니다."

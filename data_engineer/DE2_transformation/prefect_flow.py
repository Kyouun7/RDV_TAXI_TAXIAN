"""
DE2 - Prefect Pipeline: Transformation Flow
Runs: cleaning -> feature engineering -> data blending in order.
Run: python prefect_flow.py
"""

from prefect import flow, task
from cleaning import clean_tlc
from feature_engineering import transform_tlc
from data_blending import blend_data


@task(name="clean-tlc", retries=1)
def task_clean():
    clean_tlc()


@task(name="feature-engineering", retries=1)
def task_transform():
    transform_tlc()


@task(name="blend-weather")
def task_blend():
    blend_data()


@flow(name="transformation-pipeline", log_prints=True)
def transformation_pipeline():
    clean = task_clean()
    transform = task_transform(wait_for=[clean])
    task_blend(wait_for=[transform])


if __name__ == "__main__":
    transformation_pipeline()

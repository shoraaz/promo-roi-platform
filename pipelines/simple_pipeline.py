"""Minimal KFP pipeline — back to simple parameter passing."""

from kfp import dsl
from kfp import compiler


@dsl.component(base_image="python:3.12-slim")
def say_hello(name: str) -> str:
    message = f"Hello, {name}!"
    print(message)
    return message


@dsl.component(base_image="python:3.12-slim")
def shout(message: str) -> str:
    shouted = message.upper() + "!!!"
    print(shouted)
    return shouted


@dsl.pipeline(name="promo-roi-hello-pipeline-v3")
def hello_pipeline(name: str = "Ram"):
    hello_task = say_hello(name=name)
    shout_task = shout(message=hello_task.output)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=hello_pipeline,
        package_path="pipelines/hello_pipeline_v3.yaml",
    )
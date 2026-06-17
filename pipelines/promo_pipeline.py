"""Real pipeline: load features -> train -> evaluate -> save artifacts."""

from kfp import dsl, compiler
from kfp.dsl import Output, Input, Dataset, Model, Metrics

TRAINING_IMAGE = "us-central1-docker.pkg.dev/promo-roi-platform-2026/ml-repo/promo-training:v8"


@dsl.component(base_image=TRAINING_IMAGE)
def load_features_component(output_data: Output[Dataset]):
    """Load and prepare features from BigQuery."""
    from train import load_features, encode_categoricals

    df = load_features()
    df = encode_categoricals(df)
    df.to_parquet(output_data.path)
    print(f"Loaded {len(df)} rows, saved to {output_data.path}")


@dsl.component(base_image=TRAINING_IMAGE)
def train_component(
    input_data: Input[Dataset],
    sales_lift_model: Output[Model],
    margin_impact_model: Output[Model],
):
    """Train both XGBoost models."""
    import pandas as pd
    import pickle
    from train import split_data, get_features_and_targets, train_models

    df = pd.read_parquet(input_data.path)
    train_df, val_df = split_data(df)
    X_train, y_train = get_features_and_targets(train_df)

    models = train_models(X_train, y_train)

    with open(sales_lift_model.path, "wb") as f:
        pickle.dump(models["sales_lift_pct"], f)
    with open(margin_impact_model.path, "wb") as f:
        pickle.dump(models["margin_impact"], f)

    print("Both models trained and saved.")


@dsl.component(base_image=TRAINING_IMAGE)
def evaluate_component(
    input_data: Input[Dataset],
    sales_lift_model: Input[Model],
    margin_impact_model: Input[Model],
    metrics: Output[Metrics],
):
    """Evaluate both models on the validation set."""
    import pandas as pd
    import pickle
    from train import split_data, get_features_and_targets, evaluate_models

    df = pd.read_parquet(input_data.path)
    _, val_df = split_data(df)
    X_val, y_val = get_features_and_targets(val_df)

    with open(sales_lift_model.path, "rb") as f:
        model_lift = pickle.load(f)
    with open(margin_impact_model.path, "rb") as f:
        model_margin = pickle.load(f)

    results = evaluate_models(
        {"sales_lift_pct": model_lift, "margin_impact": model_margin}, X_val, y_val
    )

    for target, target_metrics in results.items():
        for metric_name, value in target_metrics.items():
            metrics.log_metric(f"{target}_{metric_name}", value)
            print(f"{target}_{metric_name}: {value:.4f}")


@dsl.pipeline(name="promo-roi-training-pipeline")
def promo_pipeline():
    load_task = load_features_component()

    train_task = train_component(input_data=load_task.outputs["output_data"])

    evaluate_task = evaluate_component(
        input_data=load_task.outputs["output_data"],
        sales_lift_model=train_task.outputs["sales_lift_model"],
        margin_impact_model=train_task.outputs["margin_impact_model"],
    )


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=promo_pipeline,
        package_path="pipelines/promo_pipeline.yaml",
    )
    print("Compiled to pipelines/promo_pipeline.yaml")
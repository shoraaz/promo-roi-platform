# Docker Concepts

This file will explain containerization for the training and serving workloads.

## Key ideas to cover

- Image vs. container
- Layers and cache efficiency
- Dockerfile best practices
- Local testing with docker run

## What we built here

The starter Dockerfiles for `training/` and `serving/` are now in place. They follow the standard pattern of installing dependencies, copying the app code, and defining the runtime command.

## Why this structure is used

This design keeps the training and serving environments isolated, which is important for reproducibility and easier future deployment to Artifact Registry and GKE.

## Command to run later

# Build the training image locally
`docker build -t promo-training:local ./training/`

# Build the serving image locally
`docker build -t promo-serving:local ./serving/`

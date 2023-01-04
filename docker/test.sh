#! /usr/bin/env bash

# This script allows to start the backend with all services
docker compose --profile all --env-file .env.local up -d  --build 


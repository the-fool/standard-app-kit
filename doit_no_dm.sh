#!/bin/bash

# load variables
. ./app.config

echo $ORG
echo $NAME
echo $OWNER
echo $USE_NETWORK_PROJECT

DEV="$NAME"-DEV
PRD="$NAME"-PRD

gcloud resource-manager folders create --display-name="$NAME" --organization="$ORG"

ROOT_ID=$(gcloud resource-manager folders list --organization="$ORG" --filter="DISPLAY_NAME = $NAME" --format="value(ID)")

echo $ROOT_ID

gcloud resource-manager folders create --display-name="$DEV" --organization="$ORG"
gcloud resource-manager folders create --display-name="$PRD" --organization="$ORG"

DEV_ID=$(gcloud resource-manager folders list --folder="$ROOT_ID" --filter="DISPLAY_NAME = $DEV" --format="value(ID)")
PRD_ID=$(gcloud resource-manager folders list --folder="$ROOT_ID" --filter="DISPLAY_NAME = $PRD" --format="value(ID)")

echo "dev folder: $DEV_ID"
echo "prd folder: $PRD_ID"

#!/bin/bash

# load variables
. ./app.config

echo $ORG
echo $NAME
echo $OWNER
echo $USE_NETWORK_PROJECT

cd dm

cp folder_config.tpl.yaml folder_config.yaml
cp project_config.tpl.yaml project_config.yaml

sed "s/__NAME__/$NAME/g" folder_config.yaml
sed "s/__OWNER__/$OWNER/g" folder_config.yaml
sed "s/__ORG__/$ORG/g" folder_config.yaml

gcloud deployment-manager deployments create "$NAME-folders" --config project_config.yaml

ROOT_ID=$(gcloud resource-manager folders list --organization="$ORG" --filter="DISPLAY_NAME = $NAME" --format="value(ID)")

echo "ROOT_ID: $ROOT_ID"

DEV="$NAME"-DEV
PRD="$NAME"-PRD

DEV_ID=$(gcloud resource-manager folders list --folder="$ROOT_ID" --filter="DISPLAY_NAME = $DEV" --format="value(ID)")
PRD_ID=$(gcloud resource-manager folders list --folder="$ROOT_ID" --filter="DISPLAY_NAME = $PRD" --format="value(ID)")

echo "DEV_ID: $DEV_ID"
echo "PRD_ID: $PRD_ID"

sed "s/__NAME__/$NAME/g" project_config.yaml
sed "s/__ROOT_ID__/$ROOT_ID/g" project_config.yaml
sed "s/__DEV_ID__/$DEV_ID/g" project_config.yaml
sed "s/__PRD_ID__/$PRD_ID/g" project_config.yaml
sed "s/__OWNER__/$OWNER/g" project_config.yaml
sed "s/__USE_NETWORK_PROJECT__/$USE_NETWORK_PROJECT/g" project_config.yaml

gcloud deployment-manager deployments create "$NAME-projects" --config project_config.yaml


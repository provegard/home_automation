#!/bin/bash
set -e

usage="$0 <scene ID>"

source ~/.hass_api

scene_id=${1:?$usage}

curl --fail --silent -o /dev/null -X POST \
    -H "Authorization: Bearer $HASS_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"entity_id\": \"scene.$scene_id\"}" \
    http://$HASS_HOST:$HASS_PORT/api/services/scene/turn_on

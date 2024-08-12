#!/bin/bash
set -e

usage="$0 <light ID>"

source ~/.hass_api

light_id=${1:?$usage}

curl --fail --silent -o /dev/null -X POST \
    -H "Authorization: Bearer $HASS_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"entity_id\": \"light.$light_id\"}" \
    http://$HASS_HOST:$HASS_PORT/api/services/light/turn_off

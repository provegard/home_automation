#!/bin/bash
set -e

area=SE4

get_hour_price() {
    local add_hours=$1
    local y=$(date -d "+$add_hours hour" +%Y)
    local m=$(date -d "+$add_hours hour" +%m)
    local d=$(date -d "+$add_hours hour" +%d)
    local h=$(date -d "+$add_hours hour" +%H)

    # TODO: Remove old cache files

    local cache_file="/tmp/spot-prices-${y}${m}${d}.json"
    if [[ ! -f $cache_file ]]; then
        # https://www.elprisetjustnu.se/api/v1/prices/2024/07-01_SE4.json
        url="https://www.elprisetjustnu.se/api/v1/prices/${y}/${m}-${d}_${area}.json"
        curl -s -o $cache_file $url
    fi

    # Get average for the day
    #local avg=$(jq '[.[] | .SEK_per_kWh] | add / length' $cache_file)
    # Get max price for the day
    local max=$(jq 'map(.SEK_per_kWh) | max' $cache_file)

    # Get hour price, including VAT
    local hour_price=$(jq ".[$h] | .SEK_per_kWh * 1.25" $cache_file)

    # Calculate fraction of max
    #local frac=$(echo "scale=2; $hour_price / $max" | bc)

    echo $hour_price
}

price_to_color() {
    local value=$1
    local color=""

    if (( $(echo "$value <= 0.4" | bc -l) )); then
        color="green"
    elif (( $(echo "$value <= 0.75" | bc -l) )); then
        color="yellow"
    elif (( $(echo "$value <= 1" | bc -l) )); then
        color="orange"
    else
        color="red"
    fi

    echo $color
}

lamp_1_col=$(price_to_color $(get_hour_price 0))
lamp_2_col=$(price_to_color $(get_hour_price 1))
lamp_3_col=$(price_to_color $(get_hour_price 2))

#echo "L1: $lamp_1_col"
#echo "L2: $lamp_2_col"
#echo "L3: $lamp_3_col"

mydir=$(dirname $0)

$mydir/hass_activate_scene.sh "lampa_1_$lamp_1_col"
$mydir/hass_activate_scene.sh "lampa_2_$lamp_2_col"
./hass_activate_scene.sh "lampa_3_$lamp_3_col"

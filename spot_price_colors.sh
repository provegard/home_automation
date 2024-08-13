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

mydir=$(dirname $0)

lights="
ikea_of_sweden_tradfri_bulb_e27_cws_globe_806lm_light
ikea_of_sweden_tradfri_bulb_e27_cws_globe_806lm_light_2
ikea_of_sweden_tradfri_bulb_e27_cws_globe_806lm_light_3
"

hour=$(date +%H)
off_hour=23
on_hour=6
if [ "$hour" -ge "$off_hour" ] || [ "$hour" -lt "$on_hour" ]; then
    echo "Lights off at hour $hour"
    for light in $lights; do
        $mydir/hass_light_off.sh $light
    done
    exit
fi

colors=(
"$(price_to_color $(get_hour_price 0))"
"$(price_to_color $(get_hour_price 1))"
"$(price_to_color $(get_hour_price 2))"
)
col_length=${#colors[@]}
#echo "L1: $lamp_1_col; L2: $lamp_2_col; L3: $lamp_3_col"
echo "Colors: ${colors[@]}"

for (( i=0; i<$col_length; i++ )); do
    let n=i+1
    scene="lampa_${n}_${colors[$i]}"
    $mydir/hass_activate_scene.sh "$scene"
done

#$mydir/hass_activate_scene.sh "lampa_1_$lamp_1_col"
#$mydir/hass_activate_scene.sh "lampa_2_$lamp_2_col"
#$mydir/hass_activate_scene.sh "lampa_3_$lamp_3_col"


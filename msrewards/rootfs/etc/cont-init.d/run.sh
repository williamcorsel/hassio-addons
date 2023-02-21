#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

# Define home
HOME="/config/addons_config/msrewards"
mkdir -p $HOME
chmod -R 777 $HOME


if [ ! -f "$HOME"/accounts.json ]; then
    # Copy default config.json
    cp /templates/accounts.json "$HOME"/accounts.json
    chmod 777 "$HOME"/accounts.json
    bashio::log.warning "A default config.json file was copied in $HOME. Please customize according to https://github.com/farshadz1997/Microsoft-Rewards-bot and restart the add-on"
    sleep 5
    bashio::exit.nok
else
    bashio::log.warning "The config.json file found in $HOME will be used. Please customize according to https://github.com/farshadz1997/Microsoft-Rewards-bot and restart the add-on"
fi

start_at=$(bashio::config 'start_at')
everyday=$(bashio::config 'everyday')
session=$(bashio::config 'session')
fast=$(bashio::config 'fast')
error=$(bashio::config 'error')
shutdown=$(bashio::config 'shutdown')

args=("--headless" "--accounts" "${HOME}/accounts.json" "--start-at" "${start_at}")
[[ -n ${everyday} ]] && args+=("--everyday")
[[ -n ${session} ]] && args+=("--session")
[[ -n ${fast} ]] && args+=("--fast")
[[ -n ${error} ]] && args+=("--error")
[[ -n ${shutdown} ]] && args+=("--shutdown")

bashio::log.info "Starting..."

python /ms_rewards_farmer.py "${args[@]}"
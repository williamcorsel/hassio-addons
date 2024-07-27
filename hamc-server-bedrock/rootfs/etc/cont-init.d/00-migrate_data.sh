#!/usr/bin/env bashio
# shellcheck shell=bash

if [ -d /addons/hamc-server-bedrock/data ]; then
  if [ -z "$(ls -A /config)" ]; then
    bashio::log.info "Migrating minecraft data from /addons to /addon_configs"
    mv /addons/hamc-server-bedrock/data/* /config
  else
    bashio::log.warning "HAMC config files are present at both /addons/hamc-server-bedrock/data/ and /addon_configs/"
    bashio::log.warning "Manual migration of minecraft data to /addon_configs/ may be required"
  fi
fi
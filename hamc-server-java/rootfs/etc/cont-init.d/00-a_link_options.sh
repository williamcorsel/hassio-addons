#!/usr/bin/env bashio

# Link existing /hassio_data/options.json to /data/options.json to ensure configuration options are picked up
if [ ! -L /data/options.json ]; then
    ln -s /hassio_data/options.json /data/options.json
fi 

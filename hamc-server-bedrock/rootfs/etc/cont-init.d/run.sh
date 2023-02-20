#!/usr/bin/env bashio

bashio::log.info "Setting envs"

export EULA=TRUE
export SERVER_NAME=$(bashio::config 'server_name')
export GAMEMODE=$(bashio::config 'gamemode')
export DIFFICULTY=$(bashio::config 'difficulty')
export LEVEL_TYPE=$(bashio::config 'level_type')
export ALLOW_CHEATS=$(bashio::config 'allow_cheats')
export MAX_PLAYERS=$(bashio::config 'max_players')
export ONLINE_MODE=$(bashio::config 'online_mode')
export ALLOW_LIST=$(bashio::config 'allow_list')
export VIEW_DISTANCE=$(bashio::config 'view_distance')
export TICK_DISTANCE=$(bashio::config 'tick_distance')
export PLAYER_IDLE_TIMEOUT=$(bashio::config 'player_idle_timeout')
export MAX_THREADS=$(bashio::config 'max_threads')
export LEVEL_NAME=$(bashio::config 'level_name')
export LEVEL_SEED=$(bashio::config 'level_seed')
export DEFAULT_PLAYER_PERMISSION_LEVEL=$(bashio::config 'default_player_permission')
export TEXTUREPACK_REQUIRED=$(bashio::config 'texturepack_required')
export SERVER_AUTHORITATIVE_MOVEMENT=$(bashio::config 'server_authoritative_movement')
export PLAYER_MOVEMENT_SCORE_THRESHOLD=$(bashio::config 'player_movement_score_threshold')
export PLAYER_MOVEMENT_DISTANCE_THRESHOLD=$(bashio::config 'player_movement_distance_threshold')
export PLAYER_MOVEMENT_DURATION_THRESHOLD_IN_MILLISECONDS=$(bashio::config 'player_movement_duration_threshold_ms')
export CORRECT_PLAYER_MOVEMENT=$(bashio::config 'correct_player_movement')
export ALLOW_LIST_USERS=$(bashio::config 'allow_list_users')

bashio::log.info "Starting..."

/opt/bedrock-entry.sh

## 1.2.1

- Fix some config names by @felixstorm
- Fix send-command by @felixstorm

## 1.2.0

- Fixed native home assistant backups
- BREAKING CHANGE: Server data now stored at `/addon_configs/<slug>_hamc-bedrock`. The addon will attempt to migrate your data to the new location, but it is recommended to backup your `/addons/hamc-server-bedrock/data` folder before updating.

## 1.1.0

- Fixed HAOS option loading

## 1.0.3

- Fixed `SERVER_AUTHORITATIVE_MOVEMENT` option

## 1.0.2

- Add `ENABLE_LAN_VISIBILITY` option

## 1.0.1

- Set options to ENV variables automatically
- Change add-on name

## 1.0.0

- Initial release

## 1.3.0

- Fix players not being able to connect to Bedrock server 1.26.50 and later. These versions use a new connection method (NetherNet) that needs TCP port 19132 and extra UDP ports. The add-on now uses the host network, so the server can open these ports itself.
- Add optional `SERVER_UDP_PORTS` option to set the UDP ports used for gameplay. Use it when players connect from outside your network.
- Add `SERVER_PORT` option to set the port the server uses on your Home Assistant host (default 19132).
- BREAKING CHANGE: The port in the add-on network settings is no longer used. If you changed it, set `SERVER_PORT` to that port instead.
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

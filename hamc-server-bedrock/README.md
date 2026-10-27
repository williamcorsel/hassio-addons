# HAMC Server (Bedrock)

This add-on allows for hosting a Minecraft Bedrock server using Home Assistant. Based on the Minecraft server docker by [itzg](https://github.com/itzg/docker-minecraft-bedrock-server).

## Configuration

All configuration is done using the add-on options. It allows for setting the environment variables found [here](https://github.com/itzg/docker-minecraft-bedrock-server#environment-variables). For more info about these values, also check [here](https://minecraft.fandom.com/wiki/Server.properties#Bedrock_Edition_3).

The add-on uses the host network. Players on your local network can connect to `<home_assistant_ip>:19132`, or find the server in the LAN games list. To use a different port, set `SERVER_PORT`.

To access the Minecraft server from outside your network:

1. Set `SERVER_UDP_PORTS` to `<your_public_ip>:19140-19155:19140-19155`. Players connect to this public address and these UDP ports for gameplay.
2. On your router, forward port 19132 (TCP) and ports 19140-19155 (UDP) to your Home Assistant host.
3. Connect using:

```
<your_public_ip>:19132
```

Server data is stored in the `/addon_configs/<slug>_hamc-bedrock` folder for easy backups & adjustments.

## References

- Thanks to [alexbelgium](https://github.com/alexbelgium/hassio-addons) for the add-on template.
- Thanks to [itzg](https://github.com/itzg/docker-minecraft-bedrock-server) for the docker image.

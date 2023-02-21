# HAMC Server (Bedrock)

This add-on allows for hosting a Minecraft Bedrock server using Home Assistant. Based on the Minecraft server docker by [itzg](https://github.com/itzg/docker-minecraft-bedrock-server).

## Configuration

All configuration is done using the add-on options. It allows for setting the environment variables found [here](https://github.com/itzg/docker-minecraft-bedrock-server#environment-variables). For more info about these values, also check [here](https://minecraft.fandom.com/wiki/Server.properties#Bedrock_Edition_3).

To access the Minecraft server from outside your network, forward port 19132 (UDP) on your router. Then connect using:

```
<your_ip>:19132
```

Server data is stored in the `/addons/hamc-server-bedrock/data` folder for easy backups & adjustments.

## References

* Thanks to [alexbelgium](https://github.com/alexbelgium/hassio-addons) for the add-on template.
* Thanks to [itzg](https://github.com/itzg/docker-minecraft-bedrock-server) for the docker image.
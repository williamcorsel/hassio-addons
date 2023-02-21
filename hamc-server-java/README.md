# HAMC Server (Java)

This add-on allows for hosting a Minecraft Java server using Home Assistant. Based on the Minecraft server docker by [itzg](https://github.com/itzg/docker-minecraft-server).

## Configuration

All configuration is done using the add-on options. It allows for setting the environment variables found [here](https://github.com/itzg/docker-minecraft-server).

To access the Minecraft server from outside your network, forward port 25565 (TCP) on your router. Then connect using:

```
<your_ip>:25565
```

## References

* Thanks to [alexbelgium](https://github.com/alexbelgium/hassio-addons) for the add-on template.
* Thanks to [itzg](https://github.com/itzg/docker-minecraft-server) for the docker image.
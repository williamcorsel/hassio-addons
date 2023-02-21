# Microsoft Rewards Bot

This add-on allows for running a bot that collects Microsoft reward points for your account. It is based on the script by [farshadz1997](https://github.com/farshadz1997/Microsoft-Rewards-bot).

<h2 align="center">⚠️CAUTION!⚠️</h2>
<p align="center">
  <h4 align="center">Do not use an important account for this add-on, it can cause your account to be suspended from Microsoft Rewards.</h4>

## Configuration

Use the add-on configuration options to enable script features described [here](https://github.com/farshadz1997/Microsoft-Rewards-bot).

The account information should be stored in a `accounts.json` file in the `/config/addons_config/msrewards` directory. A template file is provided here in the case the add-on is started without configuring this file. The file should be in the following format:

```
[
    {
        "username": "Your Email",
        "password": "Your Password",
    },
]
```

## References

- Thanks to [alexbelgium](https://github.com/alexbelgium/hassio-addons) for the add-on template.
- Thanks to [farshadz1997](https://github.com/farshadz1997/Microsoft-Rewards-bot) for the original script.

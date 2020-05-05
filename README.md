# @averissimo fork

> reports Pi-Hole stats via telegraf

I adapted the code to run single query instead of daemon

The idea is for it to be compatbile with telegraf. This deviated from the original code because I couldn't find a simple way of having this janw/pihole container connecting to Pi-Hole container.

```
[[inputs.exec]]
  commands = ["/usr/bin/python3 /home/pi/monitor/pi-hole-agent/telegraf.py"]
  tags = ['tags_host']
  json_name_key = "measurement"
  json_string_fields = ["fields"]
  data_format = "json"
```

## How to setup in my own raspberry pi?

```
sudo pip install -r requirements.txt
```


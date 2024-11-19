#!/bin/bash

# Pega o IP passado como argumento
IP=$1

# Primeiro comando
curl -v --digest --user admin:Tudo@2020 "http://$IP/cgi-bin/configManager.cgi?action=setConfig&AlarmOut[0].Mode=1&AlarmOut[0].Name=port0"

# Esperar 1 segundo
sleep 1

# Segundo comando
curl -v --digest --user admin:Tudo@2020 "http://$IP/cgi-bin/configManager.cgi?action=setConfig&AlarmOut[0].Mode=2&AlarmOut[0].Name=port0"

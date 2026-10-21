# Plan de IPs (generado) — criterio de subredes 2

Archivo generado por `scripts/generar.py`; no editar a mano.

## Enlaces

| Red | Router .1 | Router .2 |
| --- | --- | --- |
| 1.0.0.0/8 | Deadlock (1.0.0.1) | Cypher (1.0.0.2) |
| 2.0.0.0/8 | Deadlock (2.0.0.1) | Raze (2.0.0.2) |
| 3.0.0.0/8 | Cypher (3.0.0.1) | Killjoy (3.0.0.2) |
| 4.0.0.0/8 | Raze (4.0.0.1) | Killjoy (4.0.0.2) |
| 5.0.0.0/8 | Raze (5.0.0.1) | Neon (5.0.0.2) |
| 6.0.0.0/8 | Killjoy (6.0.0.1) | Fade (6.0.0.2) |
| 7.0.0.0/8 | Fade (7.0.0.1) | Viper (7.0.0.2) |
| 8.0.0.0/8 | Neon (8.0.0.1) | Gekko (8.0.0.2) |
| 9.0.0.0/8 | Viper (9.0.0.1) | Omen (9.0.0.2) |
| 10.0.0.0/8 | Omen (10.0.0.1) | Sage (10.0.0.2) |
| 11.0.0.0/8 | Reyna (11.0.0.1) | Sage (11.0.0.2) |
| 12.0.0.0/8 | Gekko (12.0.0.1) | Reyna (12.0.0.2) |
| 13.0.0.0/8 | Sage (13.0.0.1) | Brimstone (13.0.0.2) |

## LAN y equipos

| LAN | Red | Máscara | Puerta de enlace | Equipos |
| --- | --- | --- | --- | --- |
| Deadlock | 172.16.24.0/21 | 255.255.248.0 | 172.16.24.1 | GravNet = 172.16.24.2, Annihilation = 172.16.24.3 |
| Raze | 172.16.64.0/21 | 255.255.248.0 | 172.16.64.1 | Paint Shells = 172.16.64.2, Pack Blast = 172.16.64.3 |
| Killjoy | 172.16.120.0/21 | 255.255.248.0 | 172.16.120.1 | Turret = 172.16.120.2, Lockdown = 172.16.120.3 |
| Cypher | 172.16.192.0/21 | 255.255.248.0 | 172.16.192.1 | Trapwire = 172.16.192.2, Spycam = 172.16.192.3, Base server = 172.16.192.4 |
| Gekko | 20.25.16.0/20 | 255.255.240.0 | 20.25.16.1 | Wingman, Dizzy, Thrash (DHCP) |
| Viper | 48.7.0.64/26 | 255.255.255.192 | 48.7.0.65 | Poison Cloud, Snake Bite, Viper's Pit (DHCP) |
| Reyna | 183.112.0.0/13 | 255.248.0.0 | 183.112.0.1 | Dismiss = 183.112.0.2, Devour = 183.112.0.3, Empress = 183.112.0.4 |
| Omen | 4.93.112.0/21 | 255.255.248.0 | 4.93.112.1 | Paranoia = 4.93.112.2, Dark cover = 4.93.112.3, Shrouded Step = 4.93.112.4 |
| Brimstone | 192.168.50.0/24 | 255.255.255.0 | 192.168.50.1 | Location server = 192.168.50.2 |

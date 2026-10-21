# Contrato del Grupo 14

Reglas que los tres respetan para trabajar sin esperarse.

1. **Enlaces:** máscara 255.0.0.0 (/8). El router nombrado primero en el enunciado toma `.1` y el segundo `.2`. Tabla completa en `plan_ip.md`.
2. **LAN:** el router toma siempre la primera IP útil; los equipos van desde `.2` en el orden del enunciado. Gekko y Viper entregan IP por DHCP (se excluyen las primeras 10 útiles).
3. **Variables:** Y = 14, X = 4.
4. **Criterio de subredes:** se define en `scripts/generar.py` (`CRITERIO_DEFECTO`). Cambiarlo regenera configuraciones y tablas del informe.
5. **Interfaces:** los nombres reales (FastEthernet0/0, Serial0/0/0, etc.) van en `interfaces.json`; mientras diga `COMPLETAR`, los `.txt` de `configs/` no son pegables.
6. **Cualquier cambio** al contrato se avisa en el chat del grupo antes de aplicarlo.

## Dudas abiertas para los ayudantes

- [ ] Cómo contar las subredes (¿la subred cero cuenta como 1.ª?). Por defecto se usa el criterio 2: se excluye.
- [ ] ¿La redistribución mutua OSPF/BGP va en Raze y Killjoy (AS 10) o en Neon y Fade? Los `.txt` la dejan en Raze y Killjoy.
- [ ] La LAN de Omen (4.93.x.x) cae dentro de la red 4.0.0.0/8 del enlace Raze–Killjoy. Funciona por prefijo más largo; ¿está previsto?
- [ ] Confirmar en la topología si hay enlace directo Neon–Fade y Gekko–Viper (el enunciado no lo lista).
- [ ] Nombre exacto de los archivos de entrega (guiones bajos o espacios).
- [ ] iBGP dentro del AS 40: hay una propuesta comentada en `Reyna.txt`, `Omen.txt` y `Sage.txt`.

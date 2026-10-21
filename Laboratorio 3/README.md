# Laboratorio 3 — Redes de Computadores — Grupo 14

Capa de red en Cisco Packet Tracer: direccionamiento, DHCP, OSPF, BGP y redistribución.
Entrega: **30 de octubre de 2026, 23:59**, por Aula, como `L3-Grupo14.zip`.

**Lo que le toca a cada uno, las reglas del grupo, las dudas abiertas y la lista de entrega están en [`PLAN_DE_TRABAJO.md`](PLAN_DE_TRABAJO.md). Empezar por ahí.**

## Estructura

```
PLAN_DE_TRABAJO.md        reparto, contrato de direccionamiento, reglas, dudas, entrega
main.tex                  informe (se compila desde aquí, también en Overleaf)
informe/portada.tex       portada con integrantes y roles USM
informe/secciones/        una sección por archivo (02 memoria, 03 registro, 04_q1..q6, 05 conclusiones)
informe/tablas/           tablas .tex GENERADAS (no editar a mano)
configs/                  un .txt por router, GENERADOS por scripts/generar.py
contrato/                 interfaces.json (a completar) y plan_ip.md (generado)
evidencias/Q1..Q6/        capturas y salidas de consola
scripts/generar.py        genera configs/, plan_ip.md y tablas del informe
scripts/empaquetar.py     arma L3-Grupo14.zip desde entrega/
```

## Uso rápido

1. Completar `contrato/interfaces.json` con los nombres reales de interfaz (cada `COMPLETAR`).
2. `python3 scripts/generar.py` (o `--criterio 1`) regenera configs, plan de IPs y tablas del informe.
3. Pegar `configs/<Router>.txt` en la CLI de cada router, en tu copia del `.pkt`.
4. Guardar capturas en `evidencias/Q<n>_*/` y reemplazar cada `\pend{...}` del informe.
5. Compilar `main.tex` con pdfLaTeX.

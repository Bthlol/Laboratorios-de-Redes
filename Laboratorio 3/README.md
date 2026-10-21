# Laboratorio 3 — Redes de Computadores — Grupo 14

Capa de red en Cisco Packet Tracer: direccionamiento, DHCP, OSPF, BGP y redistribución.
Entrega: **30 de octubre de 2026, 23:59** por Aula, como `L3-Grupo14.zip`.
Plan de trabajo completo en el documento compartido del grupo.

## Estructura

```
main.tex                  informe (se compila desde aquí, también en Overleaf)
informe/portada.tex       portada con integrantes y roles USM
informe/secciones/        una sección por archivo (02 memoria, 03 registro, 04_q1..q6, 05 conclusiones)
informe/tablas/           tablas .tex GENERADAS (no editar a mano)
configs/                  un .txt por router, GENERADOS por scripts/generar.py
contrato/                 contrato.md, plan_ip.md (generado), interfaces.json
evidencias/Q1..Q6/        capturas y salidas de consola
scripts/generar.py        genera configs/, plan_ip.md y tablas del informe
scripts/empaquetar.py     arma L3-Grupo14.zip desde entrega/
```

## Quién toca qué

| Integrante | Routers (`configs/`) | Preguntas (`04_q*.tex`, `evidencias/`) | Conclusión |
| --- | --- | --- | --- |
| Sebastián | Deadlock, Cypher, Raze, Killjoy | Q3, Q5 | su subsección en `05_conclusiones.tex` |
| Benjamín | Neon, Fade, Gekko, Viper | Q1, Q4 | idem |
| Bárbara | Reyna, Omen, Sage, Brimstone | Q2, Q6 | idem |

Cada uno edita solo sus archivos, así no hay conflictos al mezclar.

## Flujo de trabajo

1. **Completar interfaces.** Abrir la topología entregada en Packet Tracer y llenar `contrato/interfaces.json` (cada `COMPLETAR`, con el nombre real de la interfaz hacia ese vecino o hacia la LAN). Conviene que cada uno llene solo sus routers.
2. **Generar.** `python3 scripts/generar.py` (o `--criterio 1`). Regenera `configs/`, `contrato/plan_ip.md` y `informe/tablas/`.
3. **Aplicar.** Pegar `configs/<Router>.txt` en la CLI de cada router, en tu copia del `.pkt`.
4. **Probar y capturar.** Guardar las capturas en `evidencias/Q<n>_*/` con los nombres que espera cada sección (si falta una, el PDF muestra un recuadro rojo con el nombre esperado).
5. **Escribir.** Reemplazar cada `\pend{...}` por texto. Antes de entregar no debe quedar ningún "PENDIENTE" en el PDF.

## Git

- Repositorio **privado** (el enunciado sanciona con nota 0 el intercambio de `.pkt` entre grupos).
- Los `.pkt` no se versionan (`.gitignore`); van en una carpeta compartida aparte y solo Sebastián toca el maestro.
- Una rama por persona (`sebastian`, `benjamin`, `barbara`) y *pull request* a `main`, o commits directos a `main` si cada uno respeta sus archivos. Hacer `git pull --rebase` antes de empezar.
- Si alguien edita `generar.py`, avisar en el chat: afecta a los tres.

## Overleaf

- Subir el repositorio como proyecto (zip, o importar desde GitHub si su plan lo permite; la sincronización con GitHub suele ser de pago).
- Compilador: pdfLaTeX. Documento principal: `main.tex`.
- Overleaf no ejecuta Python: las tablas y configs se generan fuera y se suben ya listas. Si usan Overleaf como editor principal, descarguen el proyecto al final y súbanlo al repositorio.

## Entrega

1. Compilar el PDF final y copiarlo a `entrega/` junto con el `.pkt` final.
2. Confirmar en el enunciado original el nombre exacto de ambos archivos y ajustarlo en `scripts/empaquetar.py`.
3. `python3 scripts/empaquetar.py` crea `L3-Grupo14.zip` con solo esos dos archivos.
4. Un solo integrante lo sube a Aula, idealmente el 29 de octubre.

# Laboratorio 5 – Redes de Computadores – Grupo 14

Simulación en **Mininet-WiFi** de una topología de puntos de acceso con forma de lemniscata (N = 8, exponente de pérdida 3,9), con movilidad de estaciones, traspaso entre AP, falla de enlaces con Spanning Tree y throughput según la configuración de canales.

> 🔒 **Repositorio privado del grupo.** No lo hagan público: el enunciado sanciona la copia.
> 📅 **Entrega:** 3 de diciembre, 23:59, por Aula, como `L5-Grupo14.zip`.

## Estado del trabajo

| Ítem | Estado |
|---|---|
| Script de simulación y README de entrega | ✅ Listo (`entrega/`) |
| Mediciones P2, P3 y P4 | ✅ Listas (`resultados/`) |
| Prueba en la VM del curso (OVA) | ✅ Funciona igual que en Ubuntu nativo |
| Informe en Word con las 4 preguntas | 🟡 Contenido listo; faltan capturas, enlace del video, datos de la portada y revisión/redacción propia |
| Video | ⬜ Pendiente: guion y comandos listos en `video/` |
| README de entrega: nombres y roles de integrantes 2 y 3 | ⬜ Pendiente |
| Exportar el informe a PDF y armar el zip | ⬜ Pendiente |

## Estructura

```
entrega/       Lo que va en el zip final (junto con el informe en PDF)
  lab5_simulacion.py   Simulación (topología, movilidad, control de traspaso, mediciones)
  medir_p4.sh          Lote de mediciones de throughput de la P4
  README.md            README de la entrega (integrantes, instrucciones de ejecución)
informe/
  L5-Grupo14-Informe.docx   Informe editable (marcas amarillas = pendientes)
  BORRADOR_INFORME.md       Mismo contenido en texto, para leerlo en GitHub
resultados/
  RESULTADOS.md        Resumen de todos los resultados, con el origen de cada dato
  datos/               Registros originales de cada medición (p2, p3, p4, prueba_vm)
video/
  GUION_VIDEO.md       Guion con el texto de cada escena
  comandos_video.txt   Comandos de cada escena, listos para copiar
docs/
  enunciado_Lab5.pdf   Enunciado del laboratorio
  INSTALACION.md       Cómo instalar Mininet-WiFi (Ubuntu nativo o VM del curso)
  GUIA_MEDICIONES.md   Qué medir en cada pregunta y cómo
herramientas/
  prueba_vm.sh         Prueba automática del script dentro de la VM del curso
```

## Para ponerse al día

1. Lean `resultados/RESULTADOS.md`, que resume en una página lo que se midió y lo que se concluyó.
2. Abran `informe/L5-Grupo14-Informe.docx`. La segunda página (amarilla) lista lo que falta.
3. Para ver la simulación funcionando, instalen Mininet-WiFi según `docs/INSTALACION.md` y ejecuten:

```bash
cd entrega
python3 lab5_simulacion.py --dry-run                   # topología calculada (no necesita Mininet)
sudo python3 lab5_simulacion.py --interferencia        # simulación con plano y CLI
```

## Para grabar el video

Sigan `video/GUION_VIDEO.md` (texto de cada escena) junto con `video/comandos_video.txt` (comandos para copiar). Dura unos 8–9 minutos y se recomienda grabarlo en Ubuntu nativo con OBS. Al terminar, súbanlo como **no listado** y peguen el enlace en la Pregunta 1 del informe y en `entrega/README.md`.

## Decisiones importantes (para poder defenderlas)

- **Spanning Tree** en los AP (`failMode='standalone'`, `stp=True`), con ap0 como raíz y temporizadores cortos, porque los lóbulos son anillos con ciclos.
- **Control de traspaso propio** (`ControlTraspaso`): el de Mininet-WiFi no era confiable en esta topología. Asocia a la mejor señal, con 3 dB de histéresis y traspaso *break-before-make*.
- **Estaciones a 1 m de altura:** wmediumd no admite distancia 0 entre nodos, y sta4 parte sobre ap0.
- **sta5** se mueve en la dirección del eje Y, sobre la recta x = −23.
- El modo **`--interferencia`** (wmediumd) se usó en todas las mediciones: sin él, la señal no depende de la distancia.

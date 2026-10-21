#!/usr/bin/env python3
"""Arma L3-Grupo14.zip con exactamente dos archivos, segun las reglas de entrega.

Antes de usarlo:
  1. Dejar en entrega/ el PDF final y el .pkt final con los nombres de abajo.
  2. CONFIRMAR los nombres exactos en el enunciado original (el texto extraido
     mostraba espacios donde probablemente hay guiones bajos).
"""
import sys
import zipfile
from pathlib import Path

N = "14"
ZIP = f"L3-Grupo{N}.zip"
INFORME = f"Informe_L3_Grupo{N}.pdf"       # <- confirmar
TOPOLOGIA = f"Topologia_L3_Grupo{N}.pkt"   # <- confirmar

ROOT = Path(__file__).resolve().parent.parent
ent = ROOT / "entrega"

faltan = [n for n in (INFORME, TOPOLOGIA) if not (ent / n).exists()]
if faltan:
    sys.exit(f"Faltan en entrega/: {', '.join(faltan)}")

with zipfile.ZipFile(ROOT / ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    for n in (INFORME, TOPOLOGIA):
        z.write(ent / n, arcname=n)

with zipfile.ZipFile(ROOT / ZIP) as z:
    print(f"{ZIP} creado con: {z.namelist()}")

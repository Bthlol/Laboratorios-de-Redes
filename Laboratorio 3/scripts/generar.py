#!/usr/bin/env python3
"""Genera, a partir del contrato de direccionamiento del Grupo 14:

  - configs/<Router>.txt           comandos IOS por router (pegables en Packet Tracer)
  - contrato/plan_ip.md            tabla de IPs de enlaces y equipos
  - informe/tablas/subredes.tex    Memoria de calculo (LAN y enlaces)
  - informe/tablas/variables.tex   macros \\Xval y \\Yval

Uso:
    python3 scripts/generar.py                # criterio por defecto (CRITERIO abajo)
    python3 scripts/generar.py --criterio 1   # la subred cero cuenta como 1.a
    python3 scripts/generar.py --criterio 2   # se excluye la subred cero

Los nombres de interfaz se leen de contrato/interfaces.json (se crea la primera
vez con el valor COMPLETAR; hay que llenarlo mirando la topologia en Packet Tracer).
"""
import argparse
import ipaddress as ip
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRUPO = 14
Y = GRUPO
X = GRUPO % 10 or 10
CRITERIO_DEFECTO = 2  # 1: subred cero cuenta como 1.a | 2: se excluye (clasico)

# ---------------------------------------------------------------- topologia
AS = {
    "Deadlock": 10, "Cypher": 10, "Raze": 10, "Killjoy": 10,
    "Neon": 20, "Fade": 20,
    "Gekko": 30, "Viper": 30,
    "Reyna": 40, "Omen": 40, "Sage": 40,
    "Brimstone": 50,
}
DUENO = {
    "Deadlock": "Sebastián", "Cypher": "Sebastián", "Raze": "Sebastián", "Killjoy": "Sebastián",
    "Neon": "Benjamín", "Fade": "Benjamín", "Gekko": "Benjamín", "Viper": "Benjamín",
    "Reyna": "Bárbara", "Omen": "Bárbara", "Sage": "Bárbara", "Brimstone": "Bárbara",
}
# (red, router .1, router .2)  -- el primero nombrado en el enunciado toma .1
ENLACES = [
    ("1.0.0.0", "Deadlock", "Cypher"),
    ("2.0.0.0", "Deadlock", "Raze"),
    ("3.0.0.0", "Cypher", "Killjoy"),
    ("4.0.0.0", "Raze", "Killjoy"),
    ("5.0.0.0", "Raze", "Neon"),
    ("6.0.0.0", "Killjoy", "Fade"),
    ("7.0.0.0", "Fade", "Viper"),
    ("8.0.0.0", "Neon", "Gekko"),
    ("9.0.0.0", "Viper", "Omen"),
    ("10.0.0.0", "Omen", "Sage"),
    ("11.0.0.0", "Reyna", "Sage"),
    ("12.0.0.0", "Gekko", "Reyna"),
    ("13.0.0.0", "Sage", "Brimstone"),
]
ENLACE_MASK = ip.ip_network("1.0.0.0/8").netmask  # 255.0.0.0


def _bits(n):
    return math.ceil(math.log2(n))


# LAN: base, prefijo resultante, n-esima subred, equipos, dhcp
LANS = {
    "Deadlock": dict(base="172.16.0.0/16", prefijo=16 + 5, n=3,
                     equipos=["GravNet", "Annihilation"]),
    "Raze": dict(base="172.16.0.0/16", prefijo=16 + 5, n=8,
                 equipos=["Paint Shells", "Pack Blast"]),
    "Killjoy": dict(base="172.16.0.0/16", prefijo=16 + 5, n=15,
                    equipos=["Turret", "Lockdown"]),
    "Cypher": dict(base="172.16.0.0/16", prefijo=16 + 5, n=24,
                   equipos=["Trapwire", "Spycam", "Base server"]),
    "Gekko": dict(base="20.25.0.0/16", prefijo=16 + (X // 2 + 2), n=1,
                  equipos=["Wingman", "Dizzy", "Thrash"], dhcp=True),
    "Viper": dict(base="48.7.0.0/16", prefijo=32 - _bits(Y + 25 + 2), n=1,
                  equipos=["Poison Cloud", "Snake Bite", "Viper's Pit"], dhcp=True),
    "Reyna": dict(base="183.0.0.0/8", prefijo=8 + _bits(2 * (X + 8)), n=Y,
                  equipos=["Dismiss", "Devour", "Empress"]),
    "Omen": dict(base="4.93.0.0/16", prefijo=16 + 5, n=Y,
                 equipos=["Paranoia", "Dark cover", "Shrouded Step"]),
    "Brimstone": dict(base="192.168.50.0/24", prefijo=24, n=None,
                      equipos=["Location server"]),
}
REGLAS = {
    "Deadlock": "172.16.0.0/16 en 32 subredes, la 3.ª",
    "Raze": "172.16.0.0/16 en 32 subredes, la 8.ª",
    "Killjoy": "172.16.0.0/16 en 32 subredes, la 15.ª",
    "Cypher": "172.16.0.0/16 en 32 subredes, la 24.ª",
    "Gekko": f"20.25.0.0/16 con (X/2)+2 = {X // 2 + 2} bits, la primera",
    "Viper": f"48.7.0.0/16 con Y+25 = {Y + 25} hosts, la primera",
    "Reyna": f"183.0.0.0/8 en al menos 2(X+8) = {2 * (X + 8)} subredes, la Y-ésima",
    "Omen": "4.93.0.0/16 en 32 subredes, la Y-ésima",
    "Brimstone": "192.168.50.0/24 (dada por el enunciado)",
}


def calcular_lans(criterio):
    res = {}
    for r, d in LANS.items():
        base = ip.ip_network(d["base"])
        if d["n"] is None:
            red = base
        else:
            idx = d["n"] - 1 if criterio == 1 else d["n"]
            subs = list(base.subnets(new_prefix=d["prefijo"]))
            if idx >= len(subs):
                raise SystemExit(f"{r}: la subred {d['n']} no existe con criterio {criterio}")
            red = subs[idx]
        res[r] = red
    return res


# ---------------------------------------------------------------- interfaces
# La topologia entregada trae las lineas como DIBUJOS (no son cables reales) y
# los 1941 solo tienen 2 puertos Gigabit. Supuesto del grupo: se usan los 2
# Gigabit para la LAN y un enlace Ethernet, y un modulo HWIC-2T (seriales) en
# la ranura 0 para los enlaces restantes. Reglas de asignacion:
#   - LAN (o servidor directo)           -> GigabitEthernet0/0
#   - enlaces Ethernet (GIG_LINKS)       -> siguiente Gigabit libre
#   - enlaces seriales (SERIAL_LINKS)    -> Serial0/0/0, Serial0/0/1
# El router nombrado primero en el enlace (.1) es el extremo DCE (clock rate).
SERIAL_LINKS = {"2.0.0.0", "3.0.0.0", "4.0.0.0", "9.0.0.0", "12.0.0.0", "13.0.0.0"}
CLOCK_RATE = 64000


def es_serial(red):
    return red in SERIAL_LINKS


def plan_ifaces():
    d = {r: {} for r in AS}
    for r in AS:
        gig = 0
        ser = 0
        if r in LANS:
            d[r]["LAN"] = "GigabitEthernet0/0"
            gig = 1
        for red, vec, _, _ in enlaces_de(r):
            if es_serial(red):
                d[r][vec] = f"Serial0/0/{ser}"
                ser += 1
            else:
                d[r][vec] = f"GigabitEthernet0/{gig}"
                gig += 1
        if gig > 2 or ser > 2:
            raise SystemExit(f"{r}: necesita {gig} Gigabit y {ser} seriales (max 2 y 2)")
    return d


def cargar_ifaces():
    """Plan por defecto; contrato/interfaces.json (si existe) lo sobreescribe."""
    d = plan_ifaces()
    ruta = ROOT / "contrato" / "interfaces.json"
    if ruta.exists():
        ov = json.loads(ruta.read_text(encoding="utf-8"))
        for r, m in ov.items():
            d[r].update(m)
    else:
        ruta.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return d


# ---------------------------------------------------------------- helpers
def ip_enlace(router, red):
    for n, a, b in ENLACES:
        if n == red:
            return f"{n[:-1]}1" if router == a else f"{n[:-1]}2"
    raise KeyError(red)


def enlaces_de(router):
    """[(red, vecino, ip_local, ip_vecino)]"""
    out = []
    for n, a, b in ENLACES:
        if router == a:
            out.append((n, b, f"{n[:-1]}1", f"{n[:-1]}2"))
        elif router == b:
            out.append((n, a, f"{n[:-1]}2", f"{n[:-1]}1"))
    return out


def wildcard(red):
    return str(red.hostmask)


def primera_util(red):
    return next(red.hosts())


def ip_equipo(red, i):
    """i = 0 -> primer equipo -> .2"""
    return red.network_address + 2 + i


# ---------------------------------------------------------------- configs
def config_router(router, lans, ifaces):
    asn = AS[router]
    L = []
    w = L.append
    w("!" + "=" * 60)
    w(f"! Router: {router}   AS {asn}   Responsable: {DUENO[router]}")
    w("! Generado por scripts/generar.py: para cambiar algo, editar el script o")
    w("! contrato/interfaces.json y volver a ejecutarlo.")
    mods = "HWIC-2T en la ranura 0 (puertos seriales)" if any(
        es_serial(r) for r, _, _, _ in enlaces_de(router)) else "ninguno"
    w(f"! Modulos necesarios: {mods}")
    w("!" + "=" * 60)
    w("enable")
    w("configure terminal")
    w(f"hostname {router}")
    w("!")
    # interfaces de enlace
    for red, vec, mi_ip, _ in enlaces_de(router):
        w(f"interface {ifaces[router][vec]}")
        w(f" description Enlace con {vec} ({red}/8)")
        w(f" ip address {mi_ip} {ENLACE_MASK}")
        if es_serial(red) and mi_ip.endswith(".1"):
            w(f" clock rate {CLOCK_RATE}")
        w(" no shutdown")
        w("!")
    # interfaz LAN
    if router in lans:
        red = lans[router]
        w(f"interface {ifaces[router]['LAN']}")
        w(f" description LAN de {router} ({red})")
        w(f" ip address {primera_util(red)} {red.netmask}")
        w(" no shutdown")
        w("!")
    # DHCP
    if LANS.get(router, {}).get("dhcp"):
        red = lans[router]
        ini = primera_util(red)
        fin = ini + 9
        w(f"ip dhcp excluded-address {ini} {fin}")
        w("ip dhcp pool POOL_LAN")
        w(f" network {red.network_address} {red.netmask}")
        w(f" default-router {ini}")
        w(" dns-server 0.0.0.0")
        w("!")
    # OSPF: proceso 1 en el AS 10 y proceso 40 en el AS 40.
    # Packet Tracer no soporta iBGP ("Only external neighbors are supported"),
    # asi que dentro del AS 40 las rutas se mueven por OSPF y cada router de
    # borde redistribuye entre OSPF y BGP, igual que Raze y Killjoy en el AS 10.
    if asn in (10, 40):
        w(f"router ospf {1 if asn == 10 else 40}")
        for red, vec, _, _ in enlaces_de(router):
            if AS[vec] == asn:
                w(f" network {red} 0.255.255.255 area 0")
        if router in lans:
            w(f" network {lans[router].network_address} {wildcard(lans[router])} area 0")
        # redistribucion mutua en routers de frontera (ver dudas del enunciado)
        if any(AS[v] != asn for _, v, _, _ in enlaces_de(router)):
            w(f" redistribute bgp {asn} subnets")
        w("!")
    # BGP
    ebgp = [(r, v, mi, su) for r, v, mi, su in enlaces_de(router) if AS[v] != asn]
    if ebgp:
        w(f"router bgp {asn}")
        for _, vec, _, su in ebgp:
            w(f" neighbor {su} remote-as {AS[vec]}")
        if asn == 10:
            # match internal: solo se exportan las redes propias del AS 10.
            # Sin esto Packet Tracer reexporta tambien las O E2 aprendidas de
            # Omega, y Neon y Fade las prefieren por tener AS-Path "10" (bucle).
            w(" redistribute ospf 1 match internal")
        else:
            for red, _, _, _ in enlaces_de(router):
                w(f" network {red} mask {ENLACE_MASK}")
            if router in lans:
                red = lans[router]
                w(f" network {red.network_address} mask {red.netmask}")
        if asn == 40:
            # Aqui si se exportan las externas: Location server llega a Sage por
            # eBGP, entra a OSPF 40 como O E2 y Omen y Reyna la publican afuera.
            w(" redistribute ospf 40 match internal external 1 external 2")
        w("!")
    w("end")
    w("write memory")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- salidas
def _col(cm):
    return f">{{\\raggedright\\arraybackslash}}p{{{cm}cm}}"


def tex(s):
    return s.replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")


def escribir_configs(lans, ifaces, criterio):
    for r in AS:
        txt = config_router(r, lans, ifaces).replace(
            "! Generado por", f"! Criterio de subredes: {criterio}\n! Generado por", 1)
        (ROOT / "configs" / f"{r}.txt").write_text(txt, encoding="utf-8")


def escribir_plan_ip(lans, criterio, ifaces):
    L = [f"# Plan de IPs (generado) — criterio de subredes {criterio}",
         "",
         "Archivo generado por `scripts/generar.py`; no editar a mano.",
         "",
         "## Enlaces",
         "",
         "| Red | Router .1 | Router .2 |",
         "| --- | --- | --- |"]
    for n, a, b in ENLACES:
        L.append(f"| {n}/8 | {a} ({n[:-1]}1) | {b} ({n[:-1]}2) |")
    L += ["", "## LAN y equipos", "",
          "| LAN | Red | Máscara | Puerta de enlace | Equipos |",
          "| --- | --- | --- | --- | --- |"]
    for r, red in lans.items():
        d = LANS[r]
        if d.get("dhcp"):
            eq = ", ".join(d["equipos"]) + " (DHCP)"
        else:
            eq = ", ".join(f"{e} = {ip_equipo(red, i)}" for i, e in enumerate(d["equipos"]))
        L.append(f"| {r} | {red} | {red.netmask} | {primera_util(red)} | {eq} |")
    L += ["", "## Cableado (supuesto del grupo)", "",
          "La topologia entregada trae lineas dibujadas, no cables. Se cablea asi, y cada router",
          "con un enlace serial recibe un HWIC-2T en la ranura 0 (router apagado al insertarlo).",
          "En los seriales, hacer clic primero en el router del extremo .1 (DCE).", "",
          "| Red | Tipo de cable | Extremo .1 | Extremo .2 |",
          "| --- | --- | --- | --- |"]
    for n, a, b in ENLACES:
        tipo = "Serial DCE" if es_serial(n) else "Copper Cross-Over"
        L.append(f"| {n}/8 | {tipo} | {a} {ifaces[a][b]} | {b} {ifaces[b][a]} |")
    L += ["", "LAN: cada router conecta GigabitEthernet0/0 a su switch con cable Copper Straight-Through "
          "(Brimstone conecta Gi0/0 directo a Location server con Cross-Over). "
          "Base server va al switch de Cypher, no directo al router.", ""]
    (ROOT / "contrato" / "plan_ip.md").write_text("\n".join(L), encoding="utf-8")


def escribir_tex(lans, criterio, ifaces):
    out = ROOT / "informe" / "tablas"
    (out / "variables.tex").write_text(
        f"\\newcommand{{\\Xval}}{{{X}}}\n\\newcommand{{\\Yval}}{{{Y}}}\n"
        f"\\newcommand{{\\CriterioSubredes}}{{{criterio}}}\n", encoding="utf-8")

    filas = []
    for r, red in lans.items():
        hosts = list(red.hosts())
        d = LANS[r]
        disp = f"Router {r} ({hosts[0]})"
        if d.get("dhcp"):
            disp += "; " + ", ".join(d["equipos"]) + " (DHCP)"
        else:
            disp += "; " + ", ".join(f"{e} ({ip_equipo(red, i)})" for i, e in enumerate(d["equipos"]))
        filas.append(
            f"LAN {tex(r)} & {red} & {red.netmask} /{red.prefixlen} & "
            f"{hosts[0]} -- {hosts[-1]} & {red.broadcast_address} & {tex(disp)} \\\\")
    cab = (
        "\\begin{longtable}{@{}" + _col(1.6) + _col(2.4) + _col(2.5) + _col(3.1) + _col(2.2) + _col(3.5) + "@{}}\n"
        "\\toprule\n"
        "Subred & Red & Máscara y CIDR & Rango útil & Broadcast & Dispositivos \\\\\n"
        "\\midrule\n\\endhead\n")
    (out / "subredes_lan.tex").write_text(
        cab + "\n".join(filas) + "\n\\bottomrule\n\\end{longtable}\n", encoding="utf-8")

    filas = []
    for n, a, b in ENLACES:
        red = ip.ip_network(f"{n}/8")
        hosts = (red.network_address + 1, red.broadcast_address - 1)
        filas.append(
            f"{n}/8 & 255.0.0.0 /8 & {hosts[0]} -- {hosts[1]} & "
            f"{red.broadcast_address} & {a} ({n[:-1]}1), {b} ({n[:-1]}2) \\\\")
    cab = (
        "\\begin{longtable}{@{}" + _col(1.8) + _col(2.4) + _col(4.2) + _col(2.6) + _col(4.2) + "@{}}\n"
        "\\toprule\n"
        "Red & Máscara y CIDR & Rango útil & Broadcast & Dispositivos \\\\\n"
        "\\midrule\n\\endhead\n")
    (out / "subredes_enlaces.tex").write_text(
        cab + "\n".join(filas) + "\n\\bottomrule\n\\end{longtable}\n", encoding="utf-8")

    filas = []
    for n, a, b in ENLACES:
        tipo = "Serial DCE" if es_serial(n) else "Cobre cruzado"
        filas.append(f"{n}/8 & {tipo} & {a} {ifaces[a][b]} & {b} {ifaces[b][a]} \\\\")
    (out / "cableado.tex").write_text(
        "\\begin{tabular}{@{}llll@{}}\n\\toprule\n"
        "Red & Cable & Extremo .1 & Extremo .2 \\\\\n\\midrule\n"
        + "\n".join(filas) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")

    filas = [f"{tex(r)} & {tex(REGLAS[r])} & /{lans[r].prefixlen} \\\\" for r in lans]
    (out / "reglas_lan.tex").write_text(
        "\\begin{tabular}{@{}p{2cm}p{9cm}p{1.5cm}@{}}\n\\toprule\n"
        "LAN & Regla aplicada (X=\\Xval, Y=\\Yval) & Prefijo \\\\\n\\midrule\n"
        + "\n".join(filas) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--criterio", type=int, choices=(1, 2), default=CRITERIO_DEFECTO)
    a = ap.parse_args()
    ifaces = cargar_ifaces()
    lans = calcular_lans(a.criterio)
    escribir_configs(lans, ifaces, a.criterio)
    escribir_plan_ip(lans, a.criterio, ifaces)
    escribir_tex(lans, a.criterio, ifaces)
    pend = sum(1 for r in ifaces.values() for v in r.values() if v == "COMPLETAR")
    print(f"Criterio {a.criterio}: configs, plan_ip.md y tablas .tex generados.")
    if pend:
        print(f"AVISO: {pend} interfaces sin completar en contrato/interfaces.json")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Arma el .pkt maestro del Lab 3 a partir de un borrador y del repositorio.

Toma un .pkt (por ejemplo el borrador con el AS 10 ya hecho) y le agrega lo
que falte, leyendo contrato/plan_ip.md y configs/*.txt:

  - un HWIC-2T en la ranura 0 de cada router que tenga un enlace serial
  - los cables de la seccion "Cableado" de plan_ip.md y los de cada LAN
  - la configuracion de cada router que todavia se llame "Router"
  - IP fija o DHCP en los equipos finales, segun plan_ip.md

No toca lo que ya esta hecho: los routers con nombre propio, los puertos
ya cableados y los equipos que ya tienen IP se dejan tal cual.

Uso (desde "Laboratorio 3"):
    python3 scripts/armar_maestro.py BORRADOR.pkt SALIDA.pkt [--ibgp-as40 malla|propuesta|ninguno]

Requiere el paquete twofish (pip install twofish), que trae el cifrado que
usa Packet Tracer para sus archivos.
"""
import argparse
import copy
import ctypes
import glob
import importlib.util
import os
import random
import re
import struct
import sys
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------ cifrado
def _cargar_twofish():
    spec = importlib.util.find_spec("twofish")
    if spec is None:
        sys.exit("Falta el paquete twofish: pip install twofish")
    carpeta = os.path.dirname(spec.origin)
    so = glob.glob(os.path.join(carpeta, "_twofish*"))
    if not so:
        sys.exit("No encontre la libreria _twofish del paquete twofish")
    lib = ctypes.cdll.LoadLibrary(so[0])

    class Key(ctypes.Structure):
        _fields_ = [("s", (ctypes.c_uint32 * 4) * 256), ("K", ctypes.c_uint32 * 40)]

    lib.exp_Twofish_initialise()
    key = Key()
    lib.exp_Twofish_prepare_key(bytes([137] * 16), 16, ctypes.byref(key))

    def enc(block):
        out = ctypes.create_string_buffer(16)
        lib.exp_Twofish_encrypt(ctypes.byref(key), block, out)
        return out.raw
    return enc


E = None
IV = bytes([16] * 16)


def _xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def _dbl(b):
    n = int.from_bytes(b, "big") << 1
    if n >> 128:
        n ^= 0x87
    return (n & ((1 << 128) - 1)).to_bytes(16, "big")


def _cmac(msg):
    L = E(bytes(16)); k1 = _dbl(L); k2 = _dbl(k1)
    bl = [msg[i:i + 16] for i in range(0, len(msg), 16)] or [b""]
    last = bl[-1]
    bl[-1] = _xor(last, k1) if len(last) == 16 else _xor(last + b"\x80" + bytes(15 - len(last)), k2)
    c = bytes(16)
    for b in bl:
        c = E(_xor(c, b))
    return c


def _omac(t, m):
    return _cmac(bytes(15) + bytes([t]) + m)


def _ctr(data, n0):
    out = bytearray(); c = int.from_bytes(n0, "big")
    for i in range(0, len(data), 16):
        ks = E((c & ((1 << 128) - 1)).to_bytes(16, "big")); c += 1
        out += _xor(data[i:i + 16], ks)
    return bytes(out)


def descifrar(raw):
    n = len(raw)
    s1 = bytes(raw[n - 1 - i] ^ ((n - i * n) & 0xFF) for i in range(n))
    pt = _ctr(s1[:-16], _omac(0, IV))
    m = len(pt)
    s3 = bytes(pt[i] ^ ((m - i) & 0xFF) for i in range(m))
    return zlib.decompress(s3[4:])


def cifrar(xml):
    comp = struct.pack(">I", len(xml)) + zlib.compress(xml)
    m = len(comp)
    s3 = bytes(comp[i] ^ ((m - i) & 0xFF) for i in range(m))
    N = _omac(0, IV)
    ct = _ctr(s3, N)
    tag = _xor(_xor(N, _omac(2, ct)), _omac(1, b""))
    s1 = ct + tag; n = len(s1)
    out = bytearray(n)
    for i in range(n):
        out[n - 1 - i] = s1[i] ^ ((n - i * n) & 0xFF)
    return bytes(out)


# ------------------------------------------------------------------ repo
NOMBRES_PKT = {  # nombre en el repo -> nombre en la topologia entregada
    "Annihilation": "Annhilation",
    "Trapwire": "Tripwire",
    "Pack Blast": "Blast Pack",
    "Viper's Pit": "Viper´s Pit",
}


def leer_plan():
    txt = (ROOT / "contrato" / "plan_ip.md").read_text(encoding="utf-8")
    cables, lans = [], {}
    sec = None
    for linea in txt.splitlines():
        if linea.startswith("## "):
            sec = linea[3:].strip()
            continue
        if not linea.startswith("|") or "---" in linea:
            continue
        cel = [c.strip() for c in linea.strip("|").split("|")]
        if sec and sec.startswith("Cableado") and cel[0] != "Red":
            a = cel[2].split(" ", 1); b = cel[3].split(" ", 1)
            cables.append(dict(red=cel[0], tipo=cel[1], a=a[0], pa=a[1], b=b[0], pb=b[1]))
        elif sec and sec.startswith("LAN") and cel[0] != "LAN":
            router, red, mask, gw, eq = cel
            if "(DHCP)" in eq:
                equipos = [(e.strip(), None) for e in eq.replace("(DHCP)", "").split(",")]
            else:
                equipos = [tuple(x.strip() for x in e.split("=")) for e in eq.split(",")]
            lans[router] = dict(red=red, mask=mask, gw=gw, equipos=equipos)
    return cables, lans


def leer_config(router, ibgp):
    """Devuelve (hostname, {iface: dict}, dhcp_lines, ospf_lines, bgp_lines)."""
    lineas = (ROOT / "configs" / f"{router}.txt").read_text(encoding="utf-8").splitlines()
    ifaces, dhcp, ospf, bgp = {}, [], [], []
    host = router
    bloque = None
    for l in lineas:
        cruda = l
        if l.startswith(" ! neighbor") and ibgp == "propuesta":
            l = " " + l[3:]
        if not l.strip() or l.lstrip().startswith("!") or l.strip() in ("enable", "configure terminal", "end", "write memory"):
            if not l.startswith(" "):
                bloque = None if l.strip() != "!" else bloque
            continue
        if l.startswith("hostname "):
            host = l.split()[1]; bloque = None
        elif l.startswith("interface "):
            bloque = ("if", l.split(None, 1)[1]); ifaces[bloque[1]] = dict(lines=[], up=False, ip=None, mask=None, desc="", clock=None)
        elif l.startswith("ip dhcp"):
            dhcp.append(l); bloque = ("dhcp",) if l.startswith("ip dhcp pool") else None
        elif l.startswith("router ospf"):
            bloque = ("ospf",); ospf.append(l)
        elif l.startswith("router bgp"):
            bloque = ("bgp",); bgp.append(l)
        elif l.startswith(" ") and bloque:
            if bloque[0] == "if":
                d = ifaces[bloque[1]]; s = l.strip()
                if s == "no shutdown":
                    d["up"] = True
                elif s.startswith("ip address"):
                    _, _, d["ip"], d["mask"] = s.split(); d["lines"].append(l)
                elif s.startswith("description"):
                    d["desc"] = s.split(None, 1)[1]; d["lines"].append(l)
                elif s.startswith("clock rate"):
                    d["clock"] = s.split()[-1]; d["lines"].append(l)
                else:
                    d["lines"].append(l)
            elif bloque[0] == "dhcp":
                dhcp.append(l)
            elif bloque[0] == "ospf":
                ospf.append(l)
            elif bloque[0] == "bgp":
                bgp.append(l)
    return host, ifaces, dhcp, ospf, bgp


# iBGP del AS 40 en malla completa: cada router conoce a los otros dos.
# Omen y Reyna no estan conectados directo, pero se alcanzan por Sage porque
# Sage publica las redes 10.0.0.0 y 11.0.0.0 por BGP.
IBGP_MALLA = {
    "Omen": [" neighbor 10.0.0.2 remote-as 40", " neighbor 10.0.0.2 next-hop-self",
             " neighbor 11.0.0.1 remote-as 40", " neighbor 11.0.0.1 next-hop-self"],
    "Reyna": [" neighbor 11.0.0.2 remote-as 40", " neighbor 11.0.0.2 next-hop-self",
              " neighbor 10.0.0.1 remote-as 40", " neighbor 10.0.0.1 next-hop-self"],
    "Sage": [" neighbor 10.0.0.1 remote-as 40", " neighbor 10.0.0.1 next-hop-self",
             " neighbor 11.0.0.1 remote-as 40", " neighbor 11.0.0.1 next-hop-self"],
}

CLASSFUL = {8: "255.0.0.0", 16: "255.255.0.0", 24: "255.255.255.0"}


def _classful_mask(ip):
    o = int(ip.split(".")[0])
    return CLASSFUL[8] if o < 128 else CLASSFUL[16] if o < 192 else CLASSFUL[24]


# ------------------------------------------------------------------ pkt
class Pkt:
    def __init__(self, xml):
        self.root = ET.fromstring(xml)
        self.devs = {}
        self.ref = {}
        for d in self.root.find("NETWORK/DEVICES").findall("DEVICE"):
            e = d.find("ENGINE")
            self.devs[e.findtext("NAME")] = d
            self.ref[e.findtext("SAVE_REF_ID")] = e.findtext("NAME")
        self.links = self.root.find("NETWORK/LINKS")
        self.ocupados = set()
        for l in self.links.findall("LINK"):
            c = l.find("CABLE"); p = c.findall("PORT")
            self.ocupados.add((self.ref[c.findtext("FROM")], p[0].text))
            self.ocupados.add((self.ref[c.findtext("TO")], p[1].text))

    def engine(self, n):
        return self.devs[n].find("ENGINE")

    def puertos(self, n):
        """{nombre_ios: elemento PORT} para un router 1941, switch 2960 o equipo final."""
        e = self.engine(n); tipo = e.findtext("TYPE")
        res = {}
        top = e.find("MODULE")
        if tipo == "Router":
            nr = top.find("SLOT/MODULE")
            for i, p in enumerate(nr.findall("PORT")):
                res[f"GigabitEthernet0/{i}"] = p
            for si, s in enumerate(nr.findall("SLOT")):
                m = s.find("MODULE")
                if m is not None:
                    for j, p in enumerate(m.findall("PORT")):
                        res[f"Serial0/{si}/{j}"] = p
        elif tipo == "Switch":
            nr = top.find("SLOT/MODULE")
            ps = list(nr.iter("PORT"))
            for i, p in enumerate(ps):
                nombre = f"FastEthernet0/{i + 1}" if i < 24 else f"GigabitEthernet0/{i - 23}"
                res[nombre] = p
        else:
            p = next(top.iter("PORT"))
            res["FastEthernet0"] = p
        return res

    def agregar_hwic(self, n, molde):
        nr = self.engine(n).find("MODULE/SLOT/MODULE")
        slot0 = nr.findall("SLOT")[0]
        if slot0.find("MODULE") is not None:
            return False
        gi0 = nr.findall("PORT")[0]
        mac = gi0.findtext("MACADDRESS")
        b = bytes.fromhex(mac.replace(".", ""))
        eui = bytes([b[0] ^ 2]) + b[1:3] + b"\xff\xfe" + b[3:]
        ll = "FE80::" + ":".join(f"{int.from_bytes(eui[i:i + 2], 'big'):X}" for i in range(0, 8, 2))
        m = copy.deepcopy(molde)
        for p in m.findall("PORT"):
            for tag, val in (("MACADDRESS", mac), ("BIA", mac), ("IPV6_DEFAULT_LINK_LOCAL", ll),
                             ("CLOCKRATE", "2000000"), ("CLOCKRATEFLAG", "true"), ("UP_METHOD", "5"),
                             ("IP", None), ("SUBNET", None), ("DESCRIPTION", None), ("BANDWIDTH", "1544")):
                p.find(tag).text = val
        slot0.append(m)
        return True

    def cable(self, a, pa, b, pb, tipo):
        if (a, pa) in self.ocupados or (b, pb) in self.ocupados:
            return False
        ea, eb = self.engine(a), self.engine(b)
        link = ET.SubElement(self.links, "LINK")
        ET.SubElement(link, "TYPE").text = "eSerial" if tipo == "Serial DCE" else "eCopper"
        c = ET.SubElement(link, "CABLE")
        for tag, val in (("LENGTH", "1"), ("FUNCTIONAL", "true"),
                         ("FROM", ea.findtext("SAVE_REF_ID")), ("PORT", pa),
                         ("TO", eb.findtext("SAVE_REF_ID")), ("PORT", pb),
                         ("FROM_DEVICE_MEM_ADDR", self.devs[a].findtext("WORKSPACE/LOGICAL/DEV_ADDR")),
                         ("TO_DEVICE_MEM_ADDR", self.devs[b].findtext("WORKSPACE/LOGICAL/DEV_ADDR")),
                         ("FROM_PORT_MEM_ADDR", str(random.randint(2_700_000_000_000, 2_799_999_999_999))),
                         ("TO_PORT_MEM_ADDR", str(random.randint(2_700_000_000_000, 2_799_999_999_999))),
                         ("GEO_VIEW_COLOR", "#1e59a5" if tipo == "Serial DCE" else "#6ba72e"),
                         ("IS_MANAGED_IN_RACK_VIEW", "false")):
            ET.SubElement(c, tag).text = val
        if tipo == "Serial DCE":
            ET.SubElement(c, "DCEDEV").text = ea.findtext("SAVE_REF_ID")
            ET.SubElement(c, "DCEPORT").text = pa
        else:
            ET.SubElement(c, "TYPE").text = "eCrossOver" if "Cross" in tipo else "eStraightThrough"
        self.ocupados.update({(a, pa), (b, pb)})
        return True

    def configurar_router(self, n, ibgp):
        e = self.engine(n)
        run = e.find("RUNNINGCONFIG")
        actual = [l.text or "" for l in run.findall("LINE")]
        if "hostname Router" not in actual:
            return False
        host, ifaces, dhcp, ospf, bgp = leer_config(n, ibgp)
        if ibgp == "malla" and n in IBGP_MALLA:
            bgp = bgp + IBGP_MALLA[n]
        puertos = self.puertos(n)
        # bloque de interfaces
        ifl = []
        for nombre, p in puertos.items():
            d = ifaces.get(nombre)
            ifl.append(f"interface {nombre}")
            if d:
                ifl += d["lines"]
                if nombre.startswith("Gig"):
                    ifl += [" duplex auto", " speed auto"]
                if not d["up"]:
                    ifl.append(" shutdown")
                p.find("IP").text = d["ip"]; p.find("SUBNET").text = d["mask"]
                p.find("DESCRIPTION").text = d["desc"] or None
                p.find("POWER").text = "true"
                p.find("UP_METHOD").text = "3" if d["up"] else "5"
                p.find("FULLDUPLEX").text = "true"
                if nombre.startswith("Gig"):
                    p.find("BANDWIDTH").text = "1000000"
                if d["clock"]:
                    p.find("CLOCKRATE").text = d["clock"]; p.find("CLOCKRATEFLAG").text = "true"
            else:
                ifl.append(" no ip address")
                if nombre.startswith("Gig"):
                    ifl += [" duplex auto", " speed auto"]
                else:
                    ifl.append(" clock rate 2000000")
                ifl.append(" shutdown")
            ifl.append("!")
        ifl += ["interface Vlan1", " no ip address", " shutdown", "!"]
        # bloques de enrutamiento con el formato que muestra IOS
        rut = []
        if ospf:
            rut += [ospf[0], " log-adjacency-changes"] + ospf[1:] + ["!"]
        if bgp:
            rut += [bgp[0], " bgp log-neighbor-changes", " no synchronization"]
            for l in bgp[1:]:
                m = re.match(r" network (\S+) mask (\S+)", l)
                if m and _classful_mask(m.group(1)) == m.group(2):
                    l = f" network {m.group(1)}"
                rut.append(l)
            rut.append("!")
        # armar sobre el running-config original del router
        i_sp = actual.index("spanning-tree mode pvst")
        i_if = next(i for i, l in enumerate(actual) if l.startswith("interface "))
        i_cl = actual.index("ip classless")
        cab = ["hostname " + host if l == "hostname Router" else l for l in actual[:i_sp]]
        if dhcp:
            i_cef = cab.index("no ipv6 cef")
            pool = [l for l in dhcp if not l.startswith("ip dhcp excluded")]
            exc = [l for l in dhcp if l.startswith("ip dhcp excluded")]
            cab = cab[:i_cef + 1] + ["!"] + exc + ["!"] + pool + ["!"] + cab[i_cef + 1:]
        nuevo = cab + actual[i_sp:i_if] + ifl + rut + actual[i_cl:]
        for tag in ("RUNNINGCONFIG", "STARTUPCONFIG"):
            el = e.find(tag)
            for c in list(el):
                el.remove(c)
            for l in nuevo:
                ET.SubElement(el, "LINE").text = l
        e.find("SYS_NAME").text = host
        return True

    def ip_equipo(self, n, ip, mask, gw):
        p = self.puertos(n)["FastEthernet0"]
        if p.findtext("IP") or p.findtext("PORT_DHCP_ENABLE") == "true":
            return False
        e = self.engine(n)
        if ip is None:
            p.find("PORT_DHCP_ENABLE").text = "true"
        else:
            p.find("IP").text = ip; p.find("SUBNET").text = mask
            p.find("PORT_GATEWAY").text = gw
            e.find("GATEWAY").text = gw
        return True


def main():
    global E
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("salida")
    ap.add_argument("--ibgp-as40", choices=("malla", "propuesta", "ninguno"), default="malla")
    a = ap.parse_args()
    E = _cargar_twofish()
    pkt = Pkt(descifrar(Path(a.base).read_bytes()))
    cables, lans = leer_plan()

    molde = None
    for n in pkt.devs:
        if pkt.engine(n).findtext("TYPE") == "Router":
            m = pkt.engine(n).find("MODULE/SLOT/MODULE/SLOT/MODULE")
            if m is not None and m.findtext("MODEL") == "HWIC-2T":
                molde = m; break
    if molde is None:
        sys.exit("El .pkt base necesita al menos un router con HWIC-2T para copiar el modulo")

    con_serial = {c[k] for c in cables if c["tipo"] == "Serial DCE" for k in ("a", "b")}
    for n in sorted(con_serial):
        if pkt.agregar_hwic(n, molde):
            print(f"HWIC-2T agregado a {n}")

    for c in cables:
        if pkt.cable(c["a"], c["pa"], c["b"], c["pb"], c["tipo"]):
            print(f"Cable {c['red']}: {c['a']} {c['pa']} -> {c['b']} {c['pb']}")

    for router, d in lans.items():
        equipos = [NOMBRES_PKT.get(e, e) for e, _ in d["equipos"]]
        if router == "Brimstone":
            pkt.cable("Brimstone", "GigabitEthernet0/0", equipos[0], "FastEthernet0", "Copper Cross-Over")
        else:
            sw = f"{router} SW"
            if pkt.cable(router, "GigabitEthernet0/0", sw, "FastEthernet0/1", "Copper Straight-Through"):
                print(f"LAN {router}: router -> {sw}")
            for i, eq in enumerate(equipos):
                pkt.cable(eq, "FastEthernet0", sw, f"FastEthernet0/{i + 2}", "Copper Straight-Through")
        for (eq, ip), nombre in zip(d["equipos"], equipos):
            if pkt.ip_equipo(nombre, ip, d["mask"], d["gw"]):
                print(f"Equipo {nombre}: {ip or 'DHCP'}")

    for n in pkt.devs:
        if pkt.engine(n).findtext("TYPE") == "Router" and (ROOT / "configs" / f"{n}.txt").exists():
            if pkt.configurar_router(n, a.ibgp_as40):
                print(f"Router {n} configurado desde configs/{n}.txt")

    xml = ET.tostring(pkt.root, encoding="unicode").encode("utf-8")
    Path(a.salida).write_bytes(cifrar(xml))
    print(f"Listo: {a.salida}")


if __name__ == "__main__":
    main()

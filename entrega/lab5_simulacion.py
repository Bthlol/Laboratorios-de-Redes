#!/usr/bin/env python3
"""
Laboratorio 5 - Redes de Computadores
Simulacion de una topologia de APs en forma de lemniscata con Mininet-WiFi.

Uso:
    sudo python3 lab5_simulacion.py [opciones]      (grupo 14 por defecto)

Opciones principales:
    -g / --grupo         numero de grupo G (por defecto 14: N=8, exponente 3.9)
    --canales            base | igual | 456 | 1611  (configuracion de canales, P4)
    --interferencia      usa wmediumd en modo interferencia (recomendado para P4)
    --histeresis DB      margen para cambiar de AP (por defecto 3 dB)
    --t0                 segundos de espera antes de iniciar la movilidad (STP)
    --monitor STA[,STA]  registra 'iw dev STA-wlan0 link' en ./registros/
    --cada S             periodo (s) del registro anterior
    --iperf T            mide throughput sta2 -> sta3 desde t = T s (registros/iperf_*.txt)
    --iperf-dur S        duracion de la medicion iperf (por defecto 4 s)
    --duracion S         ejecuta S segundos sin CLI y se detiene sola
    --sin-grafico        no abre la ventana del plano
    --dry-run            solo imprime posiciones, rangos y coberturas (no necesita Mininet)
"""

import argparse
import math
import sys
import threading
import time

# ---------------------------------------------------------------------------
# 1. Parametros dependientes del grupo
# ---------------------------------------------------------------------------

# Posiciones de la tabla del enunciado (en orden de recorrido del anillo)
TABLA = {
    6: ([(-61, -43), (-130, 0), (-61, 43)],
        [(90, -45), (90, 45)]),
    7: ([(-61, -43), (-130, 0), (-61, 43)],
        [(61, -43), (130, 0), (61, 43)]),
    8: ([(-46, -37), (-113, -35), (-113, 35), (-46, 37)],
        [(61, -43), (130, 0), (61, 43)]),
    9: ([(-46, -37), (-113, -35), (-113, 35), (-46, 37)],
        [(46, -37), (113, -35), (113, 35), (46, 37)]),
}

# Canales "base": uno distinto por AP (indice = numero de AP)
CANALES_BASE = [1, 4, 7, 10, 2, 5, 8, 11, 3]

# Valores por defecto de Mininet-WiFi usados para estimar el rango
TXPOWER_AP = 14      # dBm
GANANCIA = 5         # dBi (AP y estacion)
NOISE_TH = -91       # dBm, umbral bajo el cual no hay asociacion


def frecuencia(canal):
    """Frecuencia central (GHz) de un canal de 2.4 GHz."""
    return 2.412 + 0.005 * (canal - 1)


def rango_logdistance(exp, canal):
    """Replica la formula de rango de mn_wifi/propagationModels.py (logDistance)."""
    lam = 299792458.0 / (frecuencia(canal) * 1e9)
    pl_1m = 10 * math.log10((4 * math.pi * 1.0) ** 2 / lam ** 2)
    ganancias = TXPOWER_AP + 2 * GANANCIA
    return 10 ** ((-NOISE_TH - pl_1m + ganancias) / (10 * exp))


class Topologia:
    """Calcula nodos, enlaces, canales y rutas de las estaciones."""

    def __init__(self, grupo, modo_canales='base'):
        self.G = grupo
        self.N = 6 + (grupo % 4)
        self.X = grupo % 10
        self.exp = 3.5 + self.X / 10.0

        izq, der = TABLA[self.N]
        # ap0 = central; ap1..apL = lobulo izquierdo; resto = lobulo derecho
        self.pos = {'ap0': (0, 0)}
        self.izq = ['ap%d' % (i + 1) for i in range(len(izq))]
        self.der = ['ap%d' % (len(izq) + i + 1) for i in range(len(der))]
        for nombre, p in zip(self.izq + self.der, izq + der):
            self.pos[nombre] = p
        self.aps = ['ap0'] + self.izq + self.der

        # Enlaces cableados: cada lobulo es un anillo que pasa por ap0
        self.enlaces = []
        for lobulo in (self.izq, self.der):
            anillo = ['ap0'] + lobulo + ['ap0']
            for a, b in zip(anillo, anillo[1:]):
                self.enlaces.append((a, b))

        self.adyacentes_central = [self.izq[0], self.izq[-1],
                                   self.der[0], self.der[-1]]
        self.canales = self._asignar_canales(modo_canales)
        # Rango por AP (depende levemente de la frecuencia del canal)
        self.rango = {ap: rango_logdistance(self.exp, self.canales[ap])
                      for ap in self.aps}
        self.R = max(self.rango.values())
        self._estaciones()

    def _asignar_canales(self, modo):
        canales = {ap: CANALES_BASE[i] for i, ap in enumerate(self.aps)}
        if modo == 'base':
            return canales
        # central, primer nodo de cada lobulo, ultimo nodo de cada lobulo
        tabla = {'igual': (6, 6, 6), '456': (5, 4, 6), '1611': (1, 6, 11)}
        c_cen, c_pri, c_ult = tabla[modo]
        canales['ap0'] = c_cen
        for lobulo in (self.izq, self.der):
            canales[lobulo[0]] = c_pri
            canales[lobulo[-1]] = c_ult
            # nodos intermedios (no adyacentes al central): alternan 9 y 2
            for k, ap in enumerate(lobulo[1:-1]):
                canales[ap] = (9, 2)[k % 2]
        return canales

    def _estaciones(self):
        xs_izq = [self.pos[a][0] for a in self.izq]
        xs_der = [self.pos[a][0] for a in self.der]
        margen = 15

        # sta1: estatica, interior del lobulo izquierdo (centroide del anillo)
        cx_izq = round(sum(xs_izq) / (len(xs_izq) + 1))
        cx_der = round(sum(xs_der) / (len(xs_der) + 1))
        self.sta1 = (cx_izq, 5)

        # sta2: fuera de cobertura a la izquierda -> fuera a la derecha, por y=0
        x_ini = math.floor(min(xs_izq) - self.R - margen)
        x_fin = math.ceil(max(xs_der) + self.R + margen)
        self.sta2 = ((x_ini, 0), (x_fin, 0), 40)

        # sta3: desde el simetrico del nodo derecho inferior (cuadrante sup. izq.)
        #       hasta ese nodo, en linea recta por el origen
        destino = self.pos[self.der[0]]            # nodo con y < 0
        self.sta3 = ((-destino[0], -destino[1]), destino, 45)

        # sta4: desde el origen al interior del lobulo derecho
        self.sta4 = ((0, 0), (cx_der, -5), 20)

        # sta5: recorre el eje Y entre el central y los adyacentes izquierdos
        x5 = round(self.pos[self.izq[0]][0] / 2)
        y5 = math.ceil(self.R + 10)
        self.sta5 = ((x5, -y5), (x5, y5), 70)

    # ---------------------------------------------------------------
    def ap_mas_cercano(self, p):
        return min(self.aps, key=lambda ap: math.dist(p, self.pos[ap]))

    def aps_en_rango(self, p):
        return [ap for ap in self.aps
                if math.dist(p, self.pos[ap]) <= self.rango[ap]]

    def resumen(self, t0):
        lin = []
        lin.append('Grupo G=%d -> N=%d nodos, X=%d, exponente=%.1f'
                   % (self.G, self.N, self.X, self.exp))
        lin.append('Rango estimado de cobertura: %.1f m (canal 1) a %.1f m (canal 11)'
                   % (rango_logdistance(self.exp, 1), rango_logdistance(self.exp, 11)))
        lin.append('\nPuntos de acceso:')
        for ap in self.aps:
            lin.append('  %-4s pos=%-12s canal=%-2d rango=%.1f m'
                       % (ap, self.pos[ap], self.canales[ap], self.rango[ap]))
        lin.append('Enlaces cableados: ' +
                   ', '.join('%s-%s' % e for e in self.enlaces))
        lin.append('\nEstaciones:')
        lin.append('  sta1 estatica en %s -> APs en rango: %s (AP mas cercano: %s)'
                   % (self.sta1, self.aps_en_rango(self.sta1),
                      self.ap_mas_cercano(self.sta1)))
        for nombre in ('sta2', 'sta3', 'sta4', 'sta5'):
            ini, fin, dur = getattr(self, nombre)
            lin.append('  %s %s -> %s en %d s (t=%d..%d s)'
                       % (nombre, ini, fin, dur, t0, t0 + dur))
            lin.append('       zonas recorridas: ' + self.zonas(ini, fin, dur))
        return '\n'.join(lin)

    def zonas(self, ini, fin, dur):
        """Secuencia de conjuntos de APs en rango a lo largo de la ruta."""
        tramos, previo = [], None
        for s in range(dur * 10 + 1):
            f = s / (dur * 10)
            p = (ini[0] + f * (fin[0] - ini[0]), ini[1] + f * (fin[1] - ini[1]))
            actual = tuple(self.aps_en_rango(p))
            if actual != previo:
                tramos.append('[t+%.1fs] %s' % (f * dur, '{' + ','.join(actual) + '}'))
                previo = actual
        return ' '.join(tramos)


# ---------------------------------------------------------------------------
# 2. Simulacion con Mininet-WiFi
# ---------------------------------------------------------------------------

def pos3(p, z=0):
    return '%s,%s,%s' % (p[0], p[1], z)


# Las estaciones se ubican a 1 m de altura. wmediumd calcula la perdida
# con log10(d) y no admite d = 0: sta4 parte sobre ap0 y sta3 termina
# sobre ap5, lo que impedia la asociacion. Las coordenadas (x, y) del
# plano son exactamente las del enunciado.
Z_STA = 1


class ControlTraspaso(threading.Thread):
    """Control de asociacion y traspaso de las estaciones.

    Reemplaza al de Mininet-WiFi, que no era confiable en esta topologia.
    Cada PERIODO segundos, y para cada estacion:
      * calcula el RSSI a cada AP con el modelo log-distance (el mismo que
        usa wmediumd) a partir de las posiciones actuales;
      * si la estacion esta fuera de la cobertura de su AP, se desconecta
        (perdida de enlace) y se asocia al AP con mejor senal disponible;
      * si otro AP supera al actual en al menos HISTERESIS dB, hace un
        traspaso: se desconecta del AP actual y se asocia al nuevo
        (break-before-make, como en 802.11).
    Cada evento se registra en registros/traspasos_HHMMSS.log.
    """
    PERIODO = 0.5

    def __init__(self, topo, aps, estaciones, t_inicio, histeresis, log):
        threading.Thread.__init__(self, name='controlTraspaso', daemon=True)
        self.topo, self.aps, self.estaciones = topo, aps, estaciones
        self.t_inicio, self.hist, self.log = t_inicio, histeresis, log
        self.actual = {}            # estacion -> AP asociado
        self.pendiente = {}         # estacion -> (AP, plazo)
        self.activo = True

    def rssi(self, sta, nombre_ap):
        x, y, z = (float(v) for v in sta.position[:3])
        ax, ay = self.topo.pos[nombre_ap]
        d = max(math.sqrt((x - ax) ** 2 + (y - ay) ** 2 + z ** 2), 0.1)
        canal = self.topo.canales[nombre_ap]
        lam = 299792458.0 / (frecuencia(canal) * 1e9)
        pl_1m = 10 * math.log10((4 * math.pi) ** 2 / lam ** 2)
        return TXPOWER_AP + 2 * GANANCIA - pl_1m - 10 * self.topo.exp * math.log10(d)

    def registrar(self, texto):
        t = time.time() - self.t_inicio
        with open(self.log, 'a') as f:
            f.write('t=%6.1f s  %s\n' % (t, texto))

    def enlace(self, sta):
        out, _, _ = sta.pexec('iw dev %s-wlan0 link' % sta.name)
        return out

    def desconectar(self, sta):
        sta.pexec('iw dev %s-wlan0 disconnect' % sta.name)
        fin = time.time() + 1.0
        while 'Not connected' not in self.enlace(sta) and time.time() < fin:
            time.sleep(0.05)
        try:                        # registro interno de Mininet-WiFi
            intf = sta.wintfs[0]
            if intf.associatedTo:
                intf.setDisconnected(intf.associatedTo)
        except Exception:
            pass
        self.actual.pop(sta.name, None)

    def conectar(self, sta, nombre_ap):
        ap_intf = self.aps[nombre_ap].wintfs[0]
        sta.pexec('iw dev %s-wlan0 connect %s %s'
                  % (sta.name, ap_intf.ssid, ap_intf.mac))
        self.actual[sta.name] = nombre_ap
        self.pendiente[sta.name] = (nombre_ap, time.time() + 3.0)
        try:                        # registro interno de Mininet-WiFi
            intf = sta.wintfs[0]
            intf.associatedTo = ap_intf
            intf.update_client_params(ap_intf)
        except Exception:
            pass

    def evaluar(self, sta):
        nombre = sta.name
        # 1) confirmar una asociacion en curso
        if nombre in self.pendiente:
            ap, plazo = self.pendiente[nombre]
            if 'SSID: %s-ssid' % ap in self.enlace(sta):
                del self.pendiente[nombre]
                self.registrar('%s asociada a %s' % (nombre, ap))
            elif time.time() > plazo:
                del self.pendiente[nombre]
                self.registrar('%s: fallo la asociacion a %s, se reintenta'
                               % (nombre, ap))
                self.desconectar(sta)
            return
        # 2) AP con cobertura y su senal
        x, y, z = (float(v) for v in sta.position[:3])
        senal = {}
        for ap in self.topo.aps:
            ax, ay = self.topo.pos[ap]
            if math.sqrt((x - ax) ** 2 + (y - ay) ** 2 + z ** 2) <= self.topo.rango[ap]:
                senal[ap] = self.rssi(sta, ap)
        actual = self.actual.get(nombre)
        if actual and actual not in senal:
            self.registrar('%s pierde cobertura de %s (posicion %.0f, %.0f)'
                           % (nombre, actual, x, y))
            self.desconectar(sta)
            actual = None
        if not senal:
            return
        mejor = max(senal, key=senal.get)
        if actual is None:
            self.registrar('%s se asocia a %s (%.0f dBm)'
                           % (nombre, mejor, senal[mejor]))
            self.conectar(sta, mejor)
        elif mejor != actual and senal[mejor] >= senal[actual] + self.hist:
            self.registrar('%s traspaso %s (%.0f dBm) -> %s (%.0f dBm)'
                           % (nombre, actual, senal[actual], mejor, senal[mejor]))
            self.desconectar(sta)
            self.conectar(sta, mejor)

    def run(self):
        while self.activo:
            for sta in self.estaciones:
                try:
                    self.evaluar(sta)
                except Exception as e:      # no detener el control
                    self.registrar('error con %s: %s' % (sta.name, e))
            time.sleep(self.PERIODO)


def iniciar_iperf(sta2, sta3, args, t_inicio):
    """Mide throughput sta2 -> sta3 (iperf) a partir del instante args.iperf.

    El resultado, junto con el AP y la senal de ambas estaciones antes y
    despues de la medicion, se guarda en registros/iperf_<canales>_HHMMSS.txt
    """
    import os
    from mininet.log import info
    os.makedirs('registros', exist_ok=True)
    ruta = os.path.abspath('registros/iperf_%s_%s.txt'
                           % (args.canales, time.strftime('%H%M%S')))
    sta3.cmd('iperf -s > /dev/null 2>&1 &')

    def estado(f, momento):
        t = time.time() - t_inicio
        f.write('== %s (t=%.1f s)\n' % (momento, t))
        for sta in (sta2, sta3):
            out, _, _ = sta.pexec('iw dev %s-wlan0 link' % sta.name)
            ssid = [l.strip() for l in out.splitlines() if 'SSID' in l or 'signal' in l]
            f.write('   %s: %s\n' % (sta.name, ', '.join(ssid) or 'Not connected'))

    def medir():
        time.sleep(max(t_inicio + args.iperf - time.time(), 0))
        with open(ruta, 'w') as f:
            f.write('Canales: %s | interferencia: %s | t inicio iperf: %s s | duracion: %s s\n'
                    % (args.canales, args.interferencia, args.iperf, args.iperf_dur))
            estado(f, 'antes')
            f.flush()
            out, err, _ = sta2.pexec('iperf -c 10.0.0.3 -t %s -i 1 -f m'
                                     % args.iperf_dur)
            f.write(out + err)
            estado(f, 'despues')

    threading.Thread(target=medir, daemon=True).start()
    info('*** iperf sta2 -> sta3 en t=%s s durante %s s -> %s\n'
         % (args.iperf, args.iperf_dur, ruta))


def topology(args):
    from mininet.log import info
    from mn_wifi.cli import CLI
    from mn_wifi.net import Mininet_wifi


    topo = Topologia(args.grupo, args.canales)
    t0 = args.t0

    # allAutoAssociation=False: se desactiva el control de asociacion de
    # Mininet-WiFi; lo reemplaza ControlTraspaso
    kwargs = {'allAutoAssociation': False}
    if args.interferencia:
        from mn_wifi.link import wmediumd
        from mn_wifi.wmediumdConnector import interference
        kwargs.update(link=wmediumd, wmediumd_mode=interference)
    try:
        net = Mininet_wifi(**kwargs)
    except TypeError:
        # versiones antiguas de Mininet-WiFi no tienen allAutoAssociation
        kwargs.pop('allAutoAssociation')
        net = Mininet_wifi(**kwargs)
        info('*** AVISO: esta version de Mininet-WiFi no permite desactivar '
             'su control de asociacion\n')

    info('*** Creando puntos de acceso\n')
    aps = {}
    for nombre in topo.aps:
        # failMode='standalone' + stp=True: el AP actua como switch con
        # aprendizaje y Spanning Tree, evitando tormentas por los ciclos
        aps[nombre] = net.addAccessPoint(
            nombre, ssid='%s-ssid' % nombre, mode='g',
            channel=str(topo.canales[nombre]), position=pos3(topo.pos[nombre]),
            failMode='standalone', stp=True)

    info('*** Creando estaciones\n')
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:01', ip='10.0.0.1/8',
                          position=pos3(topo.sta1, Z_STA))
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:02', ip='10.0.0.2/8',
                          position=pos3(topo.sta2[0], Z_STA))
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:03', ip='10.0.0.3/8',
                          position=pos3(topo.sta3[0], Z_STA))
    sta4 = net.addStation('sta4', mac='00:00:00:00:00:04', ip='10.0.0.4/8',
                          position=pos3(topo.sta4[0], Z_STA))
    sta5 = net.addStation('sta5', mac='00:00:00:00:00:05', ip='10.0.0.5/8',
                          position=pos3(topo.sta5[0], Z_STA))

    info('*** Modelo de propagacion: logDistance, exp=%.1f\n' % topo.exp)
    net.setPropagationModel(model='logDistance', exp=topo.exp)

    info('*** Configurando nodos\n')
    net.configureNodes()

    info('*** Enlaces cableados entre APs (lemniscata)\n')
    for a, b in topo.enlaces:
        net.addLink(aps[a], aps[b])

    if not args.sin_grafico:
        lim_x = max(abs(topo.sta2[0][0]), abs(topo.sta2[1][0])) + 20
        lim_y = max(abs(topo.sta5[0][1]), 60) + 20
        net.plotGraph(min_x=-lim_x, min_y=-lim_y, max_x=lim_x, max_y=lim_y)

    info('*** Movilidad (inicia en t=%d s)\n' % t0)
    net.startMobility(time=0)
    for sta, (ini, fin, dur) in ((sta2, topo.sta2), (sta3, topo.sta3),
                                 (sta4, topo.sta4), (sta5, topo.sta5)):
        net.mobility(sta, 'start', time=t0, position=pos3(ini, Z_STA))
        net.mobility(sta, 'stop', time=t0 + dur, position=pos3(fin, Z_STA))
    net.stopMobility(time=t0 + 71)

    info('*** Iniciando red\n')
    import time
    t_inicio = time.time()      # referencia del reloj de movilidad
    net.build()
    for ap in aps.values():
        ap.start([])        # sin controlador: los APs operan en modo standalone

    # STP: ap0 como raiz y temporizadores cortos para converger en ~8 s
    # (con los valores por defecto de 802.1D tardaria ~30 s)
    for nombre, ap in aps.items():
        prio = 4096 if nombre == 'ap0' else 32768
        ap.cmd('ovs-vsctl set Bridge %s other_config:stp-priority=%d '
               'other_config:stp-hello-time=1 other_config:stp-max-age=6 '
               'other_config:stp-forward-delay=4' % (nombre, prio))

    import os
    os.makedirs('registros', exist_ok=True)
    log_traspasos = os.path.abspath('registros/traspasos_%s.log'
                                    % time.strftime('%H%M%S'))
    control = ControlTraspaso(topo, aps, [sta1, sta2, sta3, sta4, sta5],
                              t_inicio, args.histeresis, log_traspasos)
    control.start()
    info('*** Control de traspaso: senal mas fuerte con histeresis de %s dB\n'
         '*** Eventos de asociacion en %s\n' % (args.histeresis, log_traspasos))

    info('*** Referencia de tiempo: t=0 s corresponde al instante UNIX %.3f\n'
         % t_inicio)
    monitores = [m.strip() for m in args.monitor.split(',')] if args.monitor else []
    if monitores:
        import os
        os.makedirs('registros', exist_ok=True)
        hora = time.strftime('%H%M%S')
        for nombre in monitores:
            sta = net.get(nombre)
            log = os.path.abspath('registros/%s_cada%ss_%s.log'
                                  % (nombre, args.cada, hora))
            sta.cmd("sh -c 'I=%d; while true; do "
                    "echo \"== t=$(( $(date +%%s) - I ))s\"; "
                    "iw dev %s-wlan0 link; sleep %s; done' > %s 2>&1 & "
                    "echo $! > /tmp/lab5_monitor_%s.pid"
                    % (int(t_inicio), nombre, args.cada, log, nombre))
            info('*** Registrando enlace de %s cada %s s en %s\n'
                 % (nombre, args.cada, log))

    info('\n' + topo.resumen(t0) + '\n\n')
    if args.iperf is not None:
        iniciar_iperf(sta2, sta3, args, t_inicio)

    if args.duracion:
        espera = t_inicio + args.duracion - time.time()
        info('*** Ejecucion sin CLI: se detiene en t=%s s\n' % args.duracion)
        time.sleep(max(espera, 0))
    else:
        info('*** Iniciando CLI de Mininet-WiFi\n')
        CLI(net)

    info('*** Deteniendo red\n')
    control.activo = False
    if not args.sin_grafico:
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except Exception:
            pass
    for nombre in monitores:
        net.get(nombre).cmd('kill $(cat /tmp/lab5_monitor_%s.pid) 2>/dev/null'
                            % nombre)
    net.stop()
    # Salida directa: evita el error de matplotlib/Tkinter al cerrar el
    # plano desde un hilo secundario (no afecta la simulacion)
    import os
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


def main():
    p = argparse.ArgumentParser(description='Laboratorio 5 - Mininet-WiFi')
    p.add_argument('-g', '--grupo', type=int, default=14)
    p.add_argument('--canales', choices=['base', 'igual', '456', '1611'],
                   default='base')
    p.add_argument('--interferencia', action='store_true')
    p.add_argument('--histeresis', type=float, default=3.0)
    p.add_argument('--iperf', type=float, metavar='T')
    p.add_argument('--iperf-dur', type=float, default=4)
    p.add_argument('--duracion', type=float, metavar='S')
    p.add_argument('--t0', type=int, default=15)
    p.add_argument('--monitor', metavar='STA')
    p.add_argument('--cada', type=float, default=5)
    p.add_argument('--sin-grafico', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    if args.dry_run:
        print(Topologia(args.grupo, args.canales).resumen(args.t0))
        return

    from mininet.log import setLogLevel
    setLogLevel('info')
    topology(args)


if __name__ == '__main__':
    main()

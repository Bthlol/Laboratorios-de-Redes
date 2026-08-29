package session

import (
	"net"
	"strings"
	"testing"
	"time"
)

// --- dobles de prueba -------------------------------------------------------

// connFalsa reemplaza un socket real. Embebe net.Conn (que queda en nil) para
// satisfacer la interfaz completa sin escribir sus 7 métodos: sólo redefinimos
// los dos que el Manager usa de verdad.
type connFalsa struct {
	net.Conn
	escrito strings.Builder
	cerrada bool
}

func (c *connFalsa) Write(p []byte) (int, error) { return c.escrito.Write(p) }
func (c *connFalsa) Close() error                { c.cerrada = true; return nil }

// storeFalso reemplaza sesiones.csv: anota las llamadas en memoria, sin disco.
type storeFalso struct {
	expirados []string
}

func (s *storeFalso) Registrar(ses *Sesion) error                         { return nil }
func (s *storeFalso) ActualizarHeartbeat(token string, t time.Time) error { return nil }
func (s *storeFalso) MarcarExpirada(token string) error {
	s.expirados = append(s.expirados, token)
	return nil
}

// relojFalso permite avanzar el tiempo a voluntad, sin esperas reales.
type relojFalso struct{ t time.Time }

func (r *relojFalso) ahora() time.Time        { return r.t }
func (r *relojFalso) avanzar(d time.Duration) { r.t = r.t.Add(d) }

func managerDePrueba(t *testing.T) (*Manager, *storeFalso, *relojFalso) {
	t.Helper()
	store := &storeFalso{}
	reloj := &relojFalso{t: time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC)}
	m := NewManager(store)
	m.ahora = reloj.ahora
	return m, store, reloj
}

func crearSesion(t *testing.T, m *Manager) (*Sesion, *connFalsa) {
	t.Helper()
	conn := &connFalsa{}
	ses, err := m.Crear("seba", conn)
	if err != nil {
		t.Fatalf("Crear: %v", err)
	}
	return ses, conn
}

// --- las tres reglas de expiración ------------------------------------------

func TestExpiraSiNoLlegaElPrimerLatido(t *testing.T) {
	m, store, reloj := managerDePrueba(t)
	ses, conn := crearSesion(t, m)

	reloj.avanzar(TimePrimerLatido + time.Second)
	m.ExpirarVencidas()

	if _, err := m.Validar(ses.Token); err != ErrSesionExpirada {
		t.Errorf("Validar = %v, esperaba ErrSesionExpirada", err)
	}
	if !conn.cerrada {
		t.Error("el socket TCP no se cerró")
	}
	if len(store.expirados) != 1 {
		t.Errorf("se marcaron %d sesiones en el CSV, esperaba 1", len(store.expirados))
	}
}

func TestNoExpiraDentroDeLaGracia(t *testing.T) {
	m, _, reloj := managerDePrueba(t)
	ses, _ := crearSesion(t, m)

	reloj.avanzar(TimePrimerLatido - time.Second)
	m.ExpirarVencidas()

	if _, err := m.Validar(ses.Token); err != nil {
		t.Errorf("la sesión murió antes de tiempo: %v", err)
	}
}

func TestExpiraTrasPerderElHeartbeat(t *testing.T) {
	m, _, reloj := managerDePrueba(t)
	ses, conn := crearSesion(t, m)

	reloj.avanzar(10 * time.Second)
	if err := m.TocarHeartbeat(ses.Token); err != nil {
		t.Fatal(err)
	}

	reloj.avanzar(TimeoutHeartbeat + time.Second)
	m.ExpirarVencidas()

	if _, err := m.Validar(ses.Token); err != ErrSesionExpirada {
		t.Errorf("Validar = %v, esperaba ErrSesionExpirada", err)
	}
	if !conn.cerrada {
		t.Error("el socket TCP no se cerró")
	}
}

func TestLatirCadaTresSegundosMantieneLaSesion(t *testing.T) {
	m, _, reloj := managerDePrueba(t)
	ses, _ := crearSesion(t, m)

	// 100 latidos de 3s = 5 minutos, el ritmo real del cliente.
	for i := 0; i < 100; i++ {
		reloj.avanzar(3 * time.Second)
		if err := m.TocarHeartbeat(ses.Token); err != nil {
			t.Fatalf("latido %d rechazado: %v", i, err)
		}
		m.ExpirarVencidas()
	}

	if _, err := m.Validar(ses.Token); err != nil {
		t.Errorf("la sesión murió pese a latir puntual: %v", err)
	}
}

func TestElTTLVenceAunqueElClienteSigaLatiendo(t *testing.T) {
	m, _, reloj := managerDePrueba(t)
	ses, _ := crearSesion(t, m)

	// 200 latidos de 3s = 10 minutos exactos, siempre puntual.
	for i := 0; i < 200; i++ {
		reloj.avanzar(3 * time.Second)
		if err := m.TocarHeartbeat(ses.Token); err != nil {
			t.Fatalf("latido %d rechazado: %v", i, err)
		}
	}
	reloj.avanzar(time.Second) // un segundo más y el TTL absoluto manda
	m.ExpirarVencidas()

	if _, err := m.Validar(ses.Token); err != ErrSesionExpirada {
		t.Errorf("Validar = %v, esperaba ErrSesionExpirada", err)
	}
}

func TestElWatchdogNoRevocaDosVecesLaMismaSesion(t *testing.T) {
	m, store, reloj := managerDePrueba(t)
	crearSesion(t, m)

	reloj.avanzar(TimePrimerLatido + time.Second)
	m.ExpirarVencidas()
	m.ExpirarVencidas() // el watchdog corre cada 5s
	m.ExpirarVencidas()

	if len(store.expirados) != 1 {
		t.Errorf("sesiones.csv se reescribió %d veces, esperaba 1", len(store.expirados))
	}
}

// --- tokens -----------------------------------------------------------------

func TestValidarTokenInexistente(t *testing.T) {
	m, _, _ := managerDePrueba(t)

	if _, err := m.Validar("no-existe"); err != ErrTokenInvalido {
		t.Errorf("Validar = %v, esperaba ErrTokenInvalido", err)
	}
}

func TestTokensUnicosEnElMismoInstante(t *testing.T) {
	m, _, _ := managerDePrueba(t) // reloj congelado: el peor caso posible
	a, _ := crearSesion(t, m)
	b, _ := crearSesion(t, m)

	if a.Token == b.Token {
		t.Errorf("dos sesiones del mismo instante comparten token %q", a.Token)
	}
}

// --- broadcast y logout implícito -------------------------------------------

func TestBroadcastExcluyeAlRemitente(t *testing.T) {
	m, _, _ := managerDePrueba(t)
	connA, connB := &connFalsa{}, &connFalsa{}
	if _, err := m.Crear("ana", connA); err != nil {
		t.Fatal(err)
	}
	if _, err := m.Crear("beto", connB); err != nil {
		t.Fatal(err)
	}

	m.Broadcast("ana", "hola a todos")

	if got := connA.escrito.String(); got != "" {
		t.Errorf("el remitente recibió su propio mensaje: %q", got)
	}
	if got := connB.escrito.String(); got != "INCOMING ana hola a todos\n" {
		t.Errorf("connB recibió %q", got)
	}
}

func TestExpirarPorConnRevocaLaSesion(t *testing.T) {
	m, store, _ := managerDePrueba(t)
	ses, conn := crearSesion(t, m)

	m.ExpirarPorConn(conn) // el cliente cerró el socket

	if _, err := m.Validar(ses.Token); err != ErrSesionExpirada {
		t.Errorf("Validar = %v, esperaba ErrSesionExpirada", err)
	}
	if len(store.expirados) != 1 {
		t.Errorf("se marcaron %d sesiones en el CSV, esperaba 1", len(store.expirados))
	}
}

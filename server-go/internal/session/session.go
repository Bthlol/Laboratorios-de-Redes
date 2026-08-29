// Paquete session: propiedad de Persona B(Seba).
//
// Este es el ESTADO COMPARTIDO entre el servidor TCP y el servidor UDP:
// mapa de token -> sesión, con su socket TCP asociado y timestamps de
// heartbeat. Por eso vive en un paquete propio con su propio mutex,
// y tanto tcpserver como udpserver solo lo consumen a través de estos
// métodos (nunca acceden al mapa directamente).
package session

import (
	"errors"
	"fmt"
	"net"
	"sync"
	"time"
)

// Plazos definidos por el enunciado.
const (
	TTLToken         = 10 * time.Minute // vida máxima del token
	TimePrimerLatido = 30 * time.Second // plazo para el primer HEARTBEAT
	TimeoutHeartbeat = 60 * time.Second // sin latidos después del primero
)

// Errores que tcpserver traduce a las respuestas del protocolo.
var (
	ErrTokenInvalido  = errors.New("INVALID TOKEN")
	ErrSesionExpirada = errors.New("SESSION EXPIRED")
)

type Estado string

const (
	Activo   Estado = "ACTIVO"
	Expirado Estado = "EXPIRADO"
)

type Sesion struct {
	Token           string
	Username        string
	Conn            net.Conn // socket TCP del cliente, para poder cerrarlo/escribirle
	CreadaEn        time.Time
	UltimoHeartbeat time.Time
	PrimerLatido    bool
	Estado          Estado
}

// SesionesStore es lo que este paquete necesita para persistir sesiones.csv.
// Al declararlo acá y no depender de storage, session compila y se prueba solo.
type SesionesStore interface {
	Registrar(s *Sesion) error
	ActualizarHeartbeat(token string, t time.Time) error
	MarcarExpirada(token string) error
}

type Manager struct {
	mu       sync.Mutex
	sesiones map[string]*Sesion  // token -> sesión
	porConn  map[net.Conn]string // socket -> token, para el logout implícito
	store    SesionesStore
	ahora    func() time.Time // inyectable: en los tests avanzamos el reloj a voluntad
	seq      uint64           // evita que dos tokens del mismo instante choquen
}

func NewManager(store SesionesStore) *Manager {
	return &Manager{
		sesiones: make(map[string]*Sesion),
		porConn:  make(map[net.Conn]string),
		store:    store,
		ahora:    time.Now,
	}
}

// Crear registra una sesión nueva para un usuario recién autenticado.
func (m *Manager) Crear(username string, conn net.Conn) (*Sesion, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	ahora := m.ahora()
	m.seq++
	s := &Sesion{
		Token:           fmt.Sprintf("%x%x", ahora.UnixNano(), m.seq),
		Username:        username,
		Conn:            conn,
		CreadaEn:        ahora,
		UltimoHeartbeat: ahora,
		Estado:          Activo,
	}
	m.sesiones[s.Token] = s
	m.porConn[conn] = s.Token
	return s, m.store.Registrar(s)
}

// Validar comprueba que el token exista, esté activo y no haya superado su TTL.
func (m *Manager) Validar(token string) (*Sesion, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	s, ok := m.sesiones[token]
	if !ok {
		return nil, ErrTokenInvalido
	}
	if s.Estado != Activo {
		return nil, ErrSesionExpirada
	}
	if m.ahora().Sub(s.CreadaEn) > TTLToken {
		m.expirar(s)
		return nil, ErrSesionExpirada
	}
	return s, nil
}

// TocarHeartbeat actualiza el registro de actividad de un token.
func (m *Manager) TocarHeartbeat(token string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	s, ok := m.sesiones[token]
	if !ok || s.Estado != Activo {
		return ErrTokenInvalido
	}
	s.UltimoHeartbeat = m.ahora()
	s.PrimerLatido = true
	return m.store.ActualizarHeartbeat(token, s.UltimoHeartbeat)
}

// ExpirarVencidas aplica las tres reglas de expiración del enunciado.
// La llama periódicamente el watchdog de udpserver.
func (m *Manager) ExpirarVencidas() {
	m.mu.Lock()
	defer m.mu.Unlock()

	ahora := m.ahora()
	for _, s := range m.sesiones {
		if s.Estado != Activo {
			continue
		}
		switch {
		case ahora.Sub(s.CreadaEn) > TTLToken:
			m.expirar(s)
		case !s.PrimerLatido && ahora.Sub(s.CreadaEn) > TimePrimerLatido:
			m.expirar(s)
		case s.PrimerLatido && ahora.Sub(s.UltimoHeartbeat) > TimeoutHeartbeat:
			m.expirar(s)
		}
	}
}

// ExpirarPorConn cierra la sesión de un socket que se cayó (logout implícito).
func (m *Manager) ExpirarPorConn(conn net.Conn) {
	m.mu.Lock()
	defer m.mu.Unlock()

	token, ok := m.porConn[conn]
	if !ok {
		return
	}
	if s, ok := m.sesiones[token]; ok {
		m.expirar(s)
	}
}

// Broadcast retransmite un mensaje a todas las sesiones activas menos la del remitente.
func (m *Manager) Broadcast(remitente, mensaje string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	linea := fmt.Sprintf("INCOMING %s %s\n", remitente, mensaje)
	for _, s := range m.sesiones {
		if s.Username == remitente || s.Estado != Activo {
			continue
		}
		s.Conn.Write([]byte(linea))
	}
}

// expirar revoca una sesión: cierra su socket, la saca de la lista de difusión
// y la marca en sesiones.csv. La sesión NO se borra del mapa: queda con
// Estado=Expirado para que un MSG posterior reciba ERROR SESSION EXPIRED y no
// ERROR INVALID TOKEN (prueba 8 del enunciado).
// Asume que el mutex YA está tomado por quien la llama.
func (m *Manager) expirar(s *Sesion) {
	s.Estado = Expirado
	delete(m.porConn, s.Conn)
	if s.Conn != nil {
		s.Conn.Close()
	}
	m.store.MarcarExpirada(s.Token)
}

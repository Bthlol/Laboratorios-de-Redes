// Paquete session: propiedad de Persona B.
//
// Este es el ESTADO COMPARTIDO entre el servidor TCP y el servidor UDP:
// mapa de token -> sesión, con su socket TCP asociado y timestamps de
// heartbeat. Por eso vive en un paquete propio con su propio mutex,
// y tanto tcpserver como udpserver solo lo consumen a través de estos
// métodos (nunca acceden al mapa directamente).
package session

import (
	"net"
	"sync"
	"time"
)

type Estado string

const (
	Activa    Estado = "ACTIVA"
	Expirada  Estado = "EXPIRADA"
)

type Sesion struct {
	Token           string
	Username        string
	Conn            net.Conn // socket TCP del cliente, para poder cerrarlo/escribirle
	UDPPort         int
	CreadaEn        time.Time
	UltimoHeartbeat time.Time
	PrimerLatido    bool
	Estado          Estado
}

type Manager struct {
	mu       sync.Mutex
	sesiones map[string]*Sesion // token -> sesión
}

func NewManager() *Manager {
	return &Manager{sesiones: make(map[string]*Sesion)}
}

// TODO(Persona B):
//   - Crear(username string, conn net.Conn, udpPort int) *Sesion
//       genera token único (paquete crypto/rand o similar), guarda en sesiones.csv
//       vía storage.CSVStore (reutilizar el de Persona A), Estado=Activa
//   - Validar(token string) (*Sesion, error)
//       existe? Estado==Activa? CreadaEn + 10min no vencido? -> si no, ERROR SESSION EXPIRED / INVALID TOKEN
//   - TocarHeartbeat(token string)
//       set UltimoHeartbeat=now, PrimerLatido=true
//   - Expirar(token string)
//       Estado=Expirada, cerrar Conn, quitar del mapa de broadcast, marcar en sesiones.csv
//   - Broadcast(remitente string, mensaje string)
//       recorrer sesiones activas != remitente, escribir "INCOMING <user> <msg>\n" a cada Conn
//   - Watchdog() (goroutine con time.Ticker, ver watchdog.go)

func (m *Manager) Lock()   { m.mu.Lock() }
func (m *Manager) Unlock() { m.mu.Unlock() }

// Paquete udpserver: propiedad de Persona B.
//
// Componente 3: recibe HEARTBEAT <token> y corre el watchdog que revisa
// periódicamente sesiones.csv / el mapa en memoria para expirar tokens
// (30s sin primer latido, 60s sin heartbeat, 10min TTL absoluto).
package udpserver

import (
	"net"
	"strings"
	"time"

	"lab1-grupo14/server/internal/session"
)

type Server struct {
	Addr     string
	Sessions *session.Manager
}

func (s *Server) ListenAndServe() error {
	addr, err := net.ResolveUDPAddr("udp", s.Addr)
	if err != nil {
		return err
	}
	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		return err
	}
	defer conn.Close()

	go s.watchdog() // rutina en segundo plano, TODO(B) implementar abajo

	buf := make([]byte, 1024)
	for {
		n, _, err := conn.ReadFromUDP(buf)
		if err != nil {
			continue
		}
		msg := strings.TrimSpace(string(buf[:n]))
		fields := strings.SplitN(msg, " ", 2)
		if len(fields) == 2 && fields[0] == "HEARTBEAT" {
			token := fields[1]
			// TODO(B): s.Sessions.TocarHeartbeat(token)
			_ = token
		}
	}
}

// watchdog revisa cada cierto intervalo (p.ej. 5s) todas las sesiones activas.
func (s *Server) watchdog() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		// TODO(B): recorrer s.Sessions (con Lock/Unlock):
		//   - !PrimerLatido && now-CreadaEn > 30s        -> Expirar
		//   - PrimerLatido && now-UltimoHeartbeat > 60s  -> Expirar
		//   - now-CreadaEn > 10min                        -> Expirar (TTL absoluto)
	}
}

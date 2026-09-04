// Paquete udpserver recibe los latidos HEARTBEAT <token> y ejecuta el
// watchdog que revisa periódicamente el mapa de sesiones en memoria para
// expirar los tokens vencidos (30s sin primer latido, 60s sin heartbeat,
// 10min de TTL absoluto). A diferencia de TCP, UDP no maneja conexiones:
// un único socket recibe los datagramas de todos los clientes.
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

	go s.watchdog()

	buf := make([]byte, 1024)
	for {
		n, _, err := conn.ReadFromUDP(buf)
		if err != nil {
			continue
		}
		msg := strings.TrimSpace(string(buf[:n]))
		fields := strings.SplitN(msg, " ", 2)
		if len(fields) == 2 && fields[0] == "HEARTBEAT" {
			s.Sessions.TocarHeartbeat(fields[1])
		}
	}
}

// watchdog revisa periódicamente las sesiones y revoca las que vencieron.
// Las reglas viven en session.Manager, que es quien tiene el mutex del mapa.
func (s *Server) watchdog() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		s.Sessions.ExpirarVencidas()
	}
}

// Paquete tcpserver: propiedad de Seba.
//
// Componente 2: LOGIN, MSG/broadcast. Cada conexión corre en su propia
// goroutine (concurrencia nativa de Go). El estado compartido vive en session.Manager; la
// persistencia en CSV se consume a través de las interfaces de abajo (de Benja) para persistir.
package tcpserver

import (
	"bufio"
	"fmt"
	"net"
	"strings"

	"lab1-grupo14/server/internal/session"
)

// Usuarios e Historial son lo que este paquete necesita del storage de Benja.
// Al declararlas acá, tcpserver compila y se prueba sin esperar su implementación.
type Usuarios interface {
	ValidateCredentials(username, password string) bool
}

type Historial interface {
	AppendMensaje(username, mensaje string) error
}

type Server struct {
	Addr      string
	Sessions  *session.Manager
	Usuarios  Usuarios
	Historial Historial
	PuertoUDP int // el que se le informa al cliente en la respuesta del LOGIN
}

func (s *Server) ListenAndServe() error {
	ln, err := net.Listen("tcp", s.Addr)
	if err != nil {
		return err
	}
	defer ln.Close()
	for {
		conn, err := ln.Accept()
		if err != nil {
			continue
		}
		go s.handleConn(conn)
	}
}

func (s *Server) handleConn(conn net.Conn) {
	defer conn.Close()
	defer s.Sessions.ExpirarPorConn(conn) // logout implícito al caerse el socket

	reader := bufio.NewReader(conn)
	for {
		linea, err := reader.ReadString('\n') // delimitador \n según el enunciado
		if err != nil {
			return
		}
		campos := strings.SplitN(strings.TrimSpace(linea), " ", 3)
		switch campos[0] {
		case "LOGIN":
			s.login(conn, campos)
		case "MSG":
			s.mensaje(conn, campos)
		}
	}
}

// login valida credenciales contra usuarios.csv y abre una sesión.
func (s *Server) login(conn net.Conn, campos []string) {
	if len(campos) != 3 || !s.Usuarios.ValidateCredentials(campos[1], campos[2]) {
		fmt.Fprint(conn, "ERROR INVALID CREDENTIALS\n")
		return
	}
	ses, err := s.Sessions.Crear(campos[1], conn)
	if err != nil {
		fmt.Fprint(conn, "ERROR INVALID CREDENTIALS\n")
		return
	}
	fmt.Fprintf(conn, "OK %s %d\n", ses.Token, s.PuertoUDP)
}

// mensaje valida la sesión, persiste el mensaje y lo retransmite al resto.
func (s *Server) mensaje(conn net.Conn, campos []string) {
	if len(campos) != 3 {
		fmt.Fprint(conn, "ERROR INVALID TOKEN\n")
		return
	}
	ses, err := s.Sessions.Validar(campos[1])
	if err != nil {
		fmt.Fprintf(conn, "ERROR %s\n", err)
		return
	}
	if err := s.Historial.AppendMensaje(ses.Username, campos[2]); err != nil {
		return
	}
	fmt.Fprint(conn, "ACK\n")
	s.Sessions.Broadcast(ses.Username, campos[2])
}

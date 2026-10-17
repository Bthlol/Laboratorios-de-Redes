// Persistencia de usuarios.csv: registro y validación de credenciales.
//
// A diferencia de sesiones.csv, este archivo sólo crece (nunca se
// modifican filas existentes), así que no necesita el patrón de
// "leer todo -> pisar la fila -> reescribir todo completo" que usa
// session.CSVSesiones. Aun así se mantiene en un tipo propio, con su
// propio mutex, siguiendo el mismo criterio aplicado en sesiones.csv:
// cada CSV que se modifica desde más de una goroutine vive en su propio
// archivo con un único punto de bloqueo, para que nunca compitan dos
// mutex sobre el mismo archivo.
package storage

import (
	"encoding/csv"
	"errors"
	"os"
	"sync"
	"time"
)

const (
	colUsername = iota
	colPassword
	colFechaRegistro
)

var cabeceraUsuarios = []string{"username", "password", "fecha_registro"}

var ErrUsuarioExistente = errors.New("usuario ya registrado")

type UsuariosStore struct {
	mu   sync.Mutex
	ruta string
}

func NewUsuariosStore(ruta string) (*UsuariosStore, error) {
	s := &UsuariosStore{ruta: ruta}
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, err := os.Stat(ruta); os.IsNotExist(err) {
		return s, s.escribir([][]string{cabeceraUsuarios})
	}
	return s, nil
}

// RegisterUser valida existencia y agrega la fila en una sola sección
// crítica, para que dos registros concurrentes del mismo username no
// se cuelen ambos entre el chequeo y la escritura (TOCTOU).
func (s *UsuariosStore) RegisterUser(username, password string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	filas, err := s.leer()
	if err != nil {
		return err
	}
	for _, fila := range filas {
		if len(fila) == len(cabeceraUsuarios) && fila[colUsername] == username {
			return ErrUsuarioExistente
		}
	}
	filas = append(filas, []string{username, password, time.Now().Format(time.RFC3339)})
	return s.escribir(filas)
}

// UserExists se deja como utilidad aparte por si se necesita fuera del
// flujo de registro (p.ej. validaciones futuras); RegisterUser NO la
// reutiliza para evitar dos lecturas separadas del archivo.
func (s *UsuariosStore) UserExists(username string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	filas, err := s.leer()
	if err != nil {
		return false
	}
	for _, fila := range filas {
		if len(fila) == len(cabeceraUsuarios) && fila[colUsername] == username {
			return true
		}
	}
	return false
}

// ValidateCredentials satisface la interfaz tcpserver.Usuarios, consumida
// por el servidor TCP al procesar el comando LOGIN.
func (s *UsuariosStore) ValidateCredentials(username, password string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	filas, err := s.leer()
	if err != nil {
		return false
	}
	for _, fila := range filas {
		if len(fila) == len(cabeceraUsuarios) && fila[colUsername] == username {
			return fila[colPassword] == password
		}
	}
	return false
}

func (s *UsuariosStore) leer() ([][]string, error) {
	f, err := os.Open(s.ruta)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return csv.NewReader(f).ReadAll()
}

func (s *UsuariosStore) escribir(filas [][]string) error {
	f, err := os.Create(s.ruta)
	if err != nil {
		return err
	}
	defer f.Close()
	w := csv.NewWriter(f)
	if err := w.WriteAll(filas); err != nil {
		return err
	}
	return w.Error()
}

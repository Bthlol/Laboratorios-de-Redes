// Persistencia de sesiones.csv: implementación de SesionesStore.
//
// A diferencia de usuarios.csv e historial.csv (que sólo crecen), acá hay que
// modificar filas existentes: el heartbeat cambia cada 3 segundos y el estado
// pasa a EXPIRADO. Modificar una fila de un CSV obliga a reescribir el archivo
// completo, y eso se serializa con un mutex porque el servidor UDP y el
// watchdog escriben desde goroutines distintas.
package session

import (
	"encoding/csv"
	"os"
	"sync"
	"time"
)

// Columnas de sesiones.csv, en el orden que exige el enunciado.
const (
	colToken = iota
	colUsername
	colCreacion
	colUltimoHeartbeat
	colEstado
)

var cabeceraSesiones = []string{
	"token", "username", "timestamp_creacion", "timestamp_ultimo_heartbeat", "estado",
}

type CSVSesiones struct {
	mu   sync.Mutex
	ruta string
}

func NewCSVSesiones(ruta string) (*CSVSesiones, error) {
	s := &CSVSesiones{ruta: ruta}
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, err := os.Stat(ruta); os.IsNotExist(err) {
		return s, s.escribir([][]string{cabeceraSesiones})
	}
	return s, nil
}

func (s *CSVSesiones) Registrar(ses *Sesion) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	filas, err := s.leer()
	if err != nil {
		return err
	}
	filas = append(filas, []string{
		ses.Token,
		ses.Username,
		ses.CreadaEn.Format(time.RFC3339),
		ses.UltimoHeartbeat.Format(time.RFC3339),
		string(ses.Estado),
	})
	return s.escribir(filas)
}

func (s *CSVSesiones) ActualizarHeartbeat(token string, t time.Time) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.actualizar(token, colUltimoHeartbeat, t.Format(time.RFC3339))
}

func (s *CSVSesiones) MarcarExpirada(token string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.actualizar(token, colEstado, string(Expirado))
}

// actualizar cambia una columna de la fila del token dado.
// Los tres helpers de abajo asumen que el mutex YA está tomado.
func (s *CSVSesiones) actualizar(token string, columna int, valor string) error {
	filas, err := s.leer()
	if err != nil {
		return err
	}
	for i, fila := range filas {
		if len(fila) == len(cabeceraSesiones) && fila[colToken] == token {
			filas[i][columna] = valor
			return s.escribir(filas)
		}
	}
	return nil // el token no está en el archivo: no hay nada que actualizar
}

func (s *CSVSesiones) leer() ([][]string, error) {
	f, err := os.Open(s.ruta)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return csv.NewReader(f).ReadAll()
}

func (s *CSVSesiones) escribir(filas [][]string) error {
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

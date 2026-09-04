// Persistencia de historial.csv: mensajes enviados por los clientes.
//
// Sólo crece (append-only), igual que usuarios.csv: nunca se modifica
// una fila ya escrita, así que basta un mutex simple sin el patrón de
// reescritura completa que usa session.CSVSesiones.
package storage

import (
	"encoding/csv"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"
)

var cabeceraHistorial = []string{"timestamp", "username", "mensaje"}

type HistorialStore struct {
	mu   sync.Mutex
	ruta string
}

func NewHistorialStore(ruta string) (*HistorialStore, error) {
	s := &HistorialStore{ruta: ruta}
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, err := os.Stat(ruta); os.IsNotExist(err) {
		return s, s.escribirCabecera()
	}
	return s, nil
}

// AppendMensaje satisface la interfaz tcpserver.Historial, consumida por
// el servidor TCP al procesar el comando MSG. El timestamp se genera acá
// adentro, en time.RFC3339 (mismo formato usado en sesiones.csv), para
// que los tres CSV queden consistentes entre sí.
func (s *HistorialStore) AppendMensaje(username, mensaje string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	f, err := os.OpenFile(s.ruta, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	fila := []string{time.Now().Format(time.RFC3339), username, mensaje}
	if err := w.Write(fila); err != nil {
		return err
	}
	w.Flush()
	return w.Error()
}

// LeerComoTexto se usa desde GET /history. Devuelve el historial en
// texto plano, una línea legible por mensaje (se omite la fila de
// cabecera del CSV).
func (s *HistorialStore) LeerComoTexto() (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	f, err := os.Open(s.ruta)
	if err != nil {
		return "", err
	}
	defer f.Close()

	filas, err := csv.NewReader(f).ReadAll()
	if err != nil {
		return "", err
	}

	var sb strings.Builder
	for i, fila := range filas {
		if i == 0 || len(fila) != len(cabeceraHistorial) {
			continue // salta la cabecera / filas corruptas
		}
		fmt.Fprintf(&sb, "[%s] %s: %s\n", fila[0], fila[1], fila[2])
	}
	return sb.String(), nil
}

func (s *HistorialStore) escribirCabecera() error {
	f, err := os.Create(s.ruta)
	if err != nil {
		return err
	}
	defer f.Close()
	w := csv.NewWriter(f)
	if err := w.Write(cabeceraHistorial); err != nil {
		return err
	}
	w.Flush()
	return w.Error()
}

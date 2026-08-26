// Paquete storage: propiedad de Persona A.
//
// Contiene TODAS las operaciones de lectura/escritura sobre los CSV
// (usuarios.csv, sesiones.csv, historial.csv), protegidas con mutex
// para evitar condiciones de carrera ante accesos concurrentes.
//
// Persona B (TCP/UDP) SOLO debe llamar a estas funciones, nunca abrir
// los archivos directamente -- así evitamos que dos personas escriban
// lógica de bloqueo distinta sobre el mismo archivo.
package storage

import (
	"encoding/csv"
	"os"
	"sync"
)

// CSVStore centraliza el acceso a un archivo CSV con su propio mutex.
type CSVStore struct {
	mu   sync.Mutex
	path string
}

func NewCSVStore(path string, header []string) (*CSVStore, error) {
	s := &CSVStore{path: path}
	if _, err := os.Stat(path); os.IsNotExist(err) {
		f, err := os.Create(path)
		if err != nil {
			return nil, err
		}
		defer f.Close()
		w := csv.NewWriter(f)
		if err := w.Write(header); err != nil {
			return nil, err
		}
		w.Flush()
	}
	return s, nil
}

func (s *CSVStore) Append(record []string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	f, err := os.OpenFile(s.path, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer f.Close()
	w := csv.NewWriter(f)
	if err := w.Write(record); err != nil {
		return err
	}
	w.Flush()
	return w.Error()
}

func (s *CSVStore) ReadAll() ([][]string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	f, err := os.Open(s.path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	r := csv.NewReader(f)
	return r.ReadAll()
}

// TODO(Persona A):
//   - UsuariosStore: NewCSVStore("usuarios.csv", []string{"username","password","fecha_registro"})
//     + UserExists(username string) bool
//     + ValidateCredentials(username, password string) bool   <- lo usa Persona B en LOGIN
//     + RegisterUser(username, password string) error          <- 400/409/201 en http.go
//   - HistorialStore: NewCSVStore("historial.csv", []string{"timestamp","username","mensaje"})
//     + AppendMensaje(username, mensaje string) error           <- lo usa Persona B en MSG
//     + LeerHistorialComoTexto() (string, error)                <- para GET /history
//
// Nota: SesionesStore (sesiones.csv) lo maneja Persona B en internal/session,
// pero reutilizando este mismo CSVStore para no duplicar lógica de locking.

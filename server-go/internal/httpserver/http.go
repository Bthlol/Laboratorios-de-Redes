// Paquete httpserver: propiedad de Persona A.
//
// Implementa el Componente 1 (Servicio HTTP de Registro) usando el
// paquete estándar net/http (permitido para el SERVIDOR; el cliente
// Python en cambio debe hablar HTTP crudo sobre sockets TCP).
package httpserver

import (
	"encoding/json"
	"net/http"

	"lab1-grupo14/server/internal/storage"
)

type Server struct {
	Usuarios *storage.CSVStore // TODO(A): reemplazar por tu UsuariosStore
	Addr     string
}

type registerRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

func (s *Server) handleRegister(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req registerRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Username == "" || req.Password == "" {
		w.WriteHeader(http.StatusBadRequest) // 400 Bad Request
		return
	}

	// TODO(Persona A):
	//   1. if s.Usuarios.UserExists(req.Username) -> w.WriteHeader(http.StatusConflict) // 409
	//   2. si no existe -> s.Usuarios.RegisterUser(req.Username, req.Password)
	//      -> w.WriteHeader(http.StatusCreated) // 201
	//   Recordar: username,password,fecha_registro en usuarios.csv
	_ = req

	w.WriteHeader(http.StatusNotImplemented)
}

func (s *Server) handleHistory(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	// TODO(Persona A): leer historial.csv y devolverlo (texto plano o JSON)
	w.WriteHeader(http.StatusNotImplemented)
}

func (s *Server) ListenAndServe() error {
	mux := http.NewServeMux()
	mux.HandleFunc("/register", s.handleRegister)
	mux.HandleFunc("/history", s.handleHistory)
	return http.ListenAndServe(s.Addr, mux)
}

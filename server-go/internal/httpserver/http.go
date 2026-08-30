// Paquete httpserver: propiedad de Benja.
//
// Implementa el Componente 1 (Servicio HTTP de Registro) usando el
// paquete estándar net/http (permitido para el SERVIDOR; el cliente
// Python en cambio debe hablar HTTP crudo sobre sockets TCP).
package httpserver

import (
	"encoding/json"
	"errors"
	"net/http"

	"lab1-grupo14/server/internal/storage"
)

type Server struct {
	Usuarios  *storage.UsuariosStore
	Historial *storage.HistorialStore
	Addr      string
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

	err := s.Usuarios.RegisterUser(req.Username, req.Password)
	switch {
	case errors.Is(err, storage.ErrUsuarioExistente):
		w.WriteHeader(http.StatusConflict) // 409
	case err != nil:
		w.WriteHeader(http.StatusInternalServerError)
	default:
		w.WriteHeader(http.StatusCreated) // 201
	}
}

func (s *Server) handleHistory(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	texto, err := s.Historial.LeerComoTexto()
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.Write([]byte(texto))
}

func (s *Server) ListenAndServe() error {
	mux := http.NewServeMux()
	mux.HandleFunc("/register", s.handleRegister)
	mux.HandleFunc("/history", s.handleHistory)
	return http.ListenAndServe(s.Addr, mux)
}

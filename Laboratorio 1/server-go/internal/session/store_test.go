package session

import (
	"path/filepath"
	"testing"
	"time"
)

func TestActualizarFilaExistente(t *testing.T) {
	ruta := filepath.Join(t.TempDir(), "sesiones.csv")
	store, err := NewCSVSesiones(ruta)
	if err != nil {
		t.Fatal(err)
	}

	creada := time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC)
	ses := &Sesion{
		Token: "abc", Username: "seba",
		CreadaEn: creada, UltimoHeartbeat: creada, Estado: Activo,
	}
	if err := store.Registrar(ses); err != nil {
		t.Fatal(err)
	}

	latido := creada.Add(3 * time.Second)
	if err := store.ActualizarHeartbeat("abc", latido); err != nil {
		t.Fatal(err)
	}
	if err := store.MarcarExpirada("abc"); err != nil {
		t.Fatal(err)
	}

	store.mu.Lock()
	filas, err := store.leer()
	store.mu.Unlock()
	if err != nil {
		t.Fatal(err)
	}

	if len(filas) != 2 {
		t.Fatalf("esperaba cabecera + 1 fila, hay %d", len(filas))
	}
	if filas[1][colUltimoHeartbeat] != latido.Format(time.RFC3339) {
		t.Errorf("heartbeat = %q", filas[1][colUltimoHeartbeat])
	}
	if filas[1][colEstado] != string(Expirado) {
		t.Errorf("estado = %q", filas[1][colEstado])
	}
}

package storage

import (
	"path/filepath"
	"strings"
	"testing"
)

func TestAppendMensajeYLeerComoTexto(t *testing.T) {
	ruta := filepath.Join(t.TempDir(), "historial.csv")
	store, err := NewHistorialStore(ruta)
	if err != nil {
		t.Fatal(err)
	}

	if err := store.AppendMensaje("benja", "hola a todos"); err != nil {
		t.Fatal(err)
	}
	if err := store.AppendMensaje("seba", "hola benja"); err != nil {
		t.Fatal(err)
	}

	texto, err := store.LeerComoTexto()
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(texto, "benja: hola a todos") {
		t.Errorf("falta el primer mensaje en el historial: %q", texto)
	}
	if !strings.Contains(texto, "seba: hola benja") {
		t.Errorf("falta el segundo mensaje en el historial: %q", texto)
	}
}

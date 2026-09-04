package storage

import (
	"errors"
	"path/filepath"
	"sync"
	"testing"
)

func TestRegisterUserYValidateCredentials(t *testing.T) {
	ruta := filepath.Join(t.TempDir(), "usuarios.csv")
	store, err := NewUsuariosStore(ruta)
	if err != nil {
		t.Fatal(err)
	}

	if err := store.RegisterUser("benja", "clave123"); err != nil {
		t.Fatal(err)
	}

	if !store.ValidateCredentials("benja", "clave123") {
		t.Error("credenciales correctas deberían validar")
	}
	if store.ValidateCredentials("benja", "otraclave") {
		t.Error("credenciales incorrectas no deberían validar")
	}
	if store.ValidateCredentials("no-existe", "clave123") {
		t.Error("usuario inexistente no debería validar")
	}
}

func TestRegisterUserDuplicado(t *testing.T) {
	ruta := filepath.Join(t.TempDir(), "usuarios.csv")
	store, err := NewUsuariosStore(ruta)
	if err != nil {
		t.Fatal(err)
	}

	if err := store.RegisterUser("benja", "clave123"); err != nil {
		t.Fatal(err)
	}
	err = store.RegisterUser("benja", "otraclave")
	if !errors.Is(err, ErrUsuarioExistente) {
		t.Fatalf("esperaba ErrUsuarioExistente, obtuve %v", err)
	}
}

// TestRegisterUserConcurrente reproduce el escenario TOCTOU: dos
// goroutines registrando el mismo username al mismo tiempo. Solo una
// debe ganar. Correr con -race para confirmar que no hay condiciones
// de carrera en la sección crítica de RegisterUser.
func TestRegisterUserConcurrente(t *testing.T) {
	ruta := filepath.Join(t.TempDir(), "usuarios.csv")
	store, err := NewUsuariosStore(ruta)
	if err != nil {
		t.Fatal(err)
	}

	var wg sync.WaitGroup
	resultados := make([]error, 10)
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			resultados[i] = store.RegisterUser("mismo-user", "clave")
		}(i)
	}
	wg.Wait()

	exitos := 0
	for _, err := range resultados {
		if err == nil {
			exitos++
		} else if !errors.Is(err, ErrUsuarioExistente) {
			t.Fatalf("error inesperado: %v", err)
		}
	}
	if exitos != 1 {
		t.Fatalf("esperaba exactamente 1 registro exitoso, hubo %d", exitos)
	}
}

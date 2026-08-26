// Punto de entrada: levanta los tres servidores en paralelo.
// Este archivo es el punto de integración entre Persona A (http+storage)
// y Persona B (tcp+udp+session) -- edítenlo juntos al final, cuando cada
// módulo ya compile por separado.
package main

import (
	"log"

	"lab1-grupo14/server/internal/httpserver"
	"lab1-grupo14/server/internal/session"
	"lab1-grupo14/server/internal/storage"
	"lab1-grupo14/server/internal/tcpserver"
	"lab1-grupo14/server/internal/udpserver"
)

func main() {
	// TODO(A): inicializar UsuariosStore / HistorialStore reales
	usuarios, err := storage.NewCSVStore("usuarios.csv", []string{"username", "password", "fecha_registro"})
	if err != nil {
		log.Fatal(err)
	}

	sessions := session.NewManager()

	httpSrv := &httpserver.Server{Usuarios: usuarios, Addr: ":8080"}
	tcpSrv := &tcpserver.Server{Addr: ":9000", Sessions: sessions}
	udpSrv := &udpserver.Server{Addr: ":9001", Sessions: sessions}

	go func() {
		log.Println("HTTP escuchando en :8080")
		log.Fatal(httpSrv.ListenAndServe())
	}()
	go func() {
		log.Println("UDP escuchando en :9001")
		log.Fatal(udpSrv.ListenAndServe())
	}()

	log.Println("TCP escuchando en :9000")
	log.Fatal(tcpSrv.ListenAndServe())
}

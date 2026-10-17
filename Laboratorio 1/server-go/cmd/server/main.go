// Punto de entrada del servidor: instancia las tres capas de persistencia
// (usuarios, historial y sesiones) y levanta los tres servicios de red
// (HTTP, TCP y UDP) en paralelo, compartiendo el mismo session.Manager.
package main

import (
	"fmt"
	"log"

	"lab1-grupo14/server/internal/httpserver"
	"lab1-grupo14/server/internal/session"
	"lab1-grupo14/server/internal/storage"
	"lab1-grupo14/server/internal/tcpserver"
	"lab1-grupo14/server/internal/udpserver"
)

func main() {
	usuarios, err := storage.NewUsuariosStore("usuarios.csv")
	if err != nil {
		log.Fatal(err)
	}
	historial, err := storage.NewHistorialStore("historial.csv")
	if err != nil {
		log.Fatal(err)
	}
	sesionesStore, err := session.NewCSVSesiones("sesiones.csv")
	if err != nil {
		log.Fatal(err)
	}

	sessions := session.NewManager(sesionesStore)

	const puertoUDP = 9001 // único puerto UDP, compartido por todas las sesiones

	httpSrv := &httpserver.Server{Usuarios: usuarios, Historial: historial, Addr: ":8080"}
	tcpSrv := &tcpserver.Server{
		Addr:      ":9000",
		Sessions:  sessions,
		Usuarios:  usuarios,
		Historial: historial,
		PuertoUDP: puertoUDP,
	}
	udpSrv := &udpserver.Server{Addr: fmt.Sprintf(":%d", puertoUDP), Sessions: sessions}

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

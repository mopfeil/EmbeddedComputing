// TCP echo server with the BSD socket API: every received line is sent back.
// Build: gcc -Wall -o tcp_echo_server tcp_echo_server.c    Run: ./tcp_echo_server 5000
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  int port = argc > 1 ? atoi(argv[1]) : 5000;

  // 1. socket(): an endpoint for IPv4 (AF_INET) and TCP (SOCK_STREAM)
  int server = socket(AF_INET, SOCK_STREAM, 0);
  if (server < 0) { perror("socket"); return 1; }
  int on = 1;   // allow restarting the server at once on the same port
  setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &on, sizeof on);

  // 2. bind(): local address and port (INADDR_ANY = all interfaces)
  struct sockaddr_in addr = {0};
  addr.sin_family = AF_INET;
  addr.sin_addr.s_addr = htonl(INADDR_ANY);
  addr.sin_port = htons(port);            // network byte order = big endian
  if (bind(server, (struct sockaddr *)&addr, sizeof addr) < 0) { perror("bind"); return 1; }

  // 3. listen(): accept connection requests, queue up to 5
  if (listen(server, 5) < 0) { perror("listen"); return 1; }
  printf("listening on port %d\n", port);

  for (;;) {
    // 4. accept(): wait for a client; returns a NEW socket for this connection
    struct sockaddr_in client_addr;
    socklen_t len = sizeof client_addr;
    int client = accept(server, (struct sockaddr *)&client_addr, &len);
    if (client < 0) { perror("accept"); continue; }
    printf("client %s:%d connected\n", inet_ntoa(client_addr.sin_addr),
           ntohs(client_addr.sin_port));

    // 5. recv()/send(): TCP is a byte stream - one recv() may return part of a
    //    message or several messages at once
    char buf[256];
    ssize_t n;
    while ((n = recv(client, buf, sizeof buf, 0)) > 0) {
      send(client, buf, n, 0);
    }
    // 6. close(): n == 0 means the client has closed its side
    printf("client disconnected\n");
    close(client);
  }
}

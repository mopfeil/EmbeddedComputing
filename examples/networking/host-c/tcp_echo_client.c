// TCP client: connect to the echo server, send a line, print the answer.
// Build: gcc -Wall -o tcp_echo_client tcp_echo_client.c
// Run:   ./tcp_echo_client 127.0.0.1 5000 "hello"
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  const char *ip = argc > 1 ? argv[1] : "127.0.0.1";
  int port = argc > 2 ? atoi(argv[2]) : 5000;
  const char *msg = argc > 3 ? argv[3] : "hello";

  int sock = socket(AF_INET, SOCK_STREAM, 0);
  struct sockaddr_in addr = {0};
  addr.sin_family = AF_INET;
  addr.sin_port = htons(port);
  inet_pton(AF_INET, ip, &addr.sin_addr);         // text -> binary address

  // connect(): the kernel performs the three-way handshake (SYN, SYN-ACK, ACK)
  if (connect(sock, (struct sockaddr *)&addr, sizeof addr) < 0) {
    perror("connect");
    return 1;
  }
  send(sock, msg, strlen(msg), 0);

  char buf[256];
  ssize_t n = recv(sock, buf, sizeof buf - 1, 0);
  if (n > 0) {
    buf[n] = '\0';
    printf("answer: %s\n", buf);
  }
  close(sock);                                    // FIN: end of the connection
  return 0;
}

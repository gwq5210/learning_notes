#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#include <cstdio>
#include <string>

static const char kHost[] = "127.0.0.1";
static const int kPort = 9999;
static const int kMaxListenCount = 2;
static const int kBufferSize = 1024;

int socket_bind(const std::string &host, int port) {
  int fd = socket(AF_INET, SOCK_STREAM, 0);
  if (fd < 0) {
    perror("socket faield");
    return fd;
  }

  struct sockaddr_in svraddr;
  memset(&svraddr, 0, sizeof(struct sockaddr_in));
  svraddr.sin_family = AF_INET;
  inet_pton(AF_INET, host.c_str(), &svraddr.sin_addr);
  svraddr.sin_port = htons(port);
  if (bind(fd, (struct sockaddr *)&svraddr, sizeof(svraddr)) < 0) {
    perror("bind error:");
    return -1;
  }

  return fd;
}

int do_read(int fd) {
  printf("read begin\n");
  char buffer[kBufferSize];
  memset(buffer, 0, sizeof(buffer));
  int nread = read(fd, buffer, kBufferSize);
  if (nread == -1) {
    perror("read error:");
    return -1;
  } else if (nread == 0) {
    fprintf(stderr, "client close!\n");
    close(fd);
  } else {
    printf("read message is: %s\n", buffer);
  }
  return nread;
}

int do_write(int fd, const std::string &msg) {
  printf("write begin, message is: %s\n", msg.c_str());
  int nwrite = write(fd, msg.c_str(), msg.size());
  if (nwrite == -1) {
    perror("write error:");
    return -1;
  }
  printf("write end, message is: %s\n", msg.c_str());
  return nwrite;
}

int handle_accept(int listenfd) {
  int client_fd;
  struct sockaddr_in client_addr;
  socklen_t addr_len;
  client_fd = accept(listenfd, (struct sockaddr *)&client_addr, &addr_len);
  if (client_fd == -1) {
    perror("accept error!");
    return -1;
  } else {
    printf("accept a new client: %s:%d\n", inet_ntoa(client_addr.sin_addr), client_addr.sin_port);
  }
  return client_fd;
}

int my_sleep(int seconds) {
  printf("sleeping for %d seconds\n", seconds);
  sleep(seconds);
  return 0;
}

int server_run() {
  int fd = socket_bind(kHost, kPort);
  listen(fd, kMaxListenCount);
  while (true) {
    my_sleep(1000000);
    int client_fd = handle_accept(fd);
    if (client_fd < 0) {
      my_sleep(1);
      continue;
    }
    do_read(client_fd);
    do_write(client_fd, "write done");
    close(client_fd);
  }
}

int main(int argc, char *argv[]) {
  server_run();
  return 0;
}
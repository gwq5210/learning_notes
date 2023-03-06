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

int main(int argc, char *argv[]) {
  int sockfd;
  struct sockaddr_in servaddr;
  sockfd = socket(AF_INET, SOCK_STREAM, 0);
  bzero(&servaddr, sizeof(servaddr));
  servaddr.sin_family = AF_INET;
  servaddr.sin_port = htons(kPort);
  inet_pton(AF_INET, kHost, &servaddr.sin_addr);
  int ret = connect(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr));
  if (ret < 0) {
    perror("connect error");
    return ret;
  }
  do_write(sockfd, "hello world");
  do_read(sockfd);

  getchar();
  close(sockfd);
  return 0;
}

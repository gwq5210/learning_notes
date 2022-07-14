#include <errno.h>
#include <unistd.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>

static const int kBufferSize = 1024 * 1024;

int main(int argc, char* argv[]) {
  if (argc < 2) {
    printf("Usage: %s filename\n", argv[0]);
    return EXIT_FAILURE;
  }
  const char* filename = argv[1];
  char buffer[kBufferSize];
  memset(buffer, 0, sizeof(buffer));
  int ret = readlink(filename, buffer, kBufferSize);
  if (ret == -1) {
    printf("Readlink failed: %s, errmsg: %s\n", filename, strerror(errno));
  } else {
    printf("Readlink succeeded: %s -> %s\n", filename, buffer);
  }
  return 0;
}
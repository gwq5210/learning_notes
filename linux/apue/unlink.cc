#include <errno.h>
#include <unistd.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>

int main(int argc, char* argv[]) {
  if (argc < 2) {
    printf("Usage: %s filename\n", argv[0]);
    return EXIT_FAILURE;
  }
  const char* filename = argv[1];
  int ret = unlink(filename);
  if (ret == -1) {
    printf("Unlink failed: %s, errmsg: %s\n", filename, strerror(errno));
  } else {
    printf("Unlink succeeded: %s\n", filename);
  }
  return 0;
}
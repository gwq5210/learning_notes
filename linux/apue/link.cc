#include <errno.h>
#include <unistd.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>

int main(int argc, char* argv[]) {
  if (argc < 3) {
    printf("Usage: %s filename target_filename\n", argv[0]);
    return EXIT_FAILURE;
  }
  const char* filename = argv[1];
  const char* target_filename = argv[2];
  int ret = link(filename, target_filename);
  if (ret == -1) {
    printf("Link failed: %s -> %s, errmsg: %s\n", filename, target_filename, strerror(errno));
  } else {
    printf("Link succeeded: %s -> %s\n", filename, target_filename);
  }
  return 0;
}
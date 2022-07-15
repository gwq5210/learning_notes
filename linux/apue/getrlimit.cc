#include <errno.h>
#include <sys/resource.h>
#include <unistd.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>

int main(int argc, char* argv[]) {
  if (argc < 1) {
    printf("Usage: %s\n", argv[0]);
    return EXIT_FAILURE;
  }
  struct rlimit nofile_limit;
  memset(&nofile_limit, 0, sizeof(nofile_limit));
  int ret = getrlimit(RLIMIT_NOFILE, &nofile_limit);
  if (ret == -1) {
    printf("getrlimit failed: %s, errmsg: %s\n", strerror(errno));
  } else {
    printf("getrlimit succeeded: soft limit %zu, hard limit %zu\n", nofile_limit.rlim_cur, nofile_limit.rlim_max);
  }
  return 0;
}
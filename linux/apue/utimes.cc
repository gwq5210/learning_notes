#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <unistd.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

void print_file_time(const std::string& filename) {
  struct stat st;
  memset(&st, 0, sizeof(struct stat));
  int ret = stat(filename.c_str(), &st);
  if (ret == -1) {
    printf("stat failed: %s, errmsg: %s\n", filename.c_str(), strerror(errno));
    return;
  }
  printf("%s: atime: %lld.%lld, mtime: %lld.%lld, ctime: %lld.%lld\n", filename.c_str(),
         st.st_atim.tv_sec, st.st_atim.tv_nsec, st.st_mtim.tv_sec, st.st_mtim.tv_nsec,
         st.st_ctim.tv_sec, st.st_ctim.tv_nsec);
}

int main(int argc, char* argv[]) {
  if (argc < 3) {
    printf("Usage: %s (futimens|utimes) filename\n", argv[0]);
    return EXIT_FAILURE;
  }
  std::string func_name = argv[1];
  const char* filename = argv[2];
  int ret = 0;
  print_file_time(filename);
  if (func_name == "futimens") {
    ret = utimensat(AT_FDCWD, filename, NULL, AT_SYMLINK_NOFOLLOW);
  } else if (func_name == "utimes") {
    ret = utimes(filename, NULL);
  }
  if (ret == -1) {
    printf("%s failed: %s, errmsg: %s\n", func_name.c_str(), filename, strerror(errno));
  } else {
    printf("%s succeeded: %s\n", func_name.c_str(), filename);
  }
  print_file_time(filename);
  return 0;
}
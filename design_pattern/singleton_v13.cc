#include <cstdio>

// version 1.3
class Singleton {
 private:
 public:
  static Singleton instance_;
  static Singleton* GetInstance() { return &instance_; }

 private:
  Singleton(){};
  ~Singleton(){};
  Singleton(const Singleton&) = delete;
  Singleton& operator=(const Singleton&) = delete;
};

// initialize defaultly
Singleton Singleton::instance_;

int main(int argc, char* argv[]) {
  Singleton* instance1 = Singleton::GetInstance();
  Singleton* instance2 = Singleton::GetInstance();
  printf("instance %p, %p\n", instance1, instance2);
  return 0;
}
#include <cstdio>

// version 1.2
class Singleton {
 private:
 public:
  static Singleton* GetInstance() {
    static Singleton instance;
    return &instance;
  }

 private:
  Singleton(){};
  ~Singleton(){};
  Singleton(const Singleton&) = delete;
  Singleton& operator=(const Singleton&) = delete;
};

int main(int argc, char* argv[]) {
  Singleton* instance1 = Singleton::GetInstance();
  Singleton* instance2 = Singleton::GetInstance();
  printf("instance %p, %p\n", instance1, instance2);
  return 0;
}
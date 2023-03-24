#include <cstdio>

// version 1.0
class Singleton {
 private:
 public:
  static Singleton* GetInstance() {
    if (instance_ == nullptr) {
      instance_ = new Singleton();
    }
    return instance_;
  }

 private:
  Singleton(){};
  ~Singleton(){};
  Singleton(const Singleton&) = delete;
  Singleton& operator=(const Singleton&) = delete;

  static Singleton* instance_;
};

// init static member
Singleton* Singleton::instance_ = nullptr;

int main(int argc, char* argv[]) {
  Singleton* instance1 = Singleton::GetInstance();
  Singleton* instance2 = Singleton::GetInstance();
  printf("instance %p, %p\n", instance1, instance2);
  return 0;
}
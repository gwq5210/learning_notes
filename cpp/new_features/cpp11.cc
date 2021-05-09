/*
 * @Author: your name
 * @Date: 2021-05-05 15:33:21
 * @LastEditTime: 2021-05-09 17:36:13
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: \learing_notes\cpp\new_features\cpp11.cc
 */
#include <cstdio>
#include <memory>

void f(int& x) {
  printf("f lvalue\n");
}

void f(int&& x) {
  printf("f rvalue\n");
}

void rvalue_reference_test() {
  int x = 0; // `x` is an lvalue of type `int`
  int& xl = x; // `xl` is an lvalue of type `int&`
  // int&& xr = x; // compiler error -- `x` is an lvalue
  int&& xr2 = 0; // `xr2` is an lvalue of type `int&&` -- binds to the rvalue temporary, `0`

  printf("%p %p %p\n", &x, &xl, &xr2);

  f(x);  // calls f(int&)
  f(xl); // calls f(int&)
  f(3);  // calls f(int&&)
  f(std::move(x)); // calls f(int&&)

  f(xr2);           // calls f(int&)
  f(std::move(xr2)); // calls f(int&& x)
}

int main(int argc, char *argv[]) {
  rvalue_reference_test();
  return 0;
}
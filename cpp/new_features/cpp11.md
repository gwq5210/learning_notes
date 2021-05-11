- [C++11语言新特性](#c11语言新特性)
  - [移动语义](#移动语义)
  - [右值引用](#右值引用)
  - [转发引用](#转发引用)
  - [可变参数模板](#可变参数模板)
  - [初始化列表](#初始化列表)
  - [静态断言](#静态断言)
  - [auto](#auto)
  - [Lambda表达式](#lambda表达式)
  - [decltype](#decltype)
  - [类型别名](#类型别名)
  - [nullptr](#nullptr)
  - [强类型枚举](#强类型枚举)
  - [属性](#属性)
  - [constexpr](#constexpr)
  - [委托构造函数](#委托构造函数)
  - [用户定义的字面量](#用户定义的字面量)
  - [显式指定虚函数的覆盖](#显式指定虚函数的覆盖)
  - [final](#final)
  - [default和delete](#default和delete)
  - [基于范围的for循环](#基于范围的for循环)
  - [用于移动语义的成员函数](#用于移动语义的成员函数)
  - [转换构造函数](#转换构造函数)
  - [显式转换函数](#显式转换函数)
  - [inline命名空间](#inline命名空间)
  - [非静态数据成员初始化](#非静态数据成员初始化)
  - [尖括号](#尖括号)
  - [引用限定的成员函数](#引用限定的成员函数)
  - [返回类型后置](#返回类型后置)
  - [noexcept](#noexcept)
  - [char32_t和char16_t](#char32_t和char16_t)
  - [原始字符串字面量](#原始字符串字面量)
- [C++11库特性](#c11库特性)
  - [std::move](#stdmove)
  - [std::forward](#stdforward)
  - [std::thread](#stdthread)
  - [std::to_string](#stdto_string)
  - [类型萃取](#类型萃取)
  - [智能指针](#智能指针)
  - [std::chrono](#stdchrono)
  - [元组](#元组)
  - [std::tie](#stdtie)
  - [std::array](#stdarray)
  - [无序容器](#无序容器)
  - [std::make_shared](#stdmake_shared)
  - [std::ref](#stdref)
  - [内存模型](#内存模型)
  - [std::async](#stdasync)
  - [std::begin/end](#stdbeginend)
  - [参考](#参考)

# C++11语言新特性

## 移动语义

- 移动对象是将这个对象所管理资源的所有权转移到另一个对象
- 这往往能带来性能上的提升，移动资源通常只需要进行指针操作
- 移动语义可以用在临时对象或者显式调用`std::move`实现
- 另外移动语义可以作用在不可复制对象上，例如`std::unique_ptr`，使其可以在不同作用域之间进行转移

## 右值引用

- 右值引用是C++11新引入的新引用类型
- 可以通过T&&来创建T类型（非模板类型参数，如int或其他自定义类型）的右值引用
- 右值引用仅能绑定到右值

<details close>
<summary>详细信息</summary>

```cpp
// 对左值和右值的类型推导
int x = 0; // `x` is an lvalue of type `int`
int& xl = x; // `xl` is an lvalue of type `int&`
int&& xr = x; // compiler error -- `x` is an lvalue
int&& xr2 = 0; // `xr2` is an lvalue of type `int&&` -- binds to the rvalue temporary, `0`

void f(int& x) {}
void f(int&& x) {}

f(x);  // calls f(int&)
f(xl); // calls f(int&)
f(3);  // calls f(int&&)
f(std::move(x)); // calls f(int&&)

f(xr2);           // calls f(int&)
f(std::move(xr2)); // calls f(int&& x)
```

</details>

## 转发引用

- 可以通过T&&（T是模板类型参数，且不能有cv限定）或auto&&（但当其从花括号包围的初始化器列表推导时则不是）创建一个转发引用
- 转发引用是一种特殊的引用，它保持函数实参的值类别，使得能利用`std::forward`转发实参——完美转发。也就是左值转发为左值，临时对象转发为右值
- 转发引用根据类型可以绑定到左值引用或右值引用。有以下规则，称为引用坍缩或引用折叠（reference collapsing）
- 也就是右值引用的右值引用坍缩成右值引用，所有其他组合均坍缩成左值引用

```cpp
// T& & becomes T&
// T& && becomes T&
// T&& & becomes T&
// T&& && becomes T&&
```

<details close>
<summary>详细信息</summary>

```cpp
typedef int&  lref;
typedef int&& rref;
int n;
lref&  r1 = n; // r1 的类型是 int&
lref&& r2 = n; // r2 的类型是 int&
rref&  r3 = n; // r3 的类型是 int&
rref&& r4 = 1; // r4 的类型是 int&&

int x = 0; // `x` is an lvalue of type `int`
int& xl = x; // `xl` is an lvalue of type `int&`
int&& xr = x; // compiler error -- `x` is an lvalue
int&& xr2 = 0; // `xr2` is an lvalue of type `int&&` -- binds to the rvalue temporary, `0`

void f(int& x) {}
void f(int&& x) {}

f(x);  // calls f(int&)
f(xl); // calls f(int&)
f(3);  // calls f(int&&)
f(std::move(x)) // calls f(int&&)

f(xr2);           // calls f(int&)
f(std::move(xr2)) // calls f(int&& x)

template<class T>
int f(T&& x) {                    // x 是转发引用
    return g(std::forward<T>(x)); // 从而能被转发
}
int main() {
    int i;
    f(i); // 实参是左值，调用 f<int&>(int&), std::forward<int&>(x) 是左值
    f(0); // 实参是右值，调用 f<int>(int&&), std::forward<int>(x) 是右值
}
 
template<class T>
int g(const T&& x); // x 不是转发引用：const T 不是无 cv 限定的
 
template<class T> struct A {
    template<class U>
    A(T&& x, U&& y, int* p); // x 不是转发引用：T 不是构造函数的类型模板形参
                             // 但 y 是转发引用
};

int x = 0; // `x` is an lvalue of type `int`
auto&& al = x; // `al` is an lvalue of type `int&` -- binds to the lvalue, `x`
auto&& ar = 0; // `ar` is an lvalue of type `int&&` -- binds to the rvalue temporary, `0`

// auto&&转发引用的例外
auto&& z = {1, 2, 3}; // *不是*转发引用（初始化器列表的特殊情形）
```

</details>

## 可变参数模板

- 使用...创建一个参数包或者展开一个参数包，模板参数包可以接受0个或多个模板参数
- 只要有一个模板参数包的模板称为可变参数模板

```cpp
// sizeof...获取模板参数包的长度
template <typename... T>
struct arity {
  constexpr static int value = sizeof...(T);
};
static_assert(arity<>::value == 0);
static_assert(arity<char, short, int>::value == 3);
```

<details close>
<summary>详细信息</summary>

```cpp
// 可以从模板参数包创建一个初始化列表，来遍历可变参数
template <typename First, typename... Args>
auto sum(const First first, const Args... args) -> decltype(first) {
  const auto values = {first, args...};
  return std::accumulate(values.begin(), values.end(), First{0});
}

sum(1, 2, 3, 4, 5); // 15
sum(1, 2, 3);       // 6
sum(1.5, 2.0, 3.7); // 7.2
```

</details>

## 初始化列表

- 初始化列表类似数组，可以通过花括号创建
- {1, 2, 3}的类型是`std::initializer_list<int>`

<details close>
<summary>详细信息</summary>

```cpp
int sum(const std::initializer_list<int>& list) {
  int total = 0;
  for (auto& e : list) {
    total += e;
  }

  return total;
}

auto list = {1, 2, 3};
sum(list); // == 6
sum({1, 2, 3}); // == 6
sum({}); // == 0
```

</details>

## 静态断言

- 在编译阶段进行断言

```cpp
constexpr int x = 0;
constexpr int y = 1;
static_assert(x == y, "x != y");
```

## auto

- auto声明的变量由编译器根据初始化时设定值的类型推导出来
- 函数的返回值也可以使用auto进行推导，必须使用decltype指定

```cpp
auto a = 3.14; // double
auto b = 1; // int
auto& c = b; // int&
auto d = { 0 }; // std::initializer_list<int>
auto&& e = 1; // int&&
auto&& f = b; // int&
auto g = new auto(123); // int*
const auto h = 1; // const int
auto i = 1, j = 2, k = 3; // int, int, int
auto l = 1, m = true, n = 1.61; // error -- `l` deduced to be int, `m` is bool
auto o; // error -- `o` requires initializer

template <typename X, typename Y>
auto add(X x, Y y) -> decltype(x + y) {
  return x + y;
}
add(1, 2); // == 3
add(1, 2.0); // == 3.0
add(1.5, 1.5); // == 3.0
```

## Lambda表达式

- Lambda是能够捕获一些变量的匿名函数对象
- 一般由捕获列表，参数列表，返回类型，函数体组成

```cpp
int x = 10;
auto add = [=] (int a, int b) {
  return a + b + x;
}
auto c = add(1, 2); // c == 13
```

<details close>
<summary>详细信息</summary>

```cpp
[] // 未捕获
[=] // 按值捕获局部变量和参数，按值捕获不能修改捕获的变量，即捕获的变量是const的，如果需要修改，则需要在参数列表后加上mutable，例子如下
[&] // 按引用捕获局部变量和参数
[this] // 按引用捕获this
[a, &b] // 按值捕获a，按引用捕获b

int x = 1;

auto getX = [=] { return x; };
getX(); // == 1

auto addX = [=](int y) { return x + y; };
addX(1); // == 2

auto getXRef = [&]() -> int& { return x; };
getXRef(); // int& to `x`

int x = 1;

auto f1 = [&x] { x = 2; }; // OK: x is a reference and modifies the original

auto f2 = [x] { x = 2; }; // ERROR: the lambda can only perform const-operations on the captured value
// vs.
auto f3 = [x]() mutable { x = 2; }; // OK: the lambda can perform any operations on the captured value
```

</details>

## decltype

- decltype是一个新的运算符，返回给定表达式的声明类型，同时会保留cv限定符和引用类型
- decltype可以用来推导函数返回值
- 与auto类型推导有差异

```cpp
int a = 1; // `a` is declared as type `int`
decltype(a) b = a; // `decltype(a)` is `int`
const int& c = a; // `c` is declared as type `const int&`
auto x = c; // x is int
decltype(c) d = a; // `decltype(c)` is `const int&`
decltype(123) e = 123; // `decltype(123)` is `int`
int&& f = 1; // `f` is declared as type `int&&`
decltype(f) g = 1; // `decltype(f) is `int&&`
decltype((a)) h = g; // `decltype((a))` is int&

template <typename X, typename Y>
auto add(X x, Y y) -> decltype(x + y) {
  return x + y;
}
add(1, 2.0); // `decltype(x + y)` => `decltype(3.0)` => `double`
```

## 类型别名

- using与typedef类似，但使用起来更易读，且可以和模板兼容
  
```cpp
template <typename T>
using Vec = std::vector<T>;
Vec<int> v; // std::vector<int>

using String = std::string;
String s {"foo"};
```

## nullptr

- nullptr用来替代NULL宏，它的类型为`std::nullptr_t`
- nullptr可以隐式转换为其他任意指针类型，除bool外，不能转换为整数类型

```cpp
void foo(int);
void foo(char*);
foo(NULL); // error -- ambiguous
foo(nullptr); // calls foo(char*)
```

## 强类型枚举

- 类型安全的枚举，用来解决一些平常枚举带来的问题，如隐式转换，不能指定底层类型和范围污染等

```cpp
// Specifying underlying type as `unsigned int`
enum class Color : unsigned int { Red = 0xff0000, Green = 0xff00, Blue = 0xff };
// `Red`/`Green` in `Alert` don't conflict with `Color`
enum class Alert : bool { Red, Green };
Color c = Color::Red;
```

## 属性

- 提供__attribute__(...), __declspec等的通用语法

```cpp
// `noreturn` attribute indicates `f` doesn't return.
[[ noreturn ]] void f() {
  throw "error";
}
```

## constexpr

- 常量表达式在编译阶段求值
- constexpr可以指定变量，函数等是一个常量表达式

```cpp
constexpr int square(int x) {
  return x * x;
}

int square2(int x) {
  return x * x;
}

int a = square(2);  // mov DWORD PTR [rbp-4], 4

int b = square2(2); // mov edi, 2
                    // call square2(int)
                    // mov DWORD PTR [rbp-8], eax

const int x = 123;
constexpr const int& y = x; // error -- constexpr variable `y` must be initialized by a constant expression

// with class
struct Complex {
  constexpr Complex(double r, double i) : re{r}, im{i} { }
  constexpr double real() { return re; }
  constexpr double imag() { return im; }

private:
  double re;
  double im;
};

constexpr Complex I(0, 1);
```

## 委托构造函数

- 构造函数可以在初始化列表里调用其他构造函数来完成构造

```cpp
struct Foo {
  int foo;
  Foo(int foo) : foo{foo} {}
  Foo() : Foo(0) {}
};

Foo foo;
foo.foo; // == 0
```

## 用户定义的字面量

- 如下语法创建自定义的字面量：T operator "" X(...) { ... }，名称为X，返回类型为T
- 不以_开头的名字是保留的，不会被调用

```cpp
// `unsigned long long` parameter required for integer literal.
long long operator "" _celsius(unsigned long long tempCelsius) {
  return std::llround(tempCelsius * 1.8 + 32);
}
24_celsius; // == 75

// `const char*` and `std::size_t` required as parameters.
int operator "" _int(const char* str, std::size_t) {
  return std::stoi(str);
}

"123"_int; // == 123, with type `int`
```

## 显式指定虚函数的覆盖

- 通过override指定是否覆盖了父类的虚函数，如果未覆盖，则产生编译错误

```cpp
struct A {
  virtual void foo();
  void bar();
};

struct B : A {
  void foo() override; // correct -- B::foo overrides A::foo
  void bar() override; // error -- A::bar is not virtual
  void baz() override; // error -- B::baz does not override A::baz
};
```

## final

- final指定函数不能被覆盖或该类不能被继承

```cpp
struct A {
  virtual void foo();
};

struct B : A {
  virtual void foo() final;
};

struct C : B {
  virtual void foo(); // error -- declaration of 'foo' overrides a 'final' function
};

struct A final {};
struct B : A {}; // error -- base 'A' is marked 'final'
```

## default和delete

- default可以提供函数的默认实现
- delete可以删除一个函数的实现，在禁用对象复制上很有用

```cpp
struct B {
  B() : x{1} {}
  int x;
};

struct C : B {
  // Calls B::B
  C() = default;
};

C c; // c.x == 1

class A {
  int x;

public:
  A(int x) : x{x} {};
  A(const A&) = delete;
  A& operator=(const A&) = delete;
};

A x {123};
A y = x; // error -- call to deleted copy constructor
y = x; // error -- operator= deleted
```

## 基于范围的for循环

- 用于遍历容器元素的语法糖

```cpp
std::array<int, 5> a {1, 2, 3, 4, 5};
for (int& x : a) x *= 2;
// a == { 2, 4, 6, 8, 10 }
```

## 用于移动语义的成员函数

- 类可以通过移动构造函数和移动赋值运算符类实现移动语义

```cpp
struct A {
  std::string s;
  A() : s{"test"} {}
  A(const A& o) : s{o.s} {}
  A(A&& o) : s{std::move(o.s)} {}
  A& operator=(A&& o) {
   s = std::move(o.s);
   return *this;
  }
};

A f(A a) {
  return a;
}

A a1 = f(A{}); // move-constructed from rvalue temporary
A a2 = std::move(a1); // move-constructed using std::move
A a3 = A{};
a2 = std::move(a3); // move-assignment using std::move
a1 = f(A{}); // move-assignment from rvalue temporary
```

## 转换构造函数

- 转换构造函数将大括号列表中的值转换为构造函数参数

```cpp
struct A {
  A(int) {}
  A(int, int) {}
  A(int, int, int) {}
};

A a {0, 0}; // calls A::A(int, int)
A b(0, 0); // calls A::A(int, int)
A c = {0, 0}; // calls A::A(int, int)
A d {0, 0, 0}; // calls A::A(int, int, int)

// 不允许向下转换
struct A {
  A(int) {}
};

A a(1.1); // OK
A b {1.1}; // Error narrowing conversion from double to int
```

## 显式转换函数

- explicit可以用在转换函数上

```cpp
struct A {
  operator bool() const { return true; }
};

struct B {
  explicit operator bool() const { return true; }
};

A a;
if (a); // OK calls A::operator bool()
bool ba = a; // OK copy-initialization selects A::operator bool()

B b;
if (b); // OK calls B::operator bool()
bool bb = b; // error copy-initialization does not consider B::operator bool()
```

## inline命名空间

- 内联命名空间所有成员被当做其父命名空间的一部分，可以用来简化版本控制
- 内联命名空间可以传递

```cpp
namespace Program {
  namespace Version1 {
    int getVersion() { return 1; }
    bool isFirstVersion() { return true; }
  }
  inline namespace Version2 {
    int getVersion() { return 2; }
  }
}

int version {Program::getVersion()};              // Uses getVersion() from Version2
int oldVersion {Program::Version1::getVersion()}; // Uses getVersion() from Version1
bool firstVersion {Program::isFirstVersion()};    // Does not compile when Version2 is added
```

## 非静态数据成员初始化

- 允许在声明的时候对数据成员进行初始化

```cpp
// Default initialization prior to C++11
class Human {
    Human() : age{0} {}
  private:
    unsigned age;
};
// Default initialization on C++11
class Human {
  private:
    unsigned age {0};
};
```

## 尖括号

- 可以推断尖括号的结束，无需使用空格分隔

```cpp
typedef std::map<int, std::map <int, std::map <int, int> > > cpp98LongTypedef;
typedef std::map<int, std::map <int, std::map <int, int>>>   cpp11LongTypedef;
```

## 引用限定的成员函数

- 可以根据*this是左值或右值来确定使用哪个函数

```cpp
struct Bar {
  // ...
};

struct Foo {
  Bar getBar() & { return bar; }
  Bar getBar() const& { return bar; }
  Bar getBar() && { return std::move(bar); }
private:
  Bar bar;
};

Foo foo{};
Bar bar = foo.getBar(); // calls `Bar getBar() &`

const Foo foo2{};
Bar bar2 = foo2.getBar(); // calls `Bar Foo::getBar() const&`

Foo{}.getBar(); // calls `Bar Foo::getBar() &&`
std::move(foo).getBar(); // calls `Bar Foo::getBar() &&`

std::move(foo2).getBar(); // calls `Bar Foo::getBar() const&&`
```

## 返回类型后置

- 函数和Lambda允许返回类型后置

```cpp
int f() {
  return 123;
}
// vs.
auto f() -> int {
  return 123;
}

auto g = []() -> int {
  return 123;
};

// 通过decltype可以推断返回类型，C++14提供了decltype(auto)来推断返回类型
// NOTE: This does not compile!
template <typename T, typename U>
decltype(a + b) add(T a, U b) {
    return a + b;
}

// Trailing return types allows this:
template <typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}
```

## noexcept

- 说明是否会引发异常
- noexcept函数可以调用可能抛出异常的函数，当出现这种情况，会直接调用`std::terminate`结束程序

```cpp
void func1() noexcept;        // does not throw
void func2() noexcept(true);  // does not throw
void func3() throw();         // does not throw

void func4() noexcept(false); // may throw

extern void f();  // potentially-throwing
void g() noexcept {
    f();          // valid, even if f throws
    throw 42;     // valid, effectively a call to std::terminate
}
```

## char32_t和char16_t

- 用于标识UTF-8字符串的标准类型

```cpp
char32_t utf8_str[] = U"\u0123";
char16_t utf8_str[] = u"\u0123";
```

## 原始字符串字面量

- 通过这种方式可以直接使用某些转义字符，使程序更可读
- 语法为：R"delimiter(raw_characters)delimiter"
- delimiter是由除了()\和空格组成的可选序列，用于标识结束
- raw_characters不能包含)delimiter"

```cpp
// msg1 and msg2 are equivalent.
const char* msg1 = "\nHello,\n\tworld!\n";
const char* msg2 = R"(
Hello,
	world!
)";
```

# C++11库特性

## std::move

- `std::move`用来实现移动语义，定义如下，即强制转换为右值引用

```cpp
template <typename T>
typename remove_reference<T>::type&& move(T&& arg) {
  return static_cast<typename remove_reference<T>::type&&>(arg);
}
```

## std::forward

- `std::forward`进行参数转发，保留值类别和cv限定符，可以实现完美转发

```cpp
// 转发左值到左值或右值
template <typename T>
T&& forward(typename remove_reference<T>::type& arg) {
  return static_cast<T&&>(arg);
}

// 转发右值到右值
template <typename T>
T&& forward(typename remove_reference<T>::type&& arg) {
  return static_cast<T&&>(arg);
}

template <typename T, typename... Args>
T* construct_at(T* p, Args&&... args) {
  new (p) T(std::forward<Args>(args)...);
  return p;
}
```

## std::thread

- 提供对线程的控制

```cpp
void foo(bool clause) { /* do something... */ }

std::vector<std::thread> threadsVector;
threadsVector.emplace_back([]() {
  // Lambda function that will be invoked    
});
threadsVector.emplace_back(foo, true);  // thread will run foo(true)
for (auto& thread : threadsVector) {
  thread.join(); // Wait for threads to finish
}
```

## std::to_string

- 将数值类型转换为`std::string`

```cpp
std::to_string(1.2); // == "1.2"
std::to_string(123); // == "123"
```

## 类型萃取

- 通过编译时的模板接口来获取或修改类型

```cpp
static_assert(std::is_integral<int>::value);
static_assert(std::is_same<int, int>::value);
static_assert(std::is_same<std::conditional<true, int, double>::type, int>::value);
```

## 智能指针

- 引入了新的智能指针`std::unique_ptr`,`std::share_ptr`和`std::weak_ptr`
- 不推荐使用`std::auto_ptr`，其在C++17中被移除
- 推荐使用`std::make_shared`和`std::make_unique`来创建智能指针
- `std::unique_ptr`是不可复制，但可移动的对象
- `std::shared_ptr`通过引用计数来实现，引用计数是线程安全的，但是它管理的对象不是

## std::chrono

- 用来处理时间库

```cpp
std::chrono::time_point<std::chrono::steady_clock> start, end;
start = std::chrono::steady_clock::now();
// Some computations...
end = std::chrono::steady_clock::now();

std::chrono::duration<double> elapsed_seconds = end - start;
double t = elapsed_seconds.count(); // t number of seconds, represented as a `double`
```

## 元组

- 元组是固定大小的可以拥有不同类型值的集合，是泛化的`std::pair`

```cpp
// `playerProfile` has type `std::tuple<int, const char*, const char*>`.
auto playerProfile = std::make_tuple(51, "Frans Nielsen", "NYI");
std::get<0>(playerProfile); // 51
std::get<1>(playerProfile); // "Frans Nielsen"
std::get<2>(playerProfile); // "NYI"
```

## std::tie

- 可以创建元组的左值引用
- 可以用在`std::pair`和`std::tuple`上，可以通过`std::ignore`来忽略对应的值
- 在C++17中可以使用结构化绑定来替代

```cpp
// With tuples...
std::string playerName;
std::tie(std::ignore, playerName, std::ignore) = std::make_tuple(91, "John Tavares", "NYI");

// With pairs...
std::string yes, no;
std::tie(yes, no) = std::make_pair("yes", "no");
```

## std::array

- 是固定大小的容器，类似数组，支持一般容器的操作

```cpp
std::array<int, 3> a = {2, 1, 3};
std::sort(a.begin(), a.end()); // a == { 1, 2, 3 }
for (int& x : a) x *= 2; // a == { 2, 4, 6 }
```

## 无序容器

- 拥有常量操作时间，包括`std::unordered_map`,`std::unordered_multimap`,`unordered_set`和`unordered_multiset`

## std::make_shared

- `std::make_shared`是创建`std::shared_ptr`对象的推荐方式，原因如下
  - 避免使用new运算符
  - 指定指针的类型时，避免代码重复
  - 提供了异常安全
  - 避免两次内存分配，即一次new T和一次智能指针的内存分配

```cpp
// function_that_throws出现异常时，可能造成内存泄漏
foo(std::shared_ptr<T>{new T{}}, function_that_throws(), std::shared_ptr<T>{new T{}});
foo(std::make_shared<T>(), function_that_throws(), std::make_shared<T>());
```

## std::ref

- 用来创建`std::reference_wrapper`对象的函数，可以绑定一个值的引用
- 通常用在使用一般引用无法编译或类型推导无法满足需求的地方
- `std::cref`可以创建常量引用

```cpp
// create a container to store reference of objects.
auto val = 99;
auto _ref = std::ref(val);
_ref++;
auto _cref = std::cref(val);
//_cref++; does not compile
std::vector<std::reference_wrapper<int>>vec; // vector<int&>vec does not compile
vec.push_back(_ref); // vec.push_back(&i) does not compile
cout << val << endl; // prints 100
cout << vec[0] << endl; // prints 100
cout << _cref; // prints 100
```

## 内存模型

- C++11引入了内存模型，可以支持线程和原子操作
- 包括：atomic loads/stores, compare-and-swap, atomic flags, promises, futures, locks, and condition variables等

## std::async

- `std::async`可以异步或延迟执行给定的函数，返回一个保存函数执行结果的`std::future`

```cpp
int foo() {
  /* Do something here, then return the result. */
  return 1000;
}

auto handle = std::async(std::launch::async, foo);  // create an async task
auto result = handle.get();  // wait for the result
```

## std::begin/end

- 返回容器的begin和end迭代器
- 可以用在原始数组上

```cpp
template <typename T>
int CountTwos(const T& container) {
  return std::count_if(std::begin(container), std::end(container), [](int item) {
    return item == 2;
  });
}

std::vector<int> vec = {2, 2, 43, 435, 4543, 534};
int arr[8] = {2, 43, 45, 435, 32, 32, 32, 32};
auto a = CountTwos(vec); // 2
auto b = CountTwos(arr);  // 1
```

## 参考

- [modern-cpp-features](https://github.com/AnthonyCalandra/modern-cpp-features)

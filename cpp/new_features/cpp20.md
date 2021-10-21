- [C++20语言新特性](#c20语言新特性)
  - [协程](#协程)
  - [概念](#概念)
  - [指定初始化](#指定初始化)
  - [Lambda的模板语法](#lambda的模板语法)
  - [带初始化的基于范围的for循环](#带初始化的基于范围的for循环)
  - [likely和unlikely属性](#likely和unlikely属性)
  - [弃用this的隐式捕获](#弃用this的隐式捕获)
  - [在非类型模板参数中使用类](#在非类型模板参数中使用类)
  - [constexpr的虚函数](#constexpr的虚函数)
  - [explicit(bool)](#explicitbool)
  - [立即函数](#立即函数)
  - [using枚举](#using枚举)
  - [Lambda捕获模板参数包](#lambda捕获模板参数包)
  - [char8_t](#char8_t)
- [C++20库特性](#c20库特性)
  - [概念库](#概念库)
    - [核心语言概念](#核心语言概念)
    - [比较概念](#比较概念)
    - [对象概念](#对象概念)
    - [可调用概念](#可调用概念)
  - [同步缓冲区的输出流](#同步缓冲区的输出流)
  - [std::span](#stdspan)
  - [位操作](#位操作)
  - [数学常量](#数学常量)
  - [std::is_constant_evaluated](#stdis_constant_evaluated)
  - [std::make_shared支持数组](#stdmake_shared支持数组)
  - [字符串新成员`starts_with`和`ends_with`](#字符串新成员starts_with和ends_with)
  - [检查关联容器是否存在某元素](#检查关联容器是否存在某元素)
  - [std::bit_cast](#stdbit_cast)
  - [std::midpoint](#stdmidpoint)
  - [std::to_array](#stdto_array)
- [参考](#参考)

# C++20语言新特性

## 协程

- 协程是可以暂停执行和恢复执行的特殊函数
- 协程的函数体内`co_return`,`co_wait`或`co_yeild`关键字之一
- C++20的协程是无栈的，除非编译器优化，否则它们的状态分配在堆上
- `co_yeild`获取给定表达式的值，返回其值，并挂起该协程，恢复后，继续执行其后的语句

```cpp
// 示例是一个生成器函数，每次调用时产生一个值
generator<int> range(int start, int end) {
  while (start < end) {
    co_yield start;
    start++;
  }

  // Implicit co_return at the end of this function:
  // co_return;
}

for (int n : range(0, 10)) {
  std::cout << n << std::endl;
}
```

## 概念

- 概念是可约束类型的编译时谓词，形式如下
- `constraint-expression`的值为`constexpr`的布尔值
- 约束应该为语义需求的模型，如类型是数字还是可哈希的
- 如果给定类型不满足约束条件，则产生编译错误，可以提供更有意义的错误信息和运行时安全

```cpp
template < template-parameter-list >
concept concept-name = constraint-expression;
```

```cpp
// `T` is not limited by any constraints.
template <typename T>
concept always_satisfied = true;
// Limit `T` to integrals.
template <typename T>
concept integral = std::is_integral_v<T>;
// Limit `T` to both the `integral` constraint and signedness.
template <typename T>
concept signed_integral = integral<T> && std::is_signed_v<T>;
// Limit `T` to both the `integral` constraint and the negation of the `signed_integral` constraint.
template <typename T>
concept unsigned_integral = integral<T> && !signed_integral<T>;
```

```cpp
// 使用概念的语法形式
// Forms for function parameters:
// `T` is a constrained type template parameter.
template <my_concept T>
void f(T v);

// `T` is a constrained type template parameter.
template <typename T>
  requires my_concept<T>
void f(T v);

// `T` is a constrained type template parameter.
template <typename T>
void f(T v) requires my_concept<T>;

// `v` is a constrained deduced parameter.
void f(my_concept auto v);

// `v` is a constrained non-type template parameter.
template <my_concept auto v>
void g();

// Forms for auto-deduced variables:
// `foo` is a constrained auto-deduced value.
my_concept auto foo = ...;

// Forms for lambdas:
// `T` is a constrained type template parameter.
auto f = []<my_concept T> (T v) {
  // ...
};
// `T` is a constrained type template parameter.
auto f = []<typename T> requires my_concept<T> (T v) {
  // ...
};
// `T` is a constrained type template parameter.
auto f = []<typename T> (T v) requires my_concept<T> {
  // ...
};
// `v` is a constrained deduced parameter.
auto f = [](my_concept auto v) {
  // ...
};
// `v` is a constrained non-type template parameter.
auto g = []<my_concept auto v> () {
  // ...
};
```

- `requiers`关键字用于约束子句或约束表达式

```cpp
template <typename T>
  requires my_concept<T> // `requires` clause.
void f(T);

template <typename T>
concept callable = requires (T f) { f(); }; // `requires` expression.

template <typename T>
  requires requires (T x) { x + x; } // `requires` clause and expression on same line.
T add(T a, T b) {
  return a + b;
}
```

约束表达式的参数列表是可选的，约束表达式的要求是以下之一

- 简单要求——断言给定的表达式是有效的

```cpp
template <typename T>
concept callable = requires (T f) { f(); };
```

- 类型要求——用`typename`关键字表示，后跟一个类型名称，表示给定的类型名称有效

```cpp
struct foo {
  int foo;
};

struct bar {
  using value = int;
  value data;
};

struct baz {
  using value = int;
  value data;
};

// Using SFINAE, enable if `T` is a `baz`.
template <typename T, typename = std::enable_if_t<std::is_same_v<T, baz>>>
struct S {};

template <typename T>
using Ref = T&;

template <typename T>
concept C = requires {
                     // Requirements on type `T`:
  typename T::value; // A) has an inner member named `value`
  typename S<T>;     // B) must have a valid class template specialization for `S`
  typename Ref<T>;   // C) must be a valid alias template substitution
};

template <C T>
void g(T a);

g(foo{}); // ERROR: Fails requirement A.
g(bar{}); // ERROR: Fails requirement B.
g(baz{}); // PASS.
```

- 复合要求——用大括号表示的表达式，后跟返回类型或类型约束

```cpp
template <typename T>
concept C = requires(T x) {
  {*x} -> typename T::inner; // the type of the expression `*x` is convertible to `T::inner`
  {x + 1} -> std::same_as<int>; // the expression `x + 1` satisfies `std::same_as<decltype((x + 1))>`
  {x * 1} -> T; // the type of the expression `x * 1` is convertible to `T`
};
```

- 嵌套要求——用`requires`表示，指定其他约束类型

```cpp
template <typename T>
concept C = requires(T x) {
  requires std::same_as<sizeof(x), size_t>;
};
```

## 指定初始化

- 类似C结构体的初始化，未列出的所有成员都将默认初始化(default-initialized)

```cpp
struct A {
  int x;
  int y;
  int z = 123;
};

A a {.x = 1, .z = 2}; // a.x == 1, a.y == 0, a.z == 2
```

## Lambda的模板语法

- Lambda表达式中使用模板

```cpp
auto f = []<typename T>(std::vector<T> v) {
  // ...
};
```

## 带初始化的基于范围的for循环

- 简化常见代码模式，保持代码紧凑，为常见的声明周期问题提供了一种优雅的解决方法

```cpp
for (auto v = std::vector{1, 2, 3}; auto& e : v) {
  std::cout << e;
}
// prints "123"
```

## likely和unlikely属性

- 为优化器提供指示

```cpp
int random = get_random_number_between_x_and_y(0, 3);
[[likely]] if (random > 0) {
  // body of if statement
  // ...
}

[[unlikely]] while (unlikely_truthy_condition) {
  // body of while statement
  // ...
}
```

## 弃用this的隐式捕获

- `[=]`隐式捕获被弃用，建议使用显式捕获

```cpp
struct int_value {
  int n = 0;
  auto getter_fn() {
    // BAD:
    // return [=]() { return n; };

    // GOOD:
    return [=, *this]() { return n; };
  }
};
```

## 在非类型模板参数中使用类

- 可以在非类型模板参数中使用类
- 作为模板参数传递的对象类型为`const T`，且具有静态存储类型

```cpp
struct foo {
  foo() = default;
  constexpr foo(int) {}
};

template <foo f>
auto get_foo() {
  return f;
}

get_foo(); // uses implicit constructor
get_foo<foo{123}>();
```

## constexpr的虚函数

- `constexpr`可以用于虚函数，在编译时求值
- `constexpr`虚函数可以覆盖非`constexpr`虚函数，反之亦可

```cpp
struct X1 {
  virtual int f() const = 0;
};

struct X2: public X1 {
  constexpr virtual int f() const { return 2; }
};

struct X3: public X2 {
  virtual int f() const { return 3; }
};

struct X4: public X3 {
  constexpr virtual int f() const { return 4; }
};

constexpr X4 x4;
x4.f(); // == 4
```

## explicit(bool)

- 编译时有条件的选择是否使用显式构造函数
- `explicit`与`explicit(true)`等价

```cpp
struct foo {
  // Specify non-integral types (strings, floats, etc.) require explicit construction.
  template <typename T>
  explicit(!std::is_integral_v<T>) foo(T) {}
};

foo a = 123; // OK
foo b = "123"; // ERROR: explicit constructor is not a candidate (explicit specifier evaluates to true)
foo c {"123"}; // OK
```

## 立即函数

- 与`constexpr`函数类型，但是带有`consteval`的函数必须产生一个常数

```cpp
consteval int sqr(int n) {
  return n * n;
}

constexpr int r = sqr(100); // OK
int x = 100;
int r2 = sqr(x); // ERROR: the value of 'x' is not usable in a constant expression
                 // OK if `sqr` were a `constexpr` function
```

## using枚举

- 将枚举引入作用域，提高可读性

```cpp
// 之前
enum class rgba_color_channel { red, green, blue, alpha };

std::string_view to_string(rgba_color_channel channel) {
  switch (channel) {
    case rgba_color_channel::red:   return "red";
    case rgba_color_channel::green: return "green";
    case rgba_color_channel::blue:  return "blue";
    case rgba_color_channel::alpha: return "alpha";
  }
}

// 现在
enum class rgba_color_channel { red, green, blue, alpha };

std::string_view to_string(rgba_color_channel my_channel) {
  switch (my_channel) {
    using enum rgba_color_channel;
    case red:   return "red";
    case green: return "green";
    case blue:  return "blue";
    case alpha: return "alpha";
  }
}
```

## Lambda捕获模板参数包

- 可按值或按引用捕获

```cpp
template <typename... Args>
auto f(Args&&... args){
    // BY VALUE:
    return [...args = std::forward<Args>(args)] {
        // ...
    };
}

template <typename... Args>
auto f(Args&&... args){
    // BY REFERENCE:
    return [&...args = std::forward<Args>(args)] {
        // ...
    };
}
```

## char8_t

- 提供表示UTF-8字符串的标准类型

```cpp
char8_t utf8_str[] = u8"\u0123";
```

# C++20库特性

## 概念库

- 标准库提供了用于构建更复杂概念的概念

### 核心语言概念

- `same_as`——指定两种类型相同
- `derived_from`——指定一个类型是另一个类型派生的
- `convertible_to`——指定一种类型可以隐式转换为另一个类型
- `common_with`——指定两个类型共享一个公共类型
- `integral`——指定类型是一个整数类型
- `default_constructible`——指定类型的对象可以进行默认构造(default-constructed)

### 比较概念

- `boolean`——指定可以在布尔上下文中使用的类型
- `equality_comparable`——指定`operator==`是等价关系

### 对象概念

- `movable`——指定类型的对象可移动和交换
- `copyable`——指定类型的对象可复制，移动和交换
- `semiregular`——指定类型的对象可复制，移动，交换和默认构造(default-constructed)
- `regular`——指定类型的对象既是`semiregular`，也是`equality_comparable`的

### 可调用概念

- `invocable`——可以使用给定的参数进行调用
- `predicate`——指定可调用类型为布尔谓词

## 同步缓冲区的输出流

- 包装输出操作，确保同步，即无输出交错

```cpp
std::osyncstream{std::cout} << "The value of x is:" << x << std::endl;
```

## std::span

- 提供容器的视图，不拥有所有权
- 复制和构造不会产生内存分配
- 可以是动态的和固定大小的

```cpp
void f(std::span<int> ints) {
    std::for_each(ints.begin(), ints.end(), [](auto i) {
        // ...
    });
}

std::vector<int> v = {1, 2, 3};
f(v);
std::array<int, 3> a = {1, 2, 3};
f(a);
// etc.

constexpr size_t LENGTH_ELEMENTS = 3;
int* arr = new int[LENGTH_ELEMENTS]; // arr = {0, 0, 0}

// Fixed-sized span which provides a view of `arr`.
std::span<int, LENGTH_ELEMENTS> span = arr;
span[1] = 1; // arr = {0, 1, 0}

// Dynamic-sized span which provides a view of `arr`.
std::span<int> d_span = arr;
span[0] = 1; // arr = {1, 1, 0}

constexpr size_t LENGTH_ELEMENTS = 3;
int* arr = new int[LENGTH_ELEMENTS];

std::span<int, LENGTH_ELEMENTS> span = arr; // OK
std::span<double, LENGTH_ELEMENTS> span2 = arr; // ERROR
std::span<int, 1> span3 = arr; // ERROR
```

## 位操作

- 头文件`<bit>`提供了一些位操作

```cpp
std::popcount(0u); // 0
std::popcount(1u); // 1
std::popcount(0b1111'0000u); // 4
```

## 数学常量

- 头文件`<numbers>`提供了PI，欧拉数等常量

```cpp
std::numbers::pi; // 3.14159...
std::numbers::e; // 2.71828...
```

## std::is_constant_evaluated

- 谓词函数，在编译时上下文中调用为真

```cpp
constexpr bool is_compile_time() {
    return std::is_constant_evaluated();
}

constexpr bool a = is_compile_time(); // true
bool b = is_compile_time(); // false
```

## std::make_shared支持数组

```cpp
auto p = std::make_shared<int[]>(5); // pointer to `int[5]`
// OR
auto p = std::make_shared<int[5]>(); // pointer to `int[5]`
```

## 字符串新成员`starts_with`和`ends_with`

```cpp
std::string str = "foobar";
str.starts_with("foo"); // true
str.ends_with("baz"); // false
```

## 检查关联容器是否存在某元素

```cpp
std::map<int, char> map {{1, 'a'}, {2, 'b'}};
map.contains(2); // true
map.contains(123); // false

std::set<int> set {1, 2, 3};
set.contains(2); // true
```

## std::bit_cast

- 将一种类型解释为另一种类型更安全的方法

```cpp
float f = 123.0;
int i = std::bit_cast<int>(f);
```

## std::midpoint

- 安全的计算两个整数的中点，不会溢出

```cpp
std::midpoint(1, 3); // == 2
```

## std::to_array

```cpp
std::to_array("foo"); // returns `std::array<char, 4>`
std::to_array<int>({1, 2, 3}); // returns `std::array<int, 3>`

int a[] = {1, 2, 3};
std::to_array(a); // returns `std::array<int, 3>`
```

# 参考

- [modern-cpp-features](https://github.com/AnthonyCalandra/modern-cpp-features)

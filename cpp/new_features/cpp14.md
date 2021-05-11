- [C++14语言新特性](#c14语言新特性)
  - [二进制字面量](#二进制字面量)
  - [通用lambda表达式](#通用lambda表达式)
  - [Lambda捕获初始化](#lambda捕获初始化)
  - [返回类型推导](#返回类型推导)
  - [decltype(auto)](#decltypeauto)
  - [放松对constexpr函数的约束](#放松对constexpr函数的约束)
  - [变量模板](#变量模板)
  - [新增属性[[deprecated]]](#新增属性deprecated)
- [C++14库特性](#c14库特性)
  - [标准库的用户定义字面量](#标准库的用户定义字面量)
  - [编译时的整数序列](#编译时的整数序列)
  - [std::make_unique](#stdmake_unique)
  - [参考](#参考)

# C++14语言新特性

## 二进制字面量

- 提供方便表示2进制数字的方法，可以使用`'`分隔数字

```cpp
0b110 // == 6
0b1111'1111 // == 255
```

## 通用lambda表达式

- 允许在lambda的参数中使用auto类型说明符，进行自动类型推导，启用多态的lambda表达式

```cpp
auto identity = [](auto x) { return x; };
int three = identity(3); // == 3
std::string foo = identity("foo"); // == "foo"
```

## Lambda捕获初始化

- 允许使用任意表达式初始化lambda的捕获，捕获的名字无需与任何变量关联
- 初始化表达式在创建lambda时进行求值
- 可以使用`std::move`捕获仅可移动的对象
- 按引用捕获可以使用不同的名字

```cpp
int factory(int i) { return i * 10; }
auto f = [x = factory(2)] { return x; }; // returns 20

auto generator = [x = 0] () mutable {
  // this would not compile without 'mutable' as we are modifying x on each call
  return x++;
};
auto a = generator(); // == 0
auto b = generator(); // == 1
auto c = generator(); // == 2

auto p = std::make_unique<int>(1);

auto task1 = [=] { *p = 5; }; // ERROR: std::unique_ptr cannot be copied
// vs.
// task2中的p与上边的p是不同的变量
auto task2 = [p = std::move(p)] { *p = 5; }; // OK: p is move-constructed into the closure object
// the original p is empty after task2 is created

auto x = 1;
auto f = [&r = x, x = x * 10] {
  ++r;
  return r + x;
};
f(); // sets x to 2 and returns 12
```

## 返回类型推导

- 可以使用`auto`推导函数或lambda表达式的返回值

```cpp
// Deduce return type as `int`.
auto f(int i) {
 return i;
}

template <typename T>
auto& f(T& t) {
  return t;
}

// Returns a reference to a deduced type.
auto g = [](auto& x) -> auto& { return f(x); };
int y = 123;
int& z = g(y); // reference to `y`
```

## decltype(auto)

- `decltype(auto)`作用类似`auto`，区别是他可以保留引用和cv限定符

```cpp
const int x = 0;
auto x1 = x; // int
decltype(auto) x2 = x; // const int
int y = 0;
int& y1 = y;
auto y2 = y1; // int
decltype(auto) y3 = y1; // int&
int&& z = 0;
auto z1 = std::move(z); // int
decltype(auto) z2 = std::move(z); // int&&

// Note: Especially useful for generic code!

// Return type is `int`.
auto f(const int& i) {
 return i;
}

// Return type is `const int&`.
decltype(auto) g(const int& i) {
 return i;
}

int x = 123;
static_assert(std::is_same<const int&, decltype(f(x))>::value == 0);
static_assert(std::is_same<int, decltype(f(x))>::value == 1);
static_assert(std::is_same<const int&, decltype(g(x))>::value == 1);
```

## 放松对constexpr函数的约束

- 在C++11中，constexpr函数体只能包含`typedef`,`using`和单个return语句等
- C++14中，允许的语法增多了，如if语句，多个return语句，循环等

```cpp
constexpr int factorial(int n) {
  if (n <= 1) {
    return 1;
  } else {
    return n * factorial(n - 1);
  }
}
factorial(5); // == 120
```

## 变量模板

- 允许变量模板化

```cpp
template<class T>
constexpr T pi = T(3.1415926535897932385);
template<class T>
constexpr T e  = T(2.7182818284590452353);
```

## 新增属性[[deprecated]]

- 引入`[[deprecated]]`表示不鼓励使用某个函数或类
- 可能会产生编译警告，可以提供不推荐使用的原因

```cpp
[[deprecated]]
void old_method();
[[deprecated("Use new_method instead")]]
void legacy_method();
```

# C++14库特性

## 标准库的用户定义字面量

- 标准库新增了用户定义的字面量，包括`chrono`和`basic_string`
- 他们可以是constexpr，意味着可以在编译时使用

```cpp
using namespace std::chrono_literals;
auto day = 24h;
day.count(); // == 24
std::chrono::duration_cast<std::chrono::minutes>(day).count(); // == 1440
```

## 编译时的整数序列

- 模板类`std::integer_sequence`表示一个编译时的整数序列
  - `std::make_integer_sequence<T, N>`创建一个`0,1,...,N-1`的类型为T的序列
  - `std::index_sequence_for<T...>`将模板参数包转换为整数序列

```cpp
// 将array转换为元组
template<typename Array, std::size_t... I>
decltype(auto) a2t_impl(const Array& a, std::integer_sequence<std::size_t, I...>) {
  return std::make_tuple(a[I]...);
}

template<typename T, std::size_t N, typename Indices = std::make_index_sequence<N>>
decltype(auto) a2t(const std::array<T, N>& a) {
  return a2t_impl(a, Indices());
}
```

## std::make_unique

- `std::make_unique`是创建`std::unique_ptr`对象的推荐方式，原因如下
  - 避免使用new运算符
  - 指定指针的类型时，避免代码重复
  - 提供了异常安全
  - 避免两次内存分配，即一次new T和一次智能指针的内存分配

```cpp
// function_that_throws出现异常时，可能造成内存泄漏
foo(std::unique_ptr<T>{new T{}}, function_that_throws(), std::unique_ptr<T>{new T{}});
foo(std::make_unique<T>(), function_that_throws(), std::make_unique<T>());
```

## 参考

- [modern-cpp-features](https://github.com/AnthonyCalandra/modern-cpp-features)

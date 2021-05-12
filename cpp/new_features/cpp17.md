- [C++17语言新特性](#c17语言新特性)
  - [模板类的模板参数推导](#模板类的模板参数推导)
  - [auto声明非类型模板参数](#auto声明非类型模板参数)
  - [折叠表达式](#折叠表达式)
  - [括号初始化列表的推导新规则](#括号初始化列表的推导新规则)
  - [constexpr lambda](#constexpr-lambda)
  - [Lambda按值捕获this](#lambda按值捕获this)
  - [内联变量](#内联变量)
  - [嵌套命名空间](#嵌套命名空间)
  - [结构化绑定](#结构化绑定)
  - [带有初始化的选择语句](#带有初始化的选择语句)
  - [constexpr if](#constexpr-if)
  - [UTF-8字符量](#utf-8字符量)
  - [枚举的初始化](#枚举的初始化)
  - [fallthrough, nodiscard, maybe_unused属性](#fallthrough-nodiscard-maybe_unused属性)
- [C++17库特性](#c17库特性)
  - [std::variant](#stdvariant)
  - [std::optional](#stdoptional)
  - [std::any](#stdany)
  - [std::string_view](#stdstring_view)
  - [std::invoke](#stdinvoke)
  - [std::apply](#stdapply)
  - [std::filesystem](#stdfilesystem)
  - [std::byte](#stdbyte)
  - [拼接map和set](#拼接map和set)
  - [并行算法](#并行算法)
- [参考](#参考)


# C++17语言新特性

## 模板类的模板参数推导

- 类似模板函数参数推导，可以用在类的构造函数里

```cpp
template <typename T = float>
struct MyContainer {
  T val;
  MyContainer() : val{} {}
  MyContainer(T val) : val{val} {}
  // ...
};
MyContainer c1 {1}; // OK MyContainer<int>
MyContainer c2; // OK MyContainer<float>
```

## auto声明非类型模板参数

- 使用auto可以从模板参数列表的类型推导出非类型模板参数

```cpp
template <auto... seq>
struct my_integer_sequence {
  // Implementation here ...
};

// Explicitly pass type `int` as template argument.
auto seq = std::integer_sequence<int, 0, 1, 2>();
// Type is deduced to be `int`.
auto seq2 = my_integer_sequence<0, 1, 2>();
```

## 折叠表达式

- 在二进制运算符上可以执行模板参数包的折叠
  - 形式为`(... op e)`或`e op ...`的表达式称为一元折叠，op是运算符，e是未展开的模板参数包
  - 形式为`(e1 op ... op e2)`的表达式称为二元折叠，其中e1或e2之一是模板参数包

```cpp
template <typename... Args>
bool logicalAnd(Args... args) {
    // Binary folding.
    return (true && ... && args);
}
bool b = true;
bool& b2 = b;
logicalAnd(b, b2, true); // == true

template <typename... Args>
auto sum(Args... args) {
    // Unary folding.
    return (... + args);
}
sum(1.0, 2.0f, 3); // == 6.0
```

## 括号初始化列表的推导新规则

- 使用统一初始化语法时，对`auto`自动推导进行更改
  - `auto x {3};`先前推导为`std::initializer_list<int>`，现在为`int`

```cpp
auto x1 {1, 2, 3}; // error: not a single element
auto x2 = {1, 2, 3}; // x2 is std::initializer_list<int>
auto x3 {3}; // x3 is int
auto x4 {3.0}; // x4 is double
```

## constexpr lambda

- Lambda表达式可以声明为`constexpr`

```cpp
auto identity = [](int n) constexpr { return n; };
static_assert(identity(123) == 123);

constexpr auto add = [](int x, int y) {
  auto L = [=] { return x; };
  auto R = [=] { return y; };
  return [=] { return L() + R(); };
};

static_assert(add(1, 2)() == 3);

constexpr int addOne(int n) {
  return [n] { return n + 1; }();
}

static_assert(addOne(1) == 2);
```

## Lambda按值捕获this

- 以前lambda捕获`this`只能是以引用捕获
- 一个有问题的例子是使用异步回调的代码，这些回调可能要求对象在其声明周期之后才被调用
- `*this`在C++17中为按值捕获，会产生当前对象的拷贝，`this`仍然为按引用捕获

```cpp
struct MyObj {
  int value {123};
  auto getValueCopy() {
    return [*this] { return value; };
  }
  auto getValueRef() {
    return [this] { return value; };
  }
};
MyObj mo;
auto valueCopy = mo.getValueCopy();
auto valueRef = mo.getValueRef();
mo.value = 321;
valueCopy(); // 123
valueRef(); // 321
```

## 内联变量

- `inline`可以用于变量和函数，内联函数和内联变量具有相同语义
- 还可以用于声明和定义静态成员变量，这样就无需在源文件中对其进行初始化

```cpp
// Disassembly example using compiler explorer.
struct S { int x; };
inline S x1 = S{321}; // mov esi, dword ptr [x1]
                      // x1: .long 321

S x2 = S{123};        // mov eax, dword ptr [.L_ZZ4mainE2x2]
                      // mov dword ptr [rbp - 8], eax
                      // .L_ZZ4mainE2x2: .long 123

struct S {
  S() : id{count++} {}
  ~S() { count--; }
  int id;
  static inline int count{0}; // declare and initialize count to 0 within the class
};
```

## 嵌套命名空间

- 可以使用命名空间解析运算符创建嵌套的命名空间定义

```cpp
namespace A {
  namespace B {
    namespace C {
      int i;
    }
  }
}

namespace A::B::C {
  int i;
}
```

## 结构化绑定

- 允许类似`auto [ x, y, z ] = expr;`的表达式
  - `expr`是类元组的对象，包括`std::tuple`，`std::pair`，`std::array`和聚合类型结构

```cpp
using Coordinate = std::pair<int, int>;
Coordinate origin() {
  return Coordinate{0, 0};
}

const auto [ x, y ] = origin();
x; // == 0
y; // == 0

std::unordered_map<std::string, int> mapping {
  {"a", 1},
  {"b", 2},
  {"c", 3}
};

// Destructure by reference.
for (const auto& [key, value] : mapping) {
  // Do something with key and value
}
```

## 带有初始化的选择语句

- 允许`if`和`switch`包含初始化，使得代码更紧凑

```cpp
{
  std::lock_guard<std::mutex> lk(mx);
  if (v.empty()) v.push_back(val);
}
// vs.
if (std::lock_guard<std::mutex> lk(mx); v.empty()) {
  v.push_back(val);
}

Foo gadget(args);
switch (auto s = gadget.status()) {
  case OK: gadget.zip(); break;
  case Bad: throw BadFoo(s.message());
}
// vs.
switch (Foo gadget(args); auto s = gadget.status()) {
  case OK: gadget.zip(); break;
  case Bad: throw BadFoo(s.message());
}
```

## constexpr if

- 可以编写根据编译时条件的代码

```cpp
template <typename T>
constexpr bool isIntegral() {
  if constexpr (std::is_integral<T>::value) {
    return true;
  } else {
    return false;
  }
}
static_assert(isIntegral<int>() == true);
static_assert(isIntegral<char>() == true);
static_assert(isIntegral<double>() == false);
struct S {};
static_assert(isIntegral<S>() == false);
```

## UTF-8字符量

- 以`u8`开头的字符量是`char`类型的UTF-8字符量
- 它的值与ISO 10646值一样

```cpp
char x = u8'x';
```

## 枚举的初始化

- 可以使用括号初始化语法来初始化枚举

```cpp
enum byte : unsigned char {};
byte b {0}; // OK
byte c {-1}; // ERROR
byte d = byte{1}; // OK
byte e = byte{256}; // ERROR
```

## fallthrough, nodiscard, maybe_unused属性

- `[[fallthrough]]`表明在`switch`语句中，缺少`break`是预期行为

```cpp
switch (n) {
  case 1: [[fallthrough]]
    // ...
  case 2:
    // ...
    break;
}
```

- `[[nodiscard]]`当具有此属性的函数或类的返回值被丢弃，会产生警告

```cpp
[[nodiscard]] bool do_something() {
  return is_success; // true for success, false for failure
}

do_something(); // warning: ignoring return value of 'bool do_something()',
                // declared with attribute 'nodiscard'

// Only issues a warning when `error_info` is returned by value.
struct [[nodiscard]] error_info {
  // ...
};

error_info do_something() {
  error_info ei;
  // ...
  return ei;
}

do_something(); // warning: ignoring returned value of type 'error_info',
                // declared with attribute 'nodiscard'
```

- `[[maybe_unused]]`表明未使用是预期行为

```cpp
void my_callback(std::string msg, [[maybe_unused]] bool error) {
  // Don't care if `msg` is an error message, just log it.
  log(msg);
}
```

# C++17库特性

## std::variant

- `std::variant`可当做是类型安全的`union`
- 可为无值或某一个类型的值

```cpp
std::variant<int, double> v{ 12 };
std::get<int>(v); // == 12
std::get<0>(v); // == 12
v = 12.0;
std::get<double>(v); // == 12.0
std::get<1>(v); // == 12.0
```

## std::optional

- 可管理可选的值，可存在值或无值
- 常见的应用是可能失败函数的返回值

```cpp
std::optional<std::string> create(bool b) {
  if (b) {
    return "Godzilla";
  } else {
    return {};
  }
}

create(false).value_or("empty"); // == "empty"
create(true).value(); // == "Godzilla"
// optional-returning factory functions are usable as conditions of while and if
if (auto str = create(true)) {
  // ...
}
```

## std::any

- 可以存储任何单个值的容器

```cpp
std::any x {5};
x.has_value() // == true
std::any_cast<int>(x) // == 5
std::any_cast<int&>(x) = 10;
std::any_cast<int>(x) // == 10
```

## std::string_view

- 提供字符串的无所有权引用

```cpp
// Regular strings.
std::string_view cppstr {"foo"};
// Wide strings.
std::wstring_view wcstr_v {L"baz"};
// Character arrays.
char array[3] = {'b', 'a', 'r'};
std::string_view array_v(array, std::size(array));

std::string str {"   trim me"};
std::string_view v {str};
v.remove_prefix(std::min(v.find_first_not_of(" "), v.size()));
str; //  == "   trim me"
v; // == "trim me"
```

## std::invoke

- 可带参数调用`Callable`对象

```cpp
template <typename Callable>
class Proxy {
  Callable c;
public:
  Proxy(Callable c): c(c) {}
  template <class... Args>
  decltype(auto) operator()(Args&&... args) {
    // ...
    return std::invoke(c, std::forward<Args>(args)...);
  }
};
auto add = [](int x, int y) {
  return x + y;
};
Proxy<decltype(add)> p {add};
p(1, 2); // == 3
```

## std::apply

- 调用带元组参数的`Callable`对象

```cpp
auto add = [](int x, int y) {
  return x + y;
};
std::apply(add, std::make_tuple(1, 2)); // == 3
```

## std::filesystem

- 提供对文件系统中文件目录路径的操作

```cpp
const auto bigFilePath {"bigFileToCopy"};
if (std::filesystem::exists(bigFilePath)) {
  const auto bigFileSize {std::filesystem::file_size(bigFilePath)};
  std::filesystem::path tmpPath {"/tmp"};
  if (std::filesystem::space(tmpPath).available > bigFileSize) {
    std::filesystem::create_directory(tmpPath.append("example"));
    std::filesystem::copy_file(bigFilePath, tmpPath.append("newFile"));
  }
}
```

## std::byte

- 提供表示字节的标准方式
- `std::byte`不是字符类型也不是算术类型，唯一可用的操作是位运算
- `std::byte`是一个枚举

```cpp
// enum class byte : unsigned char {};

std::byte a {0};
std::byte b {0xFF};
int i = std::to_integer<int>(b); // 0xFF
std::byte c = a & b;
int j = std::to_integer<int>(c); // 0
```

## 拼接map和set

- 合并容器，不会产生复制和内存分配

```cpp
// 移动map到另一个
std::map<int, string> src {{1, "one"}, {2, "two"}, {3, "buckle my shoe"}};
std::map<int, string> dst {{3, "three"}};
dst.insert(src.extract(src.find(1))); // Cheap remove and insert of { 1, "one" } from `src` to `dst`.
dst.insert(src.extract(2)); // Cheap remove and insert of { 2, "two" } from `src` to `dst`.
// dst == { { 1, "one" }, { 2, "two" }, { 3, "three" } };

// 插入整个set
std::set<int> src {1, 3, 5};
std::set<int> dst {2, 4, 5};
dst.merge(src);
// src == { 5 }
// dst == { 1, 2, 3, 4, 5 }

// 插入超过容器生命周期的元素
auto elementFactory() {
  std::set<...> s;
  s.emplace(...);
  return s.extract(s.begin());
}
s2.insert(elementFactory());

// 更改key
std::map<int, string> m {{1, "one"}, {2, "two"}, {3, "three"}};
auto e = m.extract(2);
e.key() = 4;
m.insert(std::move(e));
// m == { { 1, "one" }, { 3, "three" }, { 4, "two" } }
```

## 并行算法

- 许多STL算法如`copy`,`find`和`sort`开始支持并行执行策略：`seq`,`par`和`par_unseq`
  - sequentially
  - parallel
  - parallel unsequenced

```cpp
std::vector<int> longVector;
// Find element using parallel execution policy
auto result1 = std::find(std::execution::par, std::begin(longVector), std::end(longVector), 2);
// Sort elements using sequential execution policy
auto result2 = std::sort(std::execution::seq, std::begin(longVector), std::end(longVector));
```

# 参考

- [modern-cpp-features](https://github.com/AnthonyCalandra/modern-cpp-features)

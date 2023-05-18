# C++ 中复杂却很有意思的SFINAE技术

SFINAE 其实就是重载的函数模板匹配，编译器根据名称找出所有适用的函数和函数模板，然后要根据实际情况对模板形参进行替换，在编译过程中寻找一个最佳匹配的过程。

比如说下面的例子：

```cpp
struct Test {
    typedef int foo;
};

template <typename T>
//要求类型T定义了内嵌类型foo
void f(typename T::foo) {} // Definition #1

template <typename T>
void f(T) {}               // Definition #2

int main() {
    f<Test>(10); // Call #1.
    f<int>(10);  // Call #2. Without error (even though there is no int::foo) thanks to SFINAE.
    return 0;
}
```

模板函数f一共定义了两个版本。`f<int>`传入了 int 类型，所以只能适配 #2，而 `f<Test>`传入 Test 类型，Test 结构体里面是定义了 foo 类型的，所以可以适配 `#1` 。

那么当编译器尝试编译一个函数调用的时候实际做了这几件事：

- 首先是根据执行名称进行查找；
- 对于函数模板来说，模板参数是根据传入的参数类型来进行推断的；
  - 根据传入类型找到对应模板之后会执行参数类型替换，并加入到解析集中；
  - 如果找到对应的类型不符合则从解析集中删除；
- 在最后，我们可以得到这个函数调用的解析集；
  - 如果解析集是空的，那么就编译失败，比如我们把上面例子中的`Definition #2`模板删除了，那 `f<int>(10);`调用就会编译失败；
  - 如果解析集有一个以上，那么需要根据参数类型找到最合适能被匹配上的函数；

![SFINAE技术](images/SFINAE%E6%8A%80%E6%9C%AF1.jpg)

那么利用 SFINAE 规则就可以做一些编译期决断，如类是否定义了内嵌类型，是否定义了给定名字的成员函数等。

```cpp
template <typename T>
struct has_reserve {
    struct good { char dummy; };
    struct bad { char dummy[2]; };
 
    template <class U, float (U::*)()>
    struct SFINAE {};

    template <typename  U>
    static good test(SFINAE<U, &U::reserve>*);

    template <typename>
    static bad test(...);

    static const bool value = sizeof(test<T>(nullptr)) == sizeof(good);
};

class  TestReserve {
public:
    float reserve();
};

class Bar {
public:
    int type;
};

int main() {   
    cout << "reserve:" << has_reserve<TestReserve>::value << endl;
    cout << "reserve:" << has_reserve<Bar>::value << endl; 
    return 0;
}
```

我们定义了一个 SFINAE 模板，内容也同样不重要，但模板的第二个参数需要是第一个参数的成员函数指针，并且参数类型为空，返回值是 float。随后，我们定义了一个要求 `SFINAE*` 类型的 reserve 成员函数模板，返回值是 good；再定义了一个对参数类型无要求的 reserve 成员函数模板。

我们定义常整型布尔值 value，结果是 true 还是 false，取决于 nullptr 能不能和 `SFINAE*` 匹配成功，而这又取决于模板参数 T 有没有返回类型是 void、接受一个参数并且类型为 size_t 的成员函数 reserve。

如果 T 未定义 reserve ，例如 Bar，由于 SFINAE 原则，适配第一个失败后编译器继续适配第二个并且成功，返回值为bad。

## enable_if

在 C++ 11 中出现了 enable_if，它是一个工具集，使得SFINAE使用上更加方便，首先从 cppreference 的例子看下enable_if的两种用法

```cpp
template <typename T>
typename std::enable_if<has_reserve<T>::value,void>::type
  reserve_test1 () {cout << "reserve_test1"<< endl;}


template < typename T,
           typename = typename std::enable_if<has_reserve<T>::value>::type>
void reserve_test2 () {cout <<"reserve_test2" << endl;}
 
int main() {   
    reserve_test1<TestReserve>();
    reserve_test2<TestReserve>();
    return 0;
} 
```

上面代表了enable_if的两种惯用方法：

- 返回值类型使用enable_if
- 模板参数额外指定一个默认的参数class = typename std::enable_if<…>::type

使用enable_if的好处是控制函数只接受某些类型的(value==true)的参数，否则编译报错，比如如果我们增加这么一句：reserve_test1<Bar>();就会报错，找不到对应的类型。

```text
error: no type named ‘type’ in ‘struct std::enable_if<false, void>’
```

要想让(value==false)的参数通过还需要加一个模板：

```cpp
template <typename T>
typename std::enable_if<!has_reserve<T>::value,void>::type
  reserve_test1 ()  {cout << "is not reserve " << endl;}
  
int main() {   
    reserve_test1<Bar>();
    return 0;
}
```

我们来看看 enable_if 是怎么利用 SFINAE 原则做到这样的效果的：

```cpp
template <bool, typename T=void>
struct enable_if {
};

template <typename T>
struct enable_if<true, T> {
  using type = T;
};
```

可以看到当enable_if第一个类型为true时会特化到第二种实现，此时内嵌类型type存在。否则编译器匹配第一种实现，内嵌类型type不存在，这也是上面编译操作提示的原因。所以当我们加了一个 is_odd重载模板，当 std::is_integral判断为 false 时取反等于 true 依然可以特化成 enable_if 的第二种实现。

除此之外还有一个 enable_if_t 的模板：

```cpp
template <bool _Test, class _Ty = void>
using enable_if_t = typename enable_if<_Test, _Ty>::type;
```

`enable_if_t`就是`enable_if::type`的重定义，如果`enable_if_t<_Test,_Ty>`的 Test 为 true，可以看出走了 enble_if 的特化版本，有 type 的定义，否则就没有 type 这个定义，有了这个版本之后实际上我们就可以把上面例子中的 `::type`去掉，稍微简化一下代码，这个也是可以在很多地方看到有用的。

## decltype & std::declval

在 C++ 11 中引入了 decltype & std::declval 为模板编程带来了许多的便利，下面先来简单介绍一下它们两。

decltype 是“declare type”的缩写，译为声明类型 ，decltype 可以认为与 auto 关键字一样，用于进行编译时类型推导，但是 decltype 的类型推导并不是像 auto 一样是从变量声明的初始化表达式获得变量的类型，而是总是以一个普通表达式作为参数，返回该表达式的类型,而且decltype并不会对表达式进行求值。简单的用法如下：

```cpp
int i = 4;
decltype(i) a; 
```

decltype 还有一个返回类型后置语法，将 decltype 和 auto 结合起来完成返回值类型的推导：

```cpp
template <typename T, typename U>
auto add(T t, U u) -> decltype(t + u){
    return t + u;
}
```

但有时候，一个类可能没有默认构造函数，这时就无法使用上面的方法，例如：

```cpp
struct A {
    A() = delete;
    int foo();
};

int main() {
    decltype(A().foo()) foo = 1; 
}
```

于是std::declval就派上了用场：

```cpp
#include <utility>

struct A {
    A() = delete;
    int foo();
};

int main() {
    decltype(std::declval<A>().foo()) foo = 1; 
}
```

所以通过使用 decltype & std::declval 让我们上面例子的写法可以更简单一些：

```cpp
template <typename  U>
auto test() ->decltype(declval<U&>().reserve(),void())
{
    cout << "type " << endl;
}

int main() {   
    test<TestReserve>();
    return 0; 
}
```

declval 可以在某类型没有默认构造函数的情况下，假想出一个该类的对象来进行类型推导。所以 `declval<U&>().reserve()` 用来测试 `U&` 类型的对象是不是有 reserve 成员函数。

需要注意的是C++ 里的逗号表达式的意思是按顺序逐个估值，并返回最后一项。所以 decltype 第二参数表示的是返回值类型为 void。

## void_t

在 C++ 17 我们还可以利用 void_t 和 decltype、declval 一起实现上面 enable_if 的功能。

void_t 的定义如下：

```cpp
template <typename...>
using void_t = void;
```

这个类型模板会把任意类型映射到 void。那么对于我们上面提到过的 has_reserve 函数可以这么写：

```cpp
template< class , class = void >
struct new_has_reserve : std::false_type
{ };
 
template< class T >
struct new_has_reserve< T , void_t< decltype(declval<T&>().reserve() ) > > : std::true_type
{ };
```

上面利用 decltype、declval 和模板特化，我们把 has_reserve 的定义大大简化。下面我们可以这么写：

```cpp
class A {
public:
    int reserve();
};

class B {
};

int main() {   
    cout << new_has_reserve< A >::value << endl; 
    cout <<new_has_reserve<B>::value << endl; 
    return 0; 
}
```

下面我们看看 void_t 是怎么生效的。

首先对于这个模板来说，它的模板参数列表有两个，第二个模板参数如果不填的话，那就是默认的 void，所以当 `new_has_reserve< A >::value`去匹配的时候，肯定是符合的，相当于 `new_has_reserve< A, void >::value`。

```cpp
template< class , class = void >
struct new_has_reserve : std::false_type
{ };
```

再来看看另一个模板的匹配情况。

```cpp
template< class T >
struct new_has_reserve< T , void_t< decltype(declval<T&>().reserve() ) > > : std::true_type
{ };
```

`new_has_reserve< A >::value` 去匹配的时候，对于第一个模板参数来说 T 是可以被推导为 A 的；

对于第二个参数实际可以写成 `void_t< decltype(declval<A&>().reserve() )`，declval 上面我们已经讲过了，它可以在某类型没有默认构造函数的情况下，假想出一个该类的对象来进行类型推导，所以 `declval<A&>().reserve()` 实际上是看 A 是否有 reserve 函数，存在则用 decltype 尝试获取 reserve 函数的类型，然后被 void_t 替换成 void 类型，都没问题最后实际上推导出来的结果如下：

```cpp
template< class T >
struct new_has_reserve< A , void ) > > : std::true_type
{ };
```

那也就是说两个模板都可以匹配成功，然后编译器会挑选一个偏特化的模板作为最合适的模板来匹配。

## constexpr

constexpr 它是在 C++ 11 被引进的，它的字面意思是 constant expression，常量表达式。它可以作用在变量和函数上。一个 constexpr 变量是一个编译时完全确定的常数。一个 constexpr 函数至少对于某一组实参可以在编译期间产生一个编译期常数。

需要注意的是 const 并未区分出编译期常量和运行期常量，并且 const 只保证了运行时不直接被修改，而 constexpr 是限定在了编译期常量。在 C++11 以后，建议凡是常量语义的场景都使用 constexpr，只对只读语义使用 const。例如：

```cpp
template<int N> class C{};

constexpr int FivePlus(int x) {
  return 5 + x;
}

void f(const int x) {
  C<x> c1;            
  C<FivePlus(6)> c2;  
} 
```

关于 const 和 constexpr 的提问在 [https://www.zhihu.com/question/35614219](https://www.zhihu.com/question/35614219) 这里讨论了很多，我就不班门弄斧了。

## C++17 & if constexpr

在 C++17 的时候多了 if constexpr 这样的语法，使得模板编程的可读性更好。

我们先看个例子，在 C++11/14 的时候，我们要使用前面讲到的 enable_if 模板的话，通常要实现两个 close_enough 模板：

```cpp
template <class T> constexpr T absolute(T arg) {
   return arg < 0 ? -arg : arg;
}

template <class T> 
constexpr enable_if_t<is_floating_point<T>::value, bool> 
close_enough(T a, T b) {
   return absolute(a - b) < static_cast<T>(0.000001);
}
template <class T>
constexpr enable_if_t<!is_floating_point<T>::value, bool> 
close_enough(T a, T b) {
   return a == b;
}
```

但是在 C++17 中配合 if constexpr 这样的语法可以简化成一个 close_enough 模板，并且将常量抽离出来变成 constexpr 变量：

```cpp
template <class T> constexpr T absolute(T arg) {
   return arg < 0 ? -arg : arg;
}

template <class T>
constexpr auto precision_threshold = T(0.000001);

template <class T> constexpr bool close_enough(T a, T b) {
   if constexpr (is_floating_point_v<T>)  
      return absolute(a - b) < precision_threshold<T>;
   else
      return a == b;
}
```

使用 if constexpr 编译器会在编译的时候计算这个分支是否符合条件，如果不符合条件会做优化丢弃掉这个分支。

## 参考

- [https://izualzhy.cn/SFINAE-and-enable_if](https://izualzhy.cn/SFINAE-and-enable_if)
- [https://zhuanlan.zhihu.com/p/21314708](https://zhuanlan.zhihu.com/p/21314708)
- [https://time.geekbang.org/column/intro/100040501](https://time.geekbang.org/column/intro/100040501)
- [https://stackoverflow.com/questions/9939305/what-is-in-c](https://stackoverflow.com/questions/9939305/what-is-in-c)
- [https://www.zhihu.com/question/51441745](https://www.zhihu.com/question/51441745)
- [https://stdrc.cc/post/2020/09/12/std-declval/](https://stdrc.cc/post/2020/09/12/std-declval/)
- [https://offensive77.plus/index.php/2021/12/04/history-von-sfinae/](https://offensive77.plus/index.php/2021/12/04/history-von-sfinae/)
- [https://www.cppstories.com/2016/02/notes-on-c-sfinae/](https://www.cppstories.com/2016/02/notes-on-c-sfinae/)
- [https://www.cppstories.com/2018/03/ifconstexpr/](https://www.cppstories.com/2018/03/ifconstexpr/)
- [https://stackoverflow.com/questions/27687389/how-does-void-t-work](https://stackoverflow.com/questions/27687389/how-does-void-t-work)
- [https://akrzemi1.wordpress.com/2013/06/20/constexpr-function-is-not-const/](https://akrzemi1.wordpress.com/2013/06/20/constexpr-function-is-not-const/)
- [https://www.zhihu.com/question/35614219](https://www.zhihu.com/question/35614219)
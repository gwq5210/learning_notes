# 从std::distance的源码学习C++模版编程的基本技术

## std::distance的作用

std::distance是STL中的一个模版函数，接收两个迭代器变量作为参数，返回这两个迭代器之间的距离，比如:

```cpp
char a[8];
cout << std::distance(&a[0], &a[1]) << endl;

std::list<int> l{0, 1, 2};
cout << std::distance(l.begin(), l.end()) << endl;

std::map<int, int> m{{0, 0}, {1, 1}};
cout << std::distance(m.begin(), m.end()) << endl;
```

可以看到std::distance可以处理各种不同类型容器的迭代器，包括原生指针。

## 要解决的主要问题

乍看之下，这个函数的实现似乎非常简单，只需要对第一个迭代器不断++，直到等于第二个迭代器为止，返回循环的次数就可以了:

```cpp
template <class Iter>
int distance(Iter first, Iter second) {
  int r{0};
  while(first != second) {
    ++first;
    ++r;
  }
  return r;
}
```

稍加思考后便会想到，这个实现对于原生指针来说，效率是非常低下的，因为如果是原始指针，那么直接返回second - first就可以了，不需要通过循环累加来计算距离。应该为指针类型提供一个特化的版本:

```cpp
template <class Iter>  
int distance(Iter* first, Iter* second) {  
    return second - first;  
}
```

但这只解决了指针的问题，某些容器(最常见的就是std::vector)的迭代器，也是可以直接用减法得到距离的，应该怎么在代码中识别出，传入的迭代器能否直接使用减法来获得距离？

ok，这就是实现std::distance要解决的主要问题了。让我们带着这个问题来看它的源码，我这里是在MacOS下看的clang15自带的STL代码，另外，在C++20引入了concept后，相关实现有了新的版本，这里看的都是c++20以前的实现。

在正式开始读源码之前，需要先了解一下STL中迭代器的分类。

## 基础知识: STL中迭代器的分类

STL中的迭代器，按能力划分为了五类（新的C++标准实际上是六类，这里忽略)：

- 输入迭代器input iterator，能对容器做单次前向只读遍历(只支持++操作)
- 输出迭代器output iterator，能对容器做单次前向只写遍历
- 前向迭代器forward iterator，能对容器做多次前向遍历
- 双向迭代器bidirectional iterator，能对容器做多次前向或后向遍历(可以++也可以--)
- 随机访问迭代器random-access iterator，能对容器做多次前向或后向遍历，也能对容器做随机访问(能通过+n或-n访问任何指定距离的对象，也能通过两个迭代器变量相减获得距离)

迭代器分类的详细介绍可以参考这里[Iterator library - cppreference.com](https://en.cppreference.com/w/cpp/iterator#Iterator%20categories)

STL代码中为每种迭代器都对应定义了一个空的struct，代码文件是`llvm/15.0.7_1/include/c++/v1/__iterator/iterator_traits.h`:

```cpp
struct _LIBCPP_TEMPLATE_VIS input_iterator_tag {};  
struct _LIBCPP_TEMPLATE_VIS output_iterator_tag {};  
struct _LIBCPP_TEMPLATE_VIS forward_iterator_tag       : public input_iterator_tag {};  
struct _LIBCPP_TEMPLATE_VIS bidirectional_iterator_tag : public forward_iterator_tag {};  
struct _LIBCPP_TEMPLATE_VIS random_access_iterator_tag : public bidirectional_iterator_tag {};
```

可以注意到random_access_iterator_tag、bidirectional_iterator_tag、forward_iterator_tag、input_iterator_tag是挨个顺序继承的关系。

通过阅读文档可知，需要随机访问迭代器才能支持使用`second - first`的方式来获取迭代器之间的距离。在后面阅读代码的时候我们能看到，STL是如何使用这些空的tag struct来识别迭代器的能力类型的。

## 开始读代码吧

代码文件是`llvm/15.0.7_1/include/c++/v1/__iterator/distance.h`

```cpp
template <class _InputIter>  
inline _LIBCPP_INLINE_VISIBILITY _LIBCPP_CONSTEXPR_AFTER_CXX14  
typename iterator_traits<_InputIter>::difference_type  
distance(_InputIter __first, _InputIter __last)  
{  
    return _VSTD::__distance(__first, __last, typename iterator_traits<_InputIter>::iterator_category());  
}
```

忽略`_LIBCPP_INLINE_VISIBILITY _LIBCPP_CONSTEXPR_AFTER_CXX14`这两个宏，对理解代码没影响。`_VSTD`实际就是`std`。

可以看到，实际调用的是`std::__distance(__first, __last, typename iterator_traits<_InputIter>::iterator_category())`。

这里对我们理解有阻碍的就是这个`iterator_traits<_InputIter>`了。用到了这个类型内定义的两个类型:`difference_type`和`iterator_category`。

## 搞懂iterator_traits

让我们看看这个类的代码，代码文件是`llvm/15.0.7_1/include/c++/v1/__iterator/iterator_traits.h`:

```cpp
template <class _Iter>  
struct _LIBCPP_TEMPLATE_VIS iterator_traits;

template<class _Tp>  
#if _LIBCPP_STD_VER > 17  
requires is_object_v<_Tp>  
#endif  
struct _LIBCPP_TEMPLATE_VIS iterator_traits<_Tp*>  
{  
    typedef ptrdiff_t difference_type;  
    typedef typename remove_cv<_Tp>::type value_type;  
    typedef _Tp* pointer;  
    typedef _Tp& reference;  
    typedef random_access_iterator_tag iterator_category;  
#if _LIBCPP_STD_VER > 17  
    typedef contiguous_iterator_tag    iterator_concept;  
#endif  
};
  




  
template <class _Iter>  
struct _LIBCPP_TEMPLATE_VIS iterator_traits  
    : __iterator_traits<_Iter, __has_iterator_typedefs<_Iter>::value> {  
  using __primary_template = iterator_traits;
};
```

首先看第1-2行，声明了类模版iterator_traits，有一个模版参数_Iter。

第4-18行（第5-7是c++20中的concept，忽略），为模版参数_Iter为指针时定义了一个特化版本，就是定义了iterator_traits内的iterator_category、difference_type、value_type、reference、pointer分别是什么类型。

从这些类型的名字就能看出是什么意思：

- difference_type - 两个迭代器之间距离的类型(一般是某种int，这里的ptrdiff_t在我的系统里是long的一个typedef)
- value_type - 迭代对象的类型，移除了cv(const和volatile)的限定
- pointer - 迭代对象指针的类型
- reference - 迭代对象引用的类型
- iterator_category - 迭代器的所属分类对应的tag struct类型，就是前面说5类(新标准是6类)中的某一个，可以看到，这里是random_access_iterator_tag，也就是随机访问迭代器

第25-29行，是一个更通用的版本，当_Iter不是指针类型时就会匹配到这里，可以看到就是简单的继承了__iterator_traits，自己本身只是加了一个__primary_template的类型定义。

从这几行来看，__iterator_traits类有两个模版参数，第一个_Iter就是迭代器的类型，第二个比较奇怪一点__has_iterator_typedefs<_Iter>::value，__has_iterator_typedefs应该是个类模版，模版参数传的是迭代器类型_Iter，我们继续跳过去看看这个模版类的代码，主要是看看这个value是什么，怎么推导的。

```cpp
template <class _Tp>  
struct __has_iterator_typedefs  
{  
private:  
    template <class _Up> static false_type __test(...);  
    template <class _Up> static true_type __test(typename __void_t<typename _Up::iterator_category>::type* = 0,  
                                                 typename __void_t<typename _Up::difference_type>::type* = 0,  
                                                 typename __void_t<typename _Up::value_type>::type* = 0,  
                                                 typename __void_t<typename _Up::reference>::type* = 0,  
                                                 typename __void_t<typename _Up::pointer>::type* = 0);  
public:  
    static const bool value = decltype(__test<_Tp>(0,0,0,0,0))::value;  
};
```

第5行声明了一个返回值是`false_type`的方法`__test`，参数是可变的，我们称这个为版本一

第6行声明了一个更特殊版本的方法`__test`，返回值是`true_type`，我们称为版本二，这个版本的声明有5个参数，每个参数都是`typename __void_t<typename _Up::xxx>::type*`，看起来很奇怪，可以看看这个`__void_t`是什么:

```cpp
template <class>  
struct __void_t { typedef void type; };
```

这个`__void_t`只是在内部定义了一个类型`type`，就是`void`。其他什么都没有。

那么回到6-10行的那几个参数定义，就能看出，其实这5个参数都是`void*`，但前提是传给`__void_t`的模版参数是合法的，也就是说，如果模版参数_Up存在iterator_category、difference_type、value_type、reference、pointer这五个类型的定义，那么__void_t就可以推导成功，从而使得版本二的`__test`被匹配，否则就会推导失败，从而匹配到第5行那个默认的版本，这就是C++的`SFINAE`机制

回到第12行，可以看到调用__test的时候，传的模版参数是_Tp，也就是迭代器的类型，传的函数参数是5个0，参数数目符合版本二的声明，编译器会先尝试按版本二去推导，如果_Tp类型内定义了iterator_category、difference_type、value_type、reference、pointer这五个类型，那么就匹配到了版本二，decltype得到的就是true_type，value就等于true_type::value；否则，就匹配到了版本一，decltype得到的是版本一，value就等于false_type::value。

最后我们来看看true_type::value和false_type::value到底是什么。

```cpp
template <class _Tp, _Tp __v>  
struct _LIBCPP_TEMPLATE_VIS integral_constant  
{  
  static _LIBCPP_CONSTEXPR const _Tp      value = __v;  
  typedef _Tp               value_type;  
  typedef integral_constant type;  
  _LIBCPP_INLINE_VISIBILITY  
  _LIBCPP_CONSTEXPR operator value_type() const _NOEXCEPT {return value;}  
#if _LIBCPP_STD_VER > 11  
  _LIBCPP_INLINE_VISIBILITY  
  constexpr value_type operator ()() const _NOEXCEPT {return value;}  
#endif  
};

typedef integral_constant<bool, true>  true_type;  
typedef integral_constant<bool, false> false_type;
```

模版类integral_constant有两个模版参数，第一个是类型，第二个是对应类型的值，内部有一个static const的成员变量。true_type和false_type就是这个模版类的两个实例，第一个参数类型是bool，第二个参数分别是true和false。所以true_type::value就是true，false_type::value就是false。

看到这里可能会感到奇怪，为什么要绕这么大圈，为什么两个版本的__test()不直接返回true和false？原因在于，如果返回的是true/false，那么就无法在编译期获得具体的值，而只能在运行时得到。在编译期只能知道返回值的数据类型，通过定义true_type和false_type这两个不同的类型，就能在编译期通过decltype获得我们想要的结果。在模版编程的世界里，关注的往往都是变量、函数、类的类型信息，而不是值或实现，因为类型信息可以在编译期获得。像上面那个__has_iterator_typedefs中的__test()就是只有声明而没有实现，这里可以好好思考体会一下。

到这里，我们回头看一下__has_iterator_typedefs<_Iter>::value，其实就是，如果_Iter类型内定义了iterator_category、difference_type、value_type、reference、pointer这五个类型，那么就是true，否则就是false，这是个编译期就可以得到的值。

这个弄清楚后就可以接着看了，再贴一遍代码:

```cpp
template <class _Iter>  
struct _LIBCPP_TEMPLATE_VIS iterator_traits  
    : __iterator_traits<_Iter, __has_iterator_typedefs<_Iter>::value> {  
  using __primary_template = iterator_traits;
};
```

我们看到第8行，__iterator_traits<_Iter, __has_iterator_typedefs<_Iter>::value>，弄清楚了其中的__has_iterator_typedefs<_Iter>::value，在_Iter有迭代器所需的5个类型定义时就是true，否则是false。接下来就可以继续看__iterator_traits到底是什么了。

```cpp
template <class _Iter, bool> struct __iterator_traits {};  
  
template <class _Iter, bool> struct __iterator_traits_impl {};  
  
template <class _Iter>  
struct __iterator_traits_impl<_Iter, true>  
{  
    typedef typename _Iter::difference_type   difference_type;    
    typedef typename _Iter::value_type        value_type;    
    typedef typename _Iter::pointer           pointer;    
    typedef typename _Iter::reference         reference;    
    typedef typename _Iter::iterator_category iterator_category;
};  
  
template <class _Iter>  
struct __iterator_traits<_Iter, true>  
    :  __iterator_traits_impl      
      <        
        _Iter,        
        is_convertible<typename _Iter::iterator_category, input_iterator_tag>::value ||        
        is_convertible<typename _Iter::iterator_category, output_iterator_tag>::value 
      >
{};
```

第1行定义了一个空的__iterator_traits，接收两个模版参数，第一个是迭代器类型，第二个是个bool的值，传入的就是迭代器类型是否定义了那五个内置类型。

第15-23行，为第二个参数为true时，定义了一个特化的版本，继承自__iterator_traits_impl，传给这个类模版的第二个参数看起来比较怪`is_convertible<typename _Iter::iterator_category, input_iterator_tag>::value || is_convertible<typename _Iter::iterator_category, output_iterator_tag>::value`。

这里就不再看is_convertible的代码了，通过搜索C++的文档可以知道，这个类模版是用来判断第一个模版参数类型能不能隐式转换为第二个模版参数类型的，所以，上面那个奇怪的表达式的意思是：如果_Iter::iterator_category可以隐式转换为input_iterator_tag或output_iterator_tag，那么就为true，否则就为false。实际上从前面的介绍可以知道，STL代码里定义的那6个tag都满足这个要求，所以只要_Iter::iterator_category是其中的任何一个，这里就为true。

我们再来看看__iterator_traits_impl，这个也一样是个模版类，同样有两个模版参数，第一个是迭代器类型第二个是bool值，也同样有一个空的默认定义(第6行)，和一个为true定义的特化版本(第8-16行)，这个特化的版本就是把_Iter的iterator_category、difference_type、value_type、reference、pointer在自己内部又定义了一遍。

看到这里，我们就基本看完了iterator_traits的代码，可以总结一下:

- iterator_traits<_Iter>在传入的_Iter是指针类型时，有一个特化版本，在内部定义了iterator_category、difference_type、value_type、reference、pointer这5个类型，其中iterator_category为random_access_iterator_tag
- iterator_traits<_Iter>在传入的_Iter不是指针，且_Iter定义了iterator_category、difference_type、value_type、reference、pointer这5个类型，且_Iter::iterator_category是STL预定义的迭代器tag struct之一时，就直接使用_Iter的5个定义作为自己的定义
- iterator_traits<_Iter>在传入的_Iter不是指针，且_Iter没有定义全iterator_category、difference_type、value_type、reference、pointer这五个类型，或者_Iter::iterator_category不是STL预定义的tag struct时，iterator_traits<_Iter>是个空的struct

可以看出来，如果要自己写一个迭代器类，那么就需要在内部定义iterator_category、difference_type、value_type、reference、pointer这5种类型，其中iterator_category用来标记迭代所属的类型和能力。

既然要求迭代器都提供这5个类型定义，那为什么不直接用，而是要弄个iterator_traits模版类呢，原因就在于，有了这个中间层后，可以为原始指针这种无法提供这5种类型定义的类型也提供适配，即使传入的类型不满足迭代器的条件（没有那5个定义），也可以通过提供一个特化版本的iterator_category来适配。

到这里，我们就清楚std::__distance(__first, __last, typename iterator_traits<_InputIter>::iterator_category())中的typename iterator_traits<_InputIter>::iterator_category()是什么了: 如果传入的_InputIter是指针，那么这个就是random_access_iterator_tag的实例；如果传入的是一个合法的迭代器，那么这个就是_InputIter::iterator_category的实例；如果都不是，那么会推导失败导致编译失败。

我们最后来看std::__distance做了什么。

## std::__distance

```cpp
template <class _InputIter>  
inline _LIBCPP_INLINE_VISIBILITY _LIBCPP_CONSTEXPR_AFTER_CXX14  
typename iterator_traits<_InputIter>::difference_type  
__distance(_InputIter __first, _InputIter __last, input_iterator_tag)  
{  
    typename iterator_traits<_InputIter>::difference_type __r(0);  
    for (; __first != __last; ++__first)  
        ++__r;  
    return __r;  
}  
  
template <class _RandIter>  
inline _LIBCPP_INLINE_VISIBILITY _LIBCPP_CONSTEXPR_AFTER_CXX14  
typename iterator_traits<_RandIter>::difference_type  
__distance(_RandIter __first, _RandIter __last, random_access_iterator_tag)  
{  
    return __last - __first;  
}
```

这个代码很好理解，std::__distance有两个版本: 如果传入的第三个参数是input_iterator_tag类型或可以隐式转换为该类型时，就使用循环++的方式计算距离；当传入的第三个参数是random_access_iterator_tag类型或可以隐式转换为该类型时，就使用减法直接得到距离。由c++函数重载的推导规则可以知道，当这两个都满足时，第二个版本更特殊(random_access_iterator_tag是input_iterator_tag的子类)，会优先选择第二个版本。第三个参数是由iterator_traints<_Iter>::iterator_category提供的。

可以想一下，如果传入的第三个参数是output_iterator_tag会怎么样？从tag struct的定义可以看到，output_iterator_tag无法隐式转换为input_iterator_tag，从而会匹配失败，也就是说，output_iterator是不能使用std::distance的。

## 总结

在搞清楚上面那些细节后，回过头看，std::distance的实现还是比较简单的，就是用iterator_traits模版类获得迭代器所属的类型，然后把这个类型的实例作为参数传给std::__distance，std::__distance有两个实现的版本，对于迭代器类型实例是random_access_iterator_tag的，就直接相减得到距离；默认的就使用循环++的方式得到距离。

通过阅读源码，我们学习到了c++模版编程中的几种基本技巧的运用，包括

- 利用SFINAE特性来识别类型是否有定义(__has_iterator_typedefs的相关实现)
- type traits的作用和使用(iterator_traits的相关实现)
- 使用type trait获得类型的能力分类，再利用特化/重载为不用能力的类型提供不同的实现(std::__distance)
- 模版编程中的一些基本工具技巧(true_type、false_type、__void_t这些)
- 要实现自定义的迭代器，需要在类内部定义iterator_category、difference_type、value_type、reference、pointer这5个类型

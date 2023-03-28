# Effective C++总结1

## Accustoming Yourself to C++

### 1. View C++ as a federation of languages

将C++视为多种相关语言组成的联邦，在其某个次语言中，各种守则都倾向简单易懂并容易记住，然而当你从一个次语言转移到另一个次语言时，守则可能改变

- C
- Object-Oriented C++
- Template C++
- STL

### 2. Prefer consts, enums, and inlines to #defines

- `#define` 是预处理指令，而不是语言特性
- 对于常量，最好使用 `const` 对象或者 `enum`，而不是 `#define`
- 对于形似函数的宏，最好使用 `inline` 函数，而不是 `#define`

### 3. Use const whenever possible

- `const` 可被施加于任何作用域内的对象、函数参数、函数返回类型、成员函数本体
- 编译器强制执行 `bitwise constness`，但不强制执行 `logical constness`，可以考虑使用 `mutable` 关键字实现概念上的常量性
- 当 `const` 和 `non-const` 成员函数有着实质等价的实现时，令 `non-const` 版本调用 `const` 版本可避免代码重复

### 4. Make sure that objects are initialized before they're used

- 对象的成员变量初始化动作发生在进入构造函数本体之前，构造函数内的动作更准确的应该叫做赋值动作
- `class` 的构造函数最好使用成员初始化列表，成员变量总是以声明顺序初始化
- 为内置型对象进行手工初始化，因为 `C++` 不保证初始化他们
- 函数内的 `static` 对象被称为 `local static` 对象，其他 `static` 对象被称为 `non-local static` 对象
- `C++` 对于“定义于不同编译单元内的 `non-local static` 对象”的初始化顺序是未定义的
  - 因此常用手法是利用 `Singleton` 模式将 `non-local static` 对象替换为 `local static` 对象
  - 这个手法的基础在于：`C++` 保证，函数内的 `local static` 对象会在“该函数被调用期间”“首次遇上该对象之定义式”时被初始化

## Constructors, Destructors, and Assignment Operators

### 5. Know what functions C++ silently writes and calls

- 编译器会为 `class` 生成 `default constructor`、`copy constructor`、`copy assignment operator`、`destructor`，所有这些函数都是 `public` 且 `inline` 的
- `default` 构造函数和析构函数会调用 `base class` 和 `non-static` 成员变量的构造函数和析构函数
- 编译器生成的析构函数是 `non-virtual` 的，除非这个 `class` 的 `base class` 自身声明有 `virtual` 析构函数

### 6. Explicitly disallow the use of compiler-generated functions you do not want

- `C++11` 中，可以使用 `=delete` 关键字显式禁用某个函数
- `C++98` 中，可以将某个函数声明为 `private` 且不实现

### 7. Declare destructors virtual in polymorphic base classes

- 带多态性质的 `base class` 应该声明 `virtual` 析构函数，以确保其 `derived class` 的析构函数被调用
- 如果一个 `class` 带有任何 `virtual` 函数，那么它应该有 `virtual` 析构函数

### 8. Prevent exceptions from leaving destructors

- 析构函数不应该抛出异常，如果一个被析构函数调用的函数可能抛出异常，析构函数应捕捉任何异常，然后吞掉异常或者结束程序

### 9. Never call virtual functions during construction or destruction

- `derived class` 对象内的 `base class` 成分会在 `derived class` 自身的成分被构造之前先行构造妥当
  - 换句通俗的话说，在 `base class` 构造期间，`virtual` 函数不是 `virtual` 的
  - 更根本的原因是，在 `derived class` 对象的 `base class` 构造期间，对象的类型是 `base class`，而不是 `derived class`，不止 `virtual` 函数会被编译器解析至 `base class`，其运行期类型信息也会把对象视为 `base class` 类型
- 解决办法之一是，既然你无法使用 `virtual` 函数从 `base class` 向下调用，那就在构造期间令 `derived class` 将必要的构造信息向上传递至 `base class` 构造函数

### 10. Have assignment operators return a reference to *this

- 赋值操作符应该返回一个指向自身的引用，以便于链式赋值

### 11. Handle assignment to self in operator=

- 确保当对象自我赋值时 `operator=` 有良好行为，其中技术包括几种
  - 比较“来源对象”和“目标对象”的地址，如果相同则直接返回
  - 精心周到的语句顺序，例如先“记住”原有对象，然后“复制”新值，最后“销毁”原有对象
  - 利用 `copy-and-swap` 技术
- 确定任何函数如果操作一个以上的对象，而其中多个对象是同一个对象时，其行为仍然正确

### 12. Copy all parts of an object

- 任何时候为 `derived class` 对象撰写 `copying` 函数，都必须谨慎的将 `base class` 部分一并复制，你应该让 `derived class` 的 `copying` 函数调用相应的 `base class` 函数
  - 保证复制所有的 `local` 成员变量
  - 保证调用所有 `base class` 内适当的 `copying` 函数
- 尽管 `copy` 构造函数和 `copy assignment` 操作符往往有着近似的实现本体，但你绝不应该令两者互相调用
  - 如果你想要消除两者之间重复的代码，建立一个新的成员函数给两者调用，**通常是 `private` 函数且被命名为 `init`**

## Resource Management

### 13. Use objects to manage resources

- 为防止资源泄露，请使用 `RAII`（`Resource Acquisition Is Initialization`）对象，它们在构造函数中获取资源并在析构函数中释放资源
- 书中介绍可以考虑使用 `STL` 库提供的 `auto_ptr` 等智能指针来管理资源
  - 早期的 `C++` 中，`auto_ptr` 是唯一的智能指针，但是它有着一些缺陷，例如不支持 `array`、严格所有权的复制等
  - 注意其实 `C++11` 已经废弃了 `auto_ptr`，建议使用 `unique_ptr` 或者 `shared_ptr`，后者也增加了对 `array` 的支持

### 14. Think carefully about copying behavior in resource-managing classes

- 通常的 `RAII class copying` 的行为包括以下几种
  - 禁止复制
  - 对底层资源使用“引用计数法”
  - 复制底层资源
  - 转移底层资源的所有权
- 复制RAII对象必须一并复制它所管理的资源，所以资源的 `copying` 行为决定 `RAII` 对象的 `copying` 行为

### 15. Provide access to raw resources in resource-managing classes

- `APIs` 往往要求访问原始资源，因此每一个 `RAII class` 都应该提供一个取得其所管理资源的办法
- 对原始资源的访问可能经由显示转换或隐式转换，一般而言显示转换更为安全，但隐式转换更为方便

### 16. Use the same form in corresponding uses of new and delete

- 当你使用 `new` 关键字时，有两件事发生
  - 一是分配内存（通过名为 `operator new` 的函数）
  - 二是针对此内存会有一个或多个构造函数被调用
- 当你使用 `delete` 关键字时，也有两件事发生
  - 一是有一个或多个析构函数被调用
  - 二是然后内存被释放（通过名为 `operator delete` 的函数）
- 如果你在 `new` 表达式使用了 `[]`，那么你也应该在 `delete` 表达式使用 `[]`，反之亦然，不要混用

### 17. Store newed objects in smart pointers in standalone statements

- 以独立语句将 `newed` 对象存储于智能指针中
- 如果不这样做，一旦一个复杂的语句次序被重排，中间某一步的异常被抛出，有可能导致难以察觉的资源泄露

## Designs and Declarations

### 18. Make interfaces easy to use correctly and hard to use incorrectly

- 好的接口很容易被正确使用，不容易被错误使用
  - 促进正确使用的办法包括接口的一致性，以及于内置类型的行为兼容
  - 阻止错误使用的办法包括建立新类型、限制类型上的操作、束缚对象值以及消除用户的资源管理责任
  - `tr1::shared_ptr` 支持定制型删除器，这也可防范 `“Cross-DLL problem”`，可被用来自动解除互斥锁等

### 19. Treat class design as type design

- 在你想设计一个优秀的 `class` 之前，你必须首先思考和回答以下问题
  - 新 `type` 的对象应该如何被创建和销毁？
    - 这将影响对象的构造函数、析构函数、内存分配函数、内存释放函数
  - 对象的初始化和赋值该有什么样的差别？
  - 新 `type` 对象如果被 `passed by value`，意味着什么？
  - 什么是新 `type` 的合法值？
    - 对于 `class` 的成员变量来说，通常只有有限数据集是有效的
    - 你必须精心设计成员函数的约束条件检查工作，尤其是构造函数和赋值操作符等
  - 新的 `type` 需要配合某个继承图系（`inheritance graph`）吗？
    - 如果需要，你就会受到这些 `classes` 的设计约束，你的设计也会影响继承新 `type` 的 `classes`
  - 新的 `type` 需要什么样的转换？
    - 如果你允许隐式转换，就必须设计相应的类型转换函数（`operator T()`）
    - 如果你只允许显示转换，就必须设计专门负责执行转换的函数
  - 什么样的操作符和函数对新 `type` 而言时合理的？
  - 什么样的标准函数应该被驳回？
  - 谁该取用新 `type` 的成员？
  - 什么是新 `type` 的未声明接口（`undeclared interface`）？
  - 新 `type` 有多么一般化？
    - 或许你并非定义一个新 `type`，而是定义一整个 `types` 家族
    - 若果真如此，则你应该考虑定义一个新的 `class template`
  - 你真的需要一个新的 `type` 吗？
    - 是否单纯的定义多个 `non-member` 函数或 `template` 函数更能达到你的目标？
- `Class` 的设计就是 `type` 的设计，在你定义新的 `type` 之前，请确定你已经考虑过了上述所有问题

### 20. Prefer pass-by-reference-to-const to pass-by-value

- `pass-by-value` 的代价很高，因为它需要复制对象，并递归的复制对象的所有成员
- `pass-by-reference` 不仅效率更高，还可以避免 `slicing`（对象切割）问题
  - 当一个 `derived class` 对象以 `by value` 方式传递并被当作 `base class` 对象时，`base class` 的 `copy` 构造函数会被调用，这将导致 `derived class` 的特化性质全被切割掉
- `pass-by-reference` 本质是通过指针实现的，因此往往并不适用于内置类型、`STL` 迭代器和函数对象
  - `STL` 迭代器是一种泛型指针，行为与指针类似
  - 函数对象是一种仿函数，行为与函数类似，一般没有构造函数和析构函数

### 21. Don’t try to return a reference when you must return an object

- 函数的返回值，绝对不要执行以下操作
  - 返回 `pointer` 或 `reference` 指向 `local stack` 对象
  - 返回 `reference` 指向 `heap-allocated` 对象
  - 返回 `pointer` 或 `reference` 指向 `local static` 对象，而有可能需要多个这样的对象

### 22. Declare data members private

- 切记将成员变量声明为 `private`
  - 赋予用户访问数据一致性
  - 可细微划分访问控制
  - 允诺约束条件获得保证
  - 为 `class` 作者提供充分的实现弹性

### 23. Prefer non-member non-friend functions to member functions

- 让我们从封装开始讨论，首先，越多的东西被封装，越少人可以看到它，我们改变这些东西的能力就越大，改变时就能影响越少的用户
  - 现在考虑对象内的数据，越少代码可以看到数据，越多的数据被封装，我们就能越自由的改变对象数据，通过计算能够访问该数据的函数数量就能作为一种粗糙的量测，因此成员变量应该是 `private` 的，否则就有无限量的函数可以访问它们
  - 因此，现在让你在 `member` 函数和 `non-member` 函数之间做选择，两者提供完全相同的机能，那么导致较大封装性的毫无疑问是 `non-member non-friend` 函数，因为其并不增加“能够访问 `class` 内 `private` 成分”的函数数量
- 在 `C++` 中，比较自然的做法是让该类函数成为 `non-member` 函数并位于相关联 `class` 所在的同一个 `namespace`
  - 另一个优势是，将不同分类的便利函数放在多个头文件内但隶属于同一个命名空间，可以降低编译依存性，并且可以让用户自由选择需要的函数
- 现在，你应该能够理解这种反直觉的行为，即宁可用 `non-member non-friend` 函数替换 `member` 函数，这样可以增加封装性、包裹弹性和机能扩充性

### 24. Declare non-member functions when type conversions should apply to all parameters

- 假设现有一个 `class Number`，该 `class` 允许 `“int-to-Number”` 隐式转换，你需要为其实现一个 `operator*` 操作
  - 此时你的直觉告诉你应该保持面向对象精神，将其实现为成员函数，写法为`const Number operator* (const Number& rhs) const`
    - 很快你就会发现，当你尝试混合式算术时只有一半行得通，即 `Number * 2` 行得通，但 `2 * Number` 却会出错，如果你以函数形式重写两式为 `Number.operator*(2)` 和 `2.operator*(Number)` ，问题一目了然
    - 结论是，只有当参数被列于参数列表内，这个参数才是隐式类型转换的合格参与者，而“被调用之成员函数所隶属的那个对象”，即 `this` 对象这个隐喻参数，绝不是隐式转换的合格参与者，这也解释了为什么 `2 * Number` 为什么会出错，此时你并能指望编译器自动将数字隐式转换为 `Number`，然后调用 `operator*` 成员函数
  - 最终，可行之道拨云见日，让 `operator*` 成为一个 `non-member` 函数，这允许编译器在每一个实参身上执行隐式转换，写法为 `const Number operator* (const Number& lhs, const Number& rhs)`
- 最后，请记住，如果你需要为某个函数的所有参数（包括被 `this` 指针所指的那个隐喻参数）进行类型转换，那么这个函数必须是个`non-member`函数

### 25. Consider support for a non-throwing swap

- 通常针对对象的做法是将 `std::swap` 进行模板全特化（`total template specialization`）
  - 为了与 `STL` 容器保持一致，我们令对象实现一个名为 `swap` 的 `public` 成员函数，然后令特化版本的 `std::swap` 调用该成员函数
  - 通常我们不被允许改变 `std` 命名空间的任何东西，但可以为标准 `templates` 制造特化版本
- 对于 `class templates` 而言，我们需要声明一个 `non-member swap` 模板函数，但是不能将其声明为 `std::swap` 的特化版本
  - 因为 C++ 只允许对 `class templates` 偏特化（`partial specialization`），而不允许对 `function templates` 偏特化
  - 虽然我们声明的 `swap` 模板函数不在 `std` 空间内，但 `C++` 依据 `argument-dependent lookup` 规则，仍能调用我们所定义的专属版本
  - 需要注意的是，不要为调用添加额外修饰符，如 `std::swap(a, b)`，这将强迫编译器调用 `std` 内的 `swap` 函数（包括其任何模板特化）
- 现在，让我们对整个形势进行总结
  - 首先如果 `std::swap` 的缺省实现能够满足你的需求，你不需要做任何额外的工作
  - 但是如果其效率不足（那几乎总是意味着你的 `class` 或 `template` 使用了某种 `pimpl`（`pointer to implementation`）手法）
  - 提供一个 `public swap` 成员函数，实现高效的 `swap` 操作，但是不要让函数抛出异常
  - 在你的 `class` 或 `template` 所在命名空间提供一个 `non-member swap`，令其调用上述 `public swap` 成员函数
  - 如果你正在编写一个 `class` 而非 `template`，为你的 `class` 特化 `std::swap`，令其调用 `public swap` 成员函数
  - 最后，如果你调用 `swap` 函数，请确定包含一个 `using` 声明，令 `std::swap` 在你的函数内部可见，然后不加任何修饰符地调用 `swap` 函数

## Implementations

### 26. Postpone variable definitions as long as possible

- 尽可能延后定义的真正意义是
  - 不仅应该延后变量的定义，直到非要使用变量的前一刻为止
  - 甚至应该尝试延后定义直到能够赋予其“具明显意义之初值”实参为止，这样能够避免构造和析构非必要对象
- 然而对于循环，需要单独考虑两种情况
  - 对于将变量定义于循环外，成本为：一次构造、一次析构、`n`次赋值
  - 对于将变量定义于循环内，成本为：`n`次构造、`n`次析构
  - 因此如果对象的赋值成本低于一组构造和析构的成本，那么应该考虑将变量定义于循环外
  - 否则，应该将变量定义于循环内，这种做法也能够保证变量的作用域不会超出循环体

### 27. Minimize casting

- C++提供四种新式转型
  - `const_cast` 通常用来实现常量性移除
  - `dynamic_cast` 通常用来执行安全向下转型，它是唯一无法由旧式语法执行的动作，但是可能消耗重大运行成本
  - `reinterpret_cast` 意图执行低级转型，实际动作可能取决于编辑器，也表示其不可移植
  - `static_cast` 用来执行强迫隐式转换
- C++中单一对象在不同类型的情况下，可能拥有一个以上的地址
  - 例如以“`Base*`指向它”时的地址和以“`Derived*`指向它”时的地址，尤其是在使用多重继承时，这种情况尤为常见
  - 这意味着“由于知道对象如何布局”而设计的转型操作，在不同编译器上可能会有不同的结果
- `derived class` 重写 `base class` 的虚函数后，希望调用 `base class` 中对应虚函数的方法
  - 切勿以 `static_cast<Base>(*this).Func()` 的方式调用 `base class` 的虚函数
    - 此方法并非在当前对象身上调用 `base class` 的虚函数，而是在“当前对象之 `base class` 成分”的副本上调用的函数
  - 正确的方法是使用 `Base::Func()`，明确的告诉编译器，我要调用的是 `base class` 的函数
- `dynamic_cast` 存在执行时较大的开销，有两个一般性的做法可以避免它
  - 其一，是使用容器并在其中存储直接指向 `derived class` 的指针，如果要处理多种类型，你可能需要多个容器
  - 其二，是设计通过 `base class` 中的接口处理“所有可能之派生类的行为”，这样就可以通过 `base class` 调用所有派生类的函数
- 尽量避免转型，如果转型时必要的，试着将其隐藏于某个函数背后，用户不必将转型放进自己的代码中
- 宁可使用 `C++` 的新式转型，而不是旧式转型，因为新式转型的行为更加明确，有着分门别类的职责

### 28. Avoid returning handles to object internals

- 尽量避免返回 `handles`（包括`references`、指针、迭代器）指向对象内部
- 这样做可以增加封装性，帮助 `const` 成员函数实现其目标
- 也可以避免对象被销毁时，`handle` 指向的内存被释放，发生悬挂指针（`dangling handles`）问题

### 29. Strive for exception-safe code

- 带有异常安全的函数会做到：不泄露任何资源、不允许数据败坏
- 异常安全函数提供以下三个保证之一
  - 基本保证：如果异常被抛出，程序内的任何事物仍然保持在有效的状态下，然而程序的现实状态不可预料
  - 强烈保证：如果异常被抛出，程序状态不改变，函数成功就是完全成功，失败会回复到函数调用之前的状态
  - 不抛出保证：承诺绝不抛出异常，因为它们总是能够完成承诺的功能，其实更准确的说法是如果其抛出异常，将是严重错误
- 强烈保证往往能够以 `copy-and-sweep` 来实现，但其强烈保证并非对所有函数都可实现或具备现实意义
- 函数提供的异常安全保证通常最高只等于其所调用各个函数的异常安全保证中的最弱者

### 30. Understand the ins and outs of inlining

- 不要过度热衷inline函数，因为其会造成代码膨胀，从而可能导致额外的换页行为，降低指令高速缓存的击中率
- `inline` 函数只是对编译器的建议，并非强制命令，大部分编译器拒绝将太过复杂的函数 `inlining`，而所有对 `virtual` 函数的调用（除非是最平淡无奇的）也都会使 `inlining` 落空，因为 `virtual` 意味着直到运行期才能确定调用哪个函数，而 `inline` 意味着执行前先将调用动作替换为被调用函数的本体
  - 隐喻声明 `inline` 函数的方式是将其定于于 `class` 的定义式内，明确的 `inline` 函数的方式是在函数定义式前加上 `inline` 关键字
  - 有时候编译器虽有意愿 `inlining` 某个函数，还是可能为函数生成一个本体，例如程序要获得某个 `inline` 函数的地址，编译器通常必须为此函数生成一个函数本体
- 值得注意的是，`inline` 函数和 `template` 函数通常都被定义于头文件中，但是 `template` 函数并非一定是 `inline` 的
  - `inline` 函数通常一定被置于头文件内，因为大多数编译器为了将“函数调用”替换为“被调用函数本体”，必须知道函数定义式，因此 `inlining` 大多是编译期行为
  - `template` 通常也被置于头文件内，因为它一旦被使用，编译器为了将其具现化，同样必须知道函数定义式
  - 但是 `template` 的具现化与 `inlining` 无关，如果你认为某个 `template` 函数应该被 `inlining`，请明确的将其声明为 `inline`
- 构造函数和析构函数通常是 `inline` 的糟糕候选人，因为编译器可能以精致复杂的代码来实现对象创造和销毁时的各种保证，而这些代码可能就放在你的构造函数和析构函数中

### 31. Minimize compilation dependencies between files

- 编译器依存性最小化的本质正是在于“声明的依存性”替换“定义的依存性”，尽量让头文件自我满足，如果做不到则让它与其他文件内的声明式（而非定义式）相依赖
- 如果使用 `object references` 或 `object pointers` 可以完成任务，就不要使用 `objects`
  - 你可以只靠一个类型声明式就定义出指向该类型的 `references` 和 `pointers`，但如果定义了某类型的 `objects`，就必须用到该类型的定义式
- 如果能够，尽量以 `class` 声明式替换 `class` 定义式
  - 注意，当声明一个函数而它用到某个 `class` 时，并不需要该 `class` 的定义，纵使函数以 `by value` 方式传递类型的参数（或返回值）
  - 或许你会惊讶为何不需要知道定义细节，但事实是，一旦任何人调用这些函数，调用之前 `class` 的定义式就必须先曝光才行
- 为声明式和定义式提供不同的头文件
  - 这两个文件必须总是保持一致性，而程序库的用户总是应该 `include` 那个声明式的头文件而非前置声明若干函数
  - 只含声明式的头文件命名方式参考 `C++` 标准程序库头文件 `<iosfwd>`，其包含 `iostream` 各组件的声明式
- 通常利用 `Handle classes` 和 `Interface classes` 解除接口和实现之间的耦合关系，从而降低文件间的编译依存性
  - 代价是运行期丧失若干速度，又为每个对象超额付出若干内存
  - 对于 `Handle classes`，成员函数必须通过 `implementation pointer` 取得对象数据，且必须初始化并指向动态分配而来的 `object`
  - 对于 `Interface classes`，由于每个函数都是 `virtual`，所以每次函数调用必须付出间接跳跃的开销，且派生对象必须包含一个 `vptr`（`virtual pointer table`）

## Inheritance and Object-Oriented Design

### 32. Make sure public inheritance models "is-a"

- `public` 继承意味 `is-a` 关系，适用于 `base class` 身上的每一件事情一定也适用于 `derived class`，因为每一个 `derived class` 对象也都是一个 `base class` 对象

### 33. Avoid hiding inherited names

- `derived class` 内的名称会遮掩 `base class` 内的名称，在 `public` 继承下从来没有人希望如此
- 为了让被遮掩的名称再见天日，可使用 `using` 声明式或 `forwarding function`
  - `using` 声明式的语法是 `using base::func`;，其作用是让 `base class` 内所有名为的 func 的函数在 `derived class` 作用域内可见并且 `public`
  - `forwarding function` 的语法是 `type func(parameter list) { return base::func(parameter list); }`，现在只有某个对应参数版本的 `func` 函数在 `derived class` 中才可见

### 34. Differentiate between inheritance of interface and inheritance of implementation

- 接口继承和实现继承不同，在 `public` 继承下，`derived class`总是继承 `base class` 的接口
- `pure virtual` 函数只具体指定接口继承，`impure virtual` 函数具体指定接口继承及其缺省实现继承
- `non-virtual` 函数具体指定接口继承及其强制性实现继承

### 35. Consider alternatives to virtual functions

- 不妨考虑 `virtual` 函数的替代方案
  - 使用 `non-virtual interface`（`NVI`）手法，这是 `Template Method` 设计模式的一种特殊形式，它以 `public non-virtual` 成员函数包裹较低访问性（`private`或`protected`）的 `virtual` 函数
  - 将 `virtual` 函数替换为函数指针成员变量，这是 `Strategy` 设计模式的一种分解表现形式
  - 将继承体系内的 `virtual` 函数替换为另一个继承体系内的 `virtual` 函数，这是 `Strategy` 设计模式的传统实现手法
- 将机能从成员函数移到 `class` 外部函数，带来的缺点是，非成员函数将无法访问 `class` 的 `non-public` 成员

### 36. Never redefine an inherited non-virtual function

- `non-virtual` 函数是静态绑定（`statically bound`），而 `virtual` 函数是动态绑定（`dynamically bound`）

### 37. Never redefine a function's inherited default parameter value

- `virtual` 函数是动态绑定（`dynamically bound`），而缺省参数值却是静态绑定（`statically bound`）
  - 静态绑定又名前期绑定，动态绑定又名后期绑定
  - 对象的静态类型（`static type`）是其在程序中被声明时所采用的类型
    - 如 `Shape* ps = new Circle;`，`ps` 的静态类型是 `Shape*`
  - 而对象的动态类型（`dynamic type`）则是指目前所指向对象的实际类型，也就是说动态类型可以表现出一个对象实际将会有什么行为，动态类型可在程序执行过程中改变（通常是经由赋值操作）
    - 如 `Shape* ps = new Circle;`，`ps` 的动态类型是 `Circle*`
- 至于 `C++` 为何会以这种方式运作，答案在于运行期效率，如果缺省参数值是动态绑定的，编译器就必须有某种方法在运行期为 `virtual` 函数决定适当的参数缺省值
- 合适的做法是考虑 `virtual` 函数的替代设计，其中之一便是 `NVI` 手法，令 `base class` 内的一个 `public non-virtual` 函数调用 `private virtual` 函数，后者可被 `derived class` 重新定义

### 38. Model "has-a" or "is-implemented-in-terms-of" through composition

- 复合（`composition`）是类型之间的一种关系，当某种类型的对象内含它种类型的对象，便是这种关系
- 在应用域（`application domain`），即程序中的对象相当于你所塑造的世界中的某些事物中，复合意味着 `has-a`
- 在实现域（`implementation domain`），即对象纯粹是实现细节上的人工制品，例如缓冲区、互斥器等，复合意味着 `is-implemented-in-terms-of`

### 39. Use private inheritance judiciously

- `private` 继承规则
  - `private` 继承时，编译器不会自动将一个 `derived class` 对象转换为 `base class` 对象
  - `private` 继承时，`base class` 中的所有成员，在 `derived class` 中都会变成 `private` 属性
- `private` 继承意味着 `is-implemented-in-terms-of`（根据某物实现出），其用意是为了采用 `base class` 内已经备妥的某些特性，而不是对象之间存在任何观念上的关系，`private` 继承纯粹只是一种实现技术
- `private` 继承虽然意味着 `is-implemented-in-terms-of`，但它的优先级要低于复合（`composition`），你需要明智而审慎的使用 `private` 继承，但是当 `derived class` 需要访问 `protected base class` 的成员，或需要重新定义继承而来的 `virtual` 函数时，这么设计是合理的
- 和复合不同的是，`private` 继承可以实现 `empty base` 最优化，这对致力于对象尺寸最小化的程序库开发者而言，可能很重要

### 40. Use multiple inheritance judiciously

- 多重继承（`multiple inheritance`）是指一个 `derived class` 可以继承自多个 `base class`，但是相应的，`base class` 中相同的名称可能会产生歧义性，要解决这个问题你必须明白的指出要调用哪一个 `base class` 内的函数
- 多重继承的 `base classes` 如果在继承体系中又有着共同且更高级的 `base class`，则会产生更致命的菱形继承问题
  - 此时你需要面对这样一个问题，如果顶层 `base class` 中存在一个成员变量 `A`，那么你是否打算让 `base class` 内的成员变量经由每一条路径被复制？如果是，那么最底层的 `derived class` 内将会有两份 `A` 成员变量，但简单的逻辑告诉我们，`derived class` 中不应该有两份 `A` 成员变量
- C++在这场多重继承的辩论中并没有倾斜立场，两个方案其都支持
  - 缺省情况下的做法是执行复制，也就是会产生两份成员变量
  - 如果那不是你想要的，则必须令那个带有此数据的 `base class` 成为 `virtual base class`，你必须令所有直接继承自它的 `classes` 采用 `virtual` 继承
- 从正确行为的观点看，`public` 继承应该总是 `virtual` 继承的，但是不要盲目使用 `virtual` 继承，因为你需要为 `virtual` 继承付出代价
  - 使用 `virtual` 继承的 `class` 所产生的对象往往比使用 `non-virtual` 继承的体积大
  - 访问 `virtual base class` 的成员变量时，也比访问 `non-virtual` 成员时速度慢
  - 支配 `virtual base class` 初始化的规则远为复杂且不直观，`virtual base` 的初始化责任是由继承体系中最底层的 `class` 负责
    - 因此 `class` 若派生自 `virtual bases` 而需要初始化，必须认知其 `virtual bases`，不论那些 `bases` 距离多远
    - 当一个新的 `derived class` 加入继承体系时，它必须承担其 `virtual bases`（不论直接或间接）的初始化责任
- 因此对 `virtual base class` 的使用忠告很简单
  - 第一，非必要不使用 `virtual base class`，必须确定，你的确是在明智而审慎的情况下使用它
  - 第二，如果必须使用，尽可能避免在其中放置数据，如果 `virtual base class` 不带任何数据，将是最具实用价值的情况


# C++内存屏障（内存顺序）总结

原子操作（atomic）是无锁编程(Lock-Free Programming)的基础。以往，要使用atomic操作，我们一般会使用[gcc内置的原子操作接口](https://gcc.gnu.org/onlinedocs/gcc-4.9.2/gcc/_005f_005fatomic-Builtins.html)，或者是基于指定平台硬件指令封装的[atomic库](https://github.com/ivmai/libatomic_ops)。c\++11直接引入了[atomic库](http://en.cppreference.com/w/cpp/atomic)，为c\++定义了原子类型操作接口以及内存模型，极大的方便了我们的使用。我尝试通过本文对C++11中内存屏障（内存顺序）的一些基本概念和使用情况进行总结。

## C++内存模型

C\++内存模型可以被看作是C\++程序和计算机系统（包括编译器，多核CPU等可能对程序进行乱序优化的软硬件）之间的契约，它规定了多个线程访问同一个内存地址时的语义，以及某个线程对内存地址的更新何时能被其它线程看见。这个模型约定：没有数据竞争(data race)的程序是遵循顺序一致性的。该模型的核心思想就是由程序员用同步原语（例如，锁或者C\++11中新引入的atomic类型的共享变量）来保证你程序是没有数据竞争的，这样CPU和编译器就会保证程序是按程序员所想的那样执行的（即顺序一致性）。换句话说，程序员只需要恰当地使用具有同步语义的指令来标记那些真正需要同步的变量和操作，就相当于告诉CPU和编译器不要对这些标记好的同步操作和变量做违反顺序一致性的优化，而其它未被标记的地方可以做原有的优化。编译器和CPU的大部分优化手段都可以继续实施，只是在同步原语处需要对优化做出相应的限制；而且程序员只需要保证正确地使用同步原语即可，因为它们最终表现出来的执行效果与顺序一致性模型一致。由此，C\++多线程内存模型帮助我们在易编程性和性能之间取得了一个平衡。

在C\++11标准之前，C\++是建立在单线程语义上的。为了进行多线程编程，C\++程序员通过使用诸如Pthreads，Windows Thread等C\++语言标准之外的线程库来完成代码设计。以Pthreads为例，它提供了类似pthread_mutex_lock这样的函数来保证对共享变量的互斥访问，以防止数据竞跑。人们不禁会问，Pthreads这样的线程库我用的好好的，干嘛需要C\++引入的多线程，这不是多此一举么？其实，以线程库的形式进行多线程编程在绝大多数应用场景下都是没有问题的。然而，线程库的解决方案也有其先天缺陷。第一，如果没有在编程语言中定义内存模型的话，我们就不能清楚的定义到底什么样的编译器/CPU优化是合法的，而程序员也不能确定程序到底会怎么样被优化执行。例如，Pthreads标准中并未对什么是数据竞争做出精确定义，因此，[C\++编译器可能会进行一些错误优化从而导致数据竞争](https://dl.acm.org/citation.cfm?id=1065042)。第二，绝大多数情况下线程库能正确的完成任务，而在极少数对性能有更高要求的情况下（尤其是需要利用底层的硬件特性来实现高性能Lock Free算法时）需要更精确的内存模型以规定好程序的行为。简而言之，把内存模型集成到编程语言中去是比线程库更好的选择。

## C++11中的内存屏障（内存顺序）

### "松散"内存屏障

std::memory_order_relaxed，松散操作，**没有同步或顺序制约**，仅对此操作要求原子性。带标签 `memory_order_relaxed`的原子操作无同步操作；它们不会在并发的内存访问间强加顺序。它们只保证原子性和修改顺序一致性。

例如，对于最初为零的`x`和`y`:

```cpp
// 线程 1 ：
r1 = y.load(memory_order_relaxed); // A
x.store(r1, memory_order_relaxed); // B

// 线程 2 ：
r2 = x.load(memory_order_relaxed); // C 
y.store(42, memory_order_relaxed); // D
```

允许产生结果`r1 == 42 && r2 == 42`，因为即使线程1中A先序于B且线程2中C先序于D ，却没有制约避免y的修改顺序中D先出现于A ，而x的修改顺序中B先出现于C。D在y上的副效应，可能可见于线程1中的加载A ，同时B在x上的副效应，可能可见于线程2中的加载C。

![01_relax_mode](images/01_relax_mode.png)

如上图所示，假设：a, b, c分别为普通变量，而x为atomic类型的变量，当在写入x时，设置memory_order_relaxed时，写入a，写入b的顺序，在另外的线程上看到的，完全可能是相互调换的，写入c的位置，完全也有可能由出现在写入x之前，而在另外一个线程上看到的，确实在写入x之后，同时，读出b的动作，完全有可能从写入x之后，编程在另外一个线程上看，是在写入x之前。也就是，各种乱序， 都是被允许的。

松散内存顺序的典型使用是计数器自增，只要求原子性，但不要求顺序或同步

### 单向的"释放"内存屏障

std::memory_order_release，释放操作，**当前线程中的读或写不能被重排到此存储后**。当前线程的所有写入，可见于<font color="#0000FF">加载</font>**该同一原子变量**的其他线程。

![02_release_mode_ok](images/02_release_mode_ok.png)

如上图所示，在使用`memory_order_release`设置的原子操作写入的情况下，原子操作之后的读写操作，在另外的线程（加载了该原子变量的线程）看来，可以重排到原子操作之前（通俗点说，就是另外线程可能认为当前线程是先执行的写入的a操作，再执行的写入x操作）。但是，如下图所示，原子操作之前的读、写操作，计算机系统必须保证，在另外一个线程看来，他是在原子操作写入之前就被写入了， 不能是在原子操作之后才写入(通俗点说，也就是另外一个线程，不能认为当前线程先写入的x，再写入的c，他一定要看到的是先写入c，再写入的x)：

![03_release_mode_not_ok](images/03_release_mode_not_ok.png)

### 单向的"加载"内存屏障

std::memory_order_acquire，加载操作，**当前线程中读或写不能被重排到此加载前**。其他<font color="#0000FF">释放</font>**同一原子变量**的线程的所有写入，为当前线程所可见。

![04_acquire_mode_ok](images/04_acquire_mode_ok.png)

如上图所示，在设置`memory_order_acquire`的对x的读操作前的读、写操作，在另外的线程看来（或者说实际的运行顺序），可以被重排到对x的读操作后，(通俗点说，就是其他线程可以是认为当前线程先读取的x，再写入的c)。然而如下图所示，对x的读操作后的读、写操作，在另外的线程看来不允许被重排到x的读操作前（不允许其他线程看到当前线程先写入的a，再读取的x）。

![05_acquire_mode_not_ok](images/05_acquire_mode_not_ok.png)

## 单向“加载”+单向“释放”协议

往往`memory_order_acquire`和`memory_order_release`是配合着一起使用的：

1. 线程1使用`memory_order_release`写入**原子变量x**
2. 线程2使用`memory_order_acquire`读出**原子变量x**

所有在线程1上，在写入x之前的写入操作，都将在线程2上，在读出x之后，被看到。使用单向“加载”+单向“释放”协议的场景往往是：

1. 线程1，写入一些实际数据，接着通过将原子变量x设置为某个值`A`（通过使用`memory_order_release`写入原子变量x）来“发布”这些数据。
2. 线程2，通过读取并判断x已被设置为`A`（通过使用`memory_order_acquire`来读取原子变量x），进而读取线程1实际“发布”的那些数据

![06_release_acquire_protocol](images/06_release_acquire_protocol.png)

如上图所示，thread_1在release写入x(值:`A`)之前，写入了待发布的a,b的数据，而thread_2，将在acquire读出x且为`A`之后，将读到thread_1发布的a,b的数据。同时，我们可以注意到，在thread_2上，在acquire读出x之前，如果对a进行读操作，我们是无法确认读到的a一定会thread_1在之前最后写入的a，这里的顺序是不会被保证的，重排是被允许的。同时，在之后，读取c，读到的是否为thread_1最后写入的c，也是不确定的，因为，在x写入之后，thread_1上又出现了一次写入，而如果在此之前，还有一次写入， 这两次写入之间，是不存在限制，可能会被重排的。

thread_1上有了release_store，对于a，b的写入就一定会在x的改变之前，在thread_2上，就不会出现类似读出c，的不确定性。thread_2上有了acquire_load，右侧的读出a，就不会被重排读到左侧，而左侧读出a的不确定性，也不存在。thread_1卡住的是：对于数据a，b的写入不能排到x的写入之后，thread_2卡住的，是对于数据a，b的读取，不能排到读取x之前，这样，就保证了数据a，b，与"信号量"x，之间，在thread_1, thread_2上的同步关系。

### 双向的"加载-释放"内存屏障

std::memory_order_acq_rel，加载-释放操作，带此内存顺序的读-修改-写操作既是获得加载又是释放操作。没有操作能够从此操作之后被重排到此操作之前，也没有操作能够从此操作之前被重排到此操作之后，当然，具有这一限制的前提是，观察读写顺序的不同线程是使用的**同一个原子变量**并基于这一内存顺序。

### 最严的"顺序一致"内存屏障

std::memory_order_seq_cst，顺序一致操作，此内存顺序的操作既是加载操作又是释放操作，没有操作能够从此操作之后被重排到此操作之前，也没有操作能够从此操作之前被重排到此操作之后。带标签`memory_order_seq_cst`的原子操作不仅以与释放/加载顺序相同的方式排序内存（在一个线程中先发生于存储的任何结果都变成做加载的线程中的可见），还对**所有拥有此标签**的内存操作建立一个单独全序。`memory_order_seq_cst`比`memory_order_acq_rel`更强，`memory_order_acq_rel`的顺序保障，是要基于**同一个原子变量**的，也就是说，在这个原子变量之前的读写，不能重排到这个原子变量之后，同时这个原子变量之后的读写，也不能重排到这个原子变量之前。但是，如果两个线程基于`memory_order_acq_rel`使用了两个不同的原子变量x1, x2，那在x1之前的读写，重排到x2之后，是完全可能的，在x1之后的读写，重排到x2之前，也是被允许的。然而，如果两个原子变量x1,x2，是基于`memory_order_seq_cst`在操作，那么即使是x1之前的读写，也不能被重排到x2之后，x1之后的读写，也不能重排到x2之前，也就说，如果都用`memory_order_seq_cst`，那么程序代码顺序(Program Order)就将会是你在多个线程上都实际观察到的顺序(Observed Order)

## 参考

- [C++内存屏障（内存顺序）总结](https://lday.me/2017/12/02/0018_cpp_atomic_summary/)

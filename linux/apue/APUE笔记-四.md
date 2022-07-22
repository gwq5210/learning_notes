- [第十一章 线程](#第十一章-线程)
  - [线程概念](#线程概念)
  - [线程标识](#线程标识)
  - [线程创建](#线程创建)
  - [线程终止](#线程终止)
  - [互斥量](#互斥量)
    - [避免死锁](#避免死锁)
    - [函数pthread_mutex_timedlock](#函数pthread_mutex_timedlock)
  - [读写锁](#读写锁)
    - [带有超时的读写锁](#带有超时的读写锁)
  - [条件变量](#条件变量)

# 第十一章 线程

## 线程概念

典型的UNIX进程可以看成只有一个控制进程：一个进程在某一时刻只能做一件事情。有了多个控制线程以后，在程序设计时就可以把进程设计成在某一时刻能够做不止一件事，每个线程处理各自独立的任务。其好处如下

- 通过为每种事件类型分配单独的处理线程，可以简化处理异步时间的代码。每个线程会采用同步编程模式，其比异步编程模式简单得多
- 多个进程必须使用操作系统提供的复杂机制才能实现内存和文件描述符的共享，而多个线程自动的可以访问相同的存储地址和文件描述符
- 有些问题可以分解而提高整个程序吞吐量。当然只有在两个任务的处理过程互不依赖的情况下，两个任务才可以较差运行
- 交互程序同样可以使用多线程来改善响应时间，多线程可以把程序中处理用户输入输出的部分与其他部分分开

有些人把多线程的程序设计与多处理器或多核系统联系起来。但是即使程序运行在单处理器上也能得到多线程编程模型的好处。其并不影响程序结构。程序都可以通过使用线程得以简化。

每个线程都包含有表示执行环境所必须的信息，其中包括进程中标识线程的线程ID、一组寄存器值、栈、调度优先级和策略、信号屏蔽字、errno变量以及线程私有数据。一个进程的所有信息对该进程的所有线程都是共享的，包括可执行程序的代码、程序的全局内存和堆内存、栈以及文件描述符

## 线程标识

每个线程有一个线程ID。进程ID在整个系统中是唯一的，但线程ID不同，线程ID只有在它所属的进程上下文中才有意义

与pid_t是一个非负整数不同。线程ID是用pthread_t数据类型表示的，实现的时候可以用一个结构来代表，所以可移植的实现不能把它作为整数处理。因此必须使用一个函数来对两个线程ID进行比较

```cpp
#include <pthread.h>

int pthread_equal(pthread_t tid1, pthread_t tid2);

若相等，返回非0数值；否则，返回0
```

无法用可移植的方法打印pthread_t的值，但线程ID通常在调试过程中需要打印

线程可以通过调用pthread_self函数获得自身的线程ID

```cpp
#include <pthread.h>

pthread_t pthread_self(void);

返回调用线程的线程ID
```

## 线程创建

在传统的UNIX进程模型中，每个进程只有一个控制线程。从概念上讲，这与基于线程模型中每个进程只包含一个线程是相同的。在pthread的情况下，程序开始运行时，它也是以单进程中的单个控制线程启动的。在创建多个控制线程以前，程序的行为与传统的进程并没有什么区别。新增的线程可以通过调用pthread_create函数创建

```cpp
#include <pthread.h>

int pthread_create(pthread_t* restrict tidp, const pthread_attr_t* restrict attr, void* (*start_rtn)(void*), void* restrict arg);

若成功，返回0；否则返回错误编号
```

attr参数用于定制各种不同的线程属性。为NULL时创建一个具有默认属性的线程。新创建的线程从start_rtn函数的地址开始运行，参数为arg

线程创建时并不能保证哪个线程会先运行：是新创建的线程，还是调用线程。新创建的线程可以访问进程的地址空间，并继承调用线程浮点环境和信号屏蔽字，但是该线程的挂起信号集会被清除

注意pthread函数在调用失败时，通常会返回错误码，并不设置errno。每个线程提供errno的副本，这只是为了与使用errno的现有函数兼容。在线程中，从函数中返回错误码更清晰整洁，不需要依赖那些随着函数执行不断变化的全局状态，这样可以把错误范围限制在出错的函数中

pthread_create虽然会返回新线程ID，但是新建的线程并不能安全的使用它，如果新线程在主线程调用pthread_create返回之前就运行了，那么新线程看到的是未初始化的tidp内容，这个内容并不是正确的线程ID

## 线程终止

如果进程中的任意线程调用了exit、_Exit或_exit，那么整个进程就会终止。与此相似，如果默认的动作是终止进程，那么发送到线程的信号就会终止整个进程

单个线程有3中方式退出，因此可以在不终止整个进程的情况下，停止它的控制流

- 线程可以简单的从启动例程中返回，返回值是线程的退出码
- 线程可以被同一进程中的其他线程取消
- 线程调用pthread_exit

```cpp
#include <pthread.h>

void pthread_exit(void* rval_ptr);
```

进程中的线程可以通过调用pthread_join函数访问到退出指针

```cpp
#include <pthread.h>

int pthread_join(pthread_t thread, void** rval_ptr);

若成功，返回0；否则，返回错误编码
```

调用线程将一直阻塞，直到指定的线程退出。如果线程简单的从它的启动例程中返回，rval_ptr就包含了返回码。如果线程被取消，由rval_ptr指定的内存单元就设置为PTHREAD_CANCELED

可以通过调用pthread_detach自动把线程置于分离状态，这样资源就可以恢复。如果线程已处理分离状态，pthread_join调用就会失败，返回EINVAL，尽管这种行为是与具体实现相关的

如果对线程的返回值不感兴趣，可以将rval_ptr设置为NULL。在这种情况下，调用pthread_join的函数可以等待指定的线程终止，但并不获取线程的终止状态

线程可以通过调用pthread_cancel函数来取消同一进程中的其他线程

```cpp
#include <pthread.h>

int pthread_cancel(pthread_t tid);

若成功，返回0；若出错，返回错误编号
```

在默认情况下，pthread_cancel函数会使得由tid标识的线程的行为表现为如同调用了参数为PTHREAD_CANCELED的pthread_exit函数，但是，线程可以选择忽略取消或者控制如何被取消。注意pthread_cancel并不等待线程终止，它仅仅提出请求

线程可以安排它退出时需要调用的函数，这与进程在退出时可以用atexit函数安排退出是类似的。这样的函数称为线程清理处理程序（thread cleanup handler）。一个线程可以建立多个清理处理程序。处理程序记录再栈中，也就是说，它们的执行顺序与他们注册时相反

```cpp
#include <pthread.h>

void pthread_cleanup_push(void (*rtn)(void*), void* arg);
void pthread_cleanup_pop(int execute);
```

pthread_cleanup_push函数注册线程清理处理程序，当线程执行以下动作时，清理函数rtn被执行，参数为arg

- 调用pthread_exit时
- 响应取消请求时
- 用非零execute参数调用pthread_cleanup_pop时

如果execute参数设置为0，清理函数将不被调用。不管发生上述哪种情况，pthread_cleanup_pop都将删除上次pthread_cleanup_push调用建立的清理处理程序

这些函数有一些限制，由于它们可以实现为宏，所以必须在与线程相同的作用域中以匹配对的形式使用。pthread_cleanup_push的宏定义可以包含{，在这种情况下，在pthread_cleanup_pop的定义中要有对应的匹配字符

在Single UNIX Specification中，如果函数在调用pthread_cleanup_push和pthread_cleanup_pop之间返回，会产生未定义行为。唯一的可移植方法是调用pthread_exit

线程和进程函数之间有相似之处，如下

![进程和线程原语比较](https://gwq5210.com/images/进程和线程原语比较.png)

在默认情况下，线程的终止状态会保存直到对该线程调用pthread_join。如果线程已经被分离，线程的底层存储资源可以在线程终止时立即被回收。在线程分离后，我们不能用pthread_join函数等待它的终止状态，因为对分离状态的线程调用pthread_join会产生未定义行为。可以调用pthread_detach分离线程

```cpp
#include <pthread.h>

int pthread_detach(pthread_t tid);

若成功，返回0；若出错，返回错误编号
```

我们将学习通过修改传给pthread_create函数的线程属性，创建一个已处于分离状态的线程

## 互斥量

可以使用pthread的互斥接口来保护数据，确保同一时间只有一个线程访问数据。互斥量（mutex）从本质上是一把锁，在访问共享资源前对互斥量进行加锁，在访问完成后解锁互斥量。对互斥量进行加锁以后，任何其他视图再次对互斥量加锁的线程都会被阻塞知道当前线程释放该互斥锁。如果释放互斥量时有一个以上的线程阻塞，那么所有该锁上的阻塞线程都会变成可运行状态，第一个变成运行的线程就可以对互斥量加锁，其他线程就会看到互斥量依然是锁着的，只能回去再次等待它重新变为可用。在这种方式下，每次只有一个线程可以向前执行。

只有将所有线程都设计成遵守相同的数据访问规则的，互斥机制才能正常工作。操作系统并不会为我们做的数据访问串行化。如果允许其中的某个线程在没有得到锁的情况下也可以访问共享资源，那么即使其他线程在使用共享资源前都申请锁，也还是会出现数据不一致的问题

互斥变量是用pthread_mutex_t数据类型表示的。在使用互斥变量以前，必须首先对它进行初始化，可以把它设置为常量PTHREAD_MUTEX_INITIALIZER（只适用于静态分配的互斥量），也可以通过调用pthread_mutex_init函数进行初始化。如果动态分配互斥量（例如通过调用malloc函数），在释放内存前需要调用pthread_mutex_destroy

```cpp
#include <pthread.h>

int pthread_mutex_init(pthread_mutex_t* restrict mutex, const pthread_mutexattr_t* restrict attr);
int pthread_mutex_destroy(pthread_mutex_t* mutex);

若成功，返回0；若出错，返回错误编号
```

要用默认的属性初始化互斥量，只需要把attr设置为NULL。

对互斥量进行加锁，需要调用pthread_mutex_lock。如果互斥量已经上锁，调用线程将阻塞直到互斥量被解锁。对互斥量解锁，需要调用pthread_mutex_unlock

```cpp
#include <pthread.h>

int pthread_mutex_lock(pthread_mutex_t* mutex);
int pthread_mutex_trylock(pthread_mutex_t* mutex);
int pthread_mutex_unlock(pthread_mutex_t* mutex);

若成功，返回0；若出错，返回错误编号
```

如果线程不希望被阻塞，它可以使用pthread_mutex_trylock尝试对互斥量进行加锁。如果调用pthread_mutex_trylock时互斥量处于为锁住状态，那么pthread_mutex_trylock将锁住互斥量，不会出现阻塞直接返回0，否则pthread_mutex_trylock就会失败，不能锁住互斥量，返回EBUSY

### 避免死锁

如果线程视图对同一个互斥量加锁两次，那么自身就会陷入死锁状态，但是使用互斥量时，还有其他不太明显的方式也能产生死锁。

可以通过仔细控制互斥量加锁的顺序来避免死锁的发生。即不同的线程总是以相同的顺序加锁互斥量

但有时候，应用程序的结构使得对互斥量进行排序是很困难的。如果涉及了太多的锁和数据结构，可用的函数并不能把它转换成简单的层次，那么就需要采用另外的方法。在这种情况下，可以先释放占用的锁，然后过一段时间再试。这种情况可以使用pthread_mutex_trylock接口避免死锁。如果已经占有某些锁而且pthread_mutex_trylock接口返回成功，那么就可以前进。但是如果不能获取锁，可以先释放已经占用的锁，做好清理工作，然后过一段时间再重新尝试

如果锁的粒度太粗，就会出现很多线程阻塞等待相同的锁，这可能并不能改善并发性。如果锁的粒度太细，那么过多的锁开销就会使系统性能收到影响，而且代码变得复杂。作为一个程序员，需要在满足锁需求的情况下，在代码复杂性和性能之间找到正确的平衡

### 函数pthread_mutex_timedlock

当线程视图获取一个已加锁的互斥量时，pthread_mutex_timedlock互斥量原语允许绑定线程阻塞时间。pthread_mutex_timedlock与pthread_mutex_lock是基本等价的，但是在到达超时时间值时，pthread_mutex_timedlock不会对互斥量进行加锁，而是返回错误码ETIMEDOUT

```cpp
#include <pthread.h>

int pthread_mutex_timedlock(pthread_mutex_t* restrict mutex, const struct timespec* restrict timespec);

若成功，返回0；若出错，返回错误编号
```

超时指定愿意等待的绝对时间（与相对时间比较而言，指定在时间X之间可以阻塞等待，而不是说愿意阻塞Y秒）。这个超时时间是用timespec结构来表示的，它用秒和纳秒来描述时间

注意，阻塞的时间可能会有所不同，造成不同的原因有很多种：开始时间可能在某秒的中间位置，系统时钟的精度可能不足以精确支持我们指定的超时时间值，或者在程序继续运行前，调度延迟可能会增加时间值

## 读写锁

读写锁（reader-writer-lock）与互斥量类似，不过读写锁允许更高的并行性。互斥量要么是锁住状态，要么就是不加锁状态，而且一次只有一个线程可以对其加锁。读写锁可以有3种状态：读模式下加锁状态，写模式下加锁状态，不加锁状态。一次只有一个线程可以占有写模式的读写锁，但是多个线程可以同时占有读模式的读写锁

在读写锁是写加锁状态时，在这个锁被解锁之前，所有尝试读对这个锁加锁的线程都会被阻塞。当读写锁在读加锁状态时，所有尝试以读模式对它进行加锁的线程都可以得到访问权，但是任何希望以写模式对此锁进行加锁的线程都会阻塞，知道所有的线程释放它们的读锁为止。

虽然各操作系统对读写锁的实现各不相同，但当读写锁处于读模式锁住的状态，而这时有一个线程视图以写模式获取锁时，读写锁通常会阻塞随后的读模式锁请求。这样可以避免读模式锁长期占用，而等待的写模式锁请求一直得不到满足

读写锁非常适用于对数据结构读的次数远大于写的情况。当读写锁在写模式下时，它所保护的数据结构就可以被安全的修改，因为一次只有一个线程可以在写模式下拥有这个锁。当读写锁在读模式下时，只要线程先获取了读模式下的读写锁，读锁所保护的数据结构就可以被多个获得读模式锁的线程读取

读写锁也叫做共享互斥锁（shared-execlusive lock）。当读写锁是以读模式锁住时，就可以说成是以共享模式锁住的。当它是写模式锁住的时候，就可以说成是互斥模式锁住的。

像互斥量一样，读写锁在使用之前必须初始化，在释放它们底层的内存之前必须销毁

```cpp
#include <pthread.h>

int pthread_rwlock_init(pthread_rwlock_t* restrict rwlock, const pthread_rwlockattr_t* restrict attr);
int pthread_rwlock_destroy(pthread_rwlock_t* rwlock);

若成功，返回0；若出错，返回错误编号
```

读写锁通过调用pthread_rwlock_init进行初始化。如果希望读写锁有默认属性，可以传一个NULL指针给attr

可以使用PTHREAD_RWLOCK_INITIALIZER对静态分配的读写锁进行初始化

在释放读写锁占用的内存之前，需要调用pthread_rwlock_destroy做清理工作。如果pthread_rwlock_init为读写锁分配了资源，pthread_rwlock_destroy将释放这些资源。如果在调用pthread_rwlock_destroy之前就释放了读写锁占用的内存空间，那么分配给这个锁的资源就会丢失

要在读模式下锁定读写锁，需要调用pthread_rwlock_rdlock。要在写模式下锁定读写锁，需要调用pthread_rwlock_wrlock。不过以何种方式锁住读写锁，都可以调用pthread_rwlock_unlock进行解锁

```cpp
#include <pthread.h>

int pthread_rwlock_rdlock(pthread_rwlock_t* rwlock);
int pthread_rwlock_wrlock(pthread_rwlock_t* rwlock);
int pthread_rwlock_unlock(pthread_rwlock_t* rwlock);

若成功，返回0；若出错，返回错误编号
```

各种实现可能会对共享模式下可获取的读写锁的次数进行限制，所以需要检查pthread_rwlock_rdlock的返回值。尽管pthread_rwlock_wrlock和pthread_rwlock_unlock有错误返回，而且从技术上来讲，在调用函数时应该总是检查错误返回，但是如果锁设计合理的话，就不需要检查它们。错误返回值的定义只是针对不正确使用读写锁的情况（如未经初始化的锁），或试图获取已拥有的锁而可能产生死锁的情况。但是需要注意，有些特定的实现可能会定义另外的错误返回

Single UNIX Specification还定义了读写锁原语的条件版本

```cpp
#include <pthread.h>

int pthread_rwlock_tryrdlock(pthread_rwlock_t* rwlock);
int pthread_rwlock_trywrlock(pthread_rwlock_t* rwlock);

若成功，返回0；若出错，返回错误编号
```

可以获取锁时，两个函数返回0，否则，它们返回EBUSY。这两个函数可以用于我们前面讨论的遵守某种锁层次但还不能完全避免死锁的情况

### 带有超时的读写锁

```cpp
#include <pthread.h>
#include <time.h>

int pthread_rwlock_timedrdlock(pthread_rwlock_t* restrict rwlock, const struct timespec* restrict tsptr);
int pthread_rwlock_timedwrlock(pthread_rwlock_t* restrict rwlock, const struct timespec* restrict tsptr);

若成功，返回0；若出错，返回错误编号
```

其行为与它们的不计时版本类似。如果不能获取锁，超时时间到达时，这两个函数将返回ETIMEDOUT错误。超时指定的是绝对时间，而不是相对时间

## 条件变量


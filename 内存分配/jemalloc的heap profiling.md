# jemalloc的heap profiling

使用 `jemalloc` 时，可以通过 `profiling` 机制来发现并定位内存泄漏(`memory leak`)。本文翻译自[原文](https://github.com/jemalloc/jemalloc/wiki/Use-Case%3A-Heap-Profiling)并增加了一些例子。

## 安装

这里我们编译安装 `jemalloc`，注意在 `configure` 的时候添加了 `--enable-prof` 选项，这样才能打开 `profiling` 机制。下文中通过 `MALLOC_CONF` 设置的参数都依赖于次选项。

```shell
wget https://github.com/jemalloc/jemalloc/archive/5.1.0.tar.gz
tar zxvf 5.1.0.tar.gz
cd jemalloc-5.1.0/
./autogen.sh
./configure --prefix=/usr/local/jemalloc-5.1.0 --enable-prof
make
make install
```

## 程序退出时的内存分配状态

作为最简单的情形，我们可以在程序退出时，查看还有哪些分配但未释放的内存，它们通常是内存泄漏的重要线索。

```cpp
#include <stdio.h>
#include <stdlib.h>

void do_something(size_t i)
{
  // Leak some memory.
  malloc(i * 1024);
}

void do_something_else(size_t i)
{
  // Leak some memory.
  malloc(i * 4096);
}

int main(int argc, char **argv)
{
  size_t i, sz;

  for (i = 0; i < 80; i++)
  {
    do_something(i);
  }

  for (i = 0; i < 40; i++)
  {
    do_something_else(i);
  }

  return (0);
}
```

然后编译。注意：我们的代码里没有 `include jemalloc` 的头文件，编译的时候也不需要链接 `jemalloc` 库。启动的时候通过 `LD_PRELOAD` 指定 `jemalloc` 库的路径就可以了。这是 `jemalloc` 方便使用的地方。当然也可以 `include jemalloc` 的头文件并链接 `jemalloc` 库来使用 `jemalloc` 的其他功能(见后文)。

```shell
gcc test.c -o a.out
```

### 程序退出时的泄漏

```cpp
# MALLOC_CONF=prof_leak:true,lg_prof_sample:0,prof_final:true LD_PRELOAD=/usr/local/jemalloc-5.1.0/lib/libjemalloc.so.2  ./a.out
<jemalloc>: Leak approximation summary: ~6926352 bytes, ~120 objects, >= 2 contexts
<jemalloc>: Run jeprof on "jeprof.34447.0.f.heap" for leak detail
```

程序退出时报告了泄漏的大概情况，多少自己，多少对象，并产生了一个”jeprof.34447.0.f.heap”文件，其中包含了详细信息。

### 泄漏的详细信息

使用 `jemalloc` 提供的 `jeprof` 工具，可以方便的查看”jeprof.34447.0.f.heap”文件：

```shell
# /usr/local/jemalloc-5.1.0/bin/jeprof a.out jeprof.34447.0.f.heap
Using local file a.out.
Using local file jeprof.34447.0.f.heap.
Welcome to jeprof!  For help, type 'help'.
(jeprof) top
Total: 6.6 MB
     3.3  50.6%  50.6%      3.3  50.6% do_something
     3.3  49.4% 100.0%      3.3  49.4% do_something_else
     0.0   0.0% 100.0%      6.6 100.0% __libc_start_main
     0.0   0.0% 100.0%      6.6 100.0% _start
     0.0   0.0% 100.0%      6.6 100.0% main
(jeprof)
```

### 泄露代码的调用路径

`jeprof` 工具也可以生成泄漏代码的调用路径图。

```shell
/usr/local/jemalloc-5.1.0/bin/jeprof  --show_bytes --pdf a.out jeprof.34447.0.f.heap > a.pdf
```

## Heap Profiling

有时候，我们不能终止程序来看程序退出时的状态，`jemalloc` 提供了一些方法来获取程序运行时的内存分配情况。

### 每1MB dump一次

```shell
# export MALLOC_CONF="prof:true,lg_prof_interval:20"
# LD_PRELOAD=/usr/local/jemalloc-5.1.0/lib/libjemalloc.so.2  ./a.out
# ll
total 40
-rwxr-xr-x. 1 root root 8520 Jan  2 18:33 a.out
-rw-r--r--. 1 root root 3878 Jan  2 18:38 jeprof.34584.0.i0.heap
-rw-r--r--. 1 root root 3882 Jan  2 18:38 jeprof.34584.1.i1.heap
-rw-r--r--. 1 root root 3882 Jan  2 18:38 jeprof.34584.2.i2.heap
-rw-r--r--. 1 root root 4004 Jan  2 18:38 jeprof.34584.3.i3.heap
-rw-r--r--. 1 root root 4004 Jan  2 18:38 jeprof.34584.4.i4.heap
-rw-r--r--. 1 root root 4006 Jan  2 18:38 jeprof.34584.5.i5.heap
```

其中 `lg_prof_interval:20` 中的 `20` 表示 `1MB(2^20)`，`prof:true` 是打开 `profiling`。运行程序时，每分配(大约) `1MB` 就会 `dump` 产生一个文件。

```shell
# /usr/local/jemalloc-5.1.0/bin/jeprof a.out jeprof.34584.3.i3.heap
Using local file a.out.
Using local file jeprof.34584.3.i3.heap.
Welcome to jeprof!  For help, type 'help'.
(jeprof) top
Total: 5.8 MB
     4.8  81.8%  81.8%      4.8  81.8% do_something
     1.1  18.2% 100.0%      1.1  18.2% do_something_else
     0.0   0.0% 100.0%      5.8 100.0% __libc_start_main
     0.0   0.0% 100.0%      5.8 100.0% _start
     0.0   0.0% 100.0%      5.8 100.0% main
(jeprof) quit
```

`jeprof` 工具不仅可以查看详细信息或者生成调用路径图(如上所示)，还可以用来比较两个 `dump` (显示增量部分)：

```shell
# /usr/local/jemalloc-5.1.0/bin/jeprof a.out --base=jeprof.34584.2.i2.heap jeprof.34584.3.i3.heap
Using local file a.out.
Using local file jeprof.34584.3.i3.heap.
Welcome to jeprof!  For help, type 'help'.
(jeprof) top
Total: 1.6 MB
     1.1  66.2%  66.2%      1.1  66.2% do_something_else
     0.5  33.8% 100.0%      0.5  33.8% do_something
     0.0   0.0% 100.0%      1.6 100.0% __libc_start_main
     0.0   0.0% 100.0%      1.6 100.0% _start
     0.0   0.0% 100.0%      1.6 100.0% main
(jeprof)
```

其中 `--base` 指定比较的基础。如上例，`dump jeprof.34584.3.i3.heap` 的时候，分配了 `5.8 MB` 内存，`do_something` 和 `do_something_else` 分别占 `81.8%` 和 `18.2%`；但和 `dump jeprof.34584.2.i2.heap` 的时候相比，多分配了 `1.6MB` 内存，`do_something` 和 `do_something_else` 分别占 `66.2%` 和 `33.8%`。可以预见，自己和自己比，没有内存被分配：

```shell
# /usr/local/jemalloc-5.1.0/bin/jeprof a.out --base=jeprof.34584.2.i2.heap jeprof.34584.2.i2.heap
Using local file a.out.
Using local file jeprof.34584.2.i2.heap.
Welcome to jeprof!  For help, type 'help'.
(jeprof) top
Total: 0.0 MB
(jeprof)
```

### 每次达到新高时dump

```shell
# export MALLOC_CONF="prof:true,prof_gdump:true"
# LD_PRELOAD=/usr/local/jemalloc-5.1.0/lib/libjemalloc.so.2  ./a.out
```

### 在代码里手动dump

注意：需要 `include jemalloc` 的头文件并链接 `jemalloc` 库。

```cpp
#include <stdio.h>
#include <stdlib.h>
#include <jemalloc/jemalloc.h>

void do_something(size_t i)
{
  // Leak some memory.
  malloc(i * 1024);
}

void do_something_else(size_t i)
{
  // Leak some memory.
  malloc(i * 4096);
}

int main(int argc, char **argv)
{
  size_t i, sz;

  for (i = 0; i < 80; i++)
  {
    do_something(i);
  }

  mallctl("prof.dump", NULL, NULL, NULL, 0);

  for (i = 0; i < 40; i++)
  {
    do_something_else(i);
  }

  mallctl("prof.dump", NULL, NULL, NULL, 0);

  return (0);
}
```

编译(指定 `jemalloc` 头文件路径，并链接 `jemalloc` 库)：

```shell
# gcc -I/usr/local/jemalloc-5.1.0/include test.c -L/usr/local/jemalloc-5.1.0/lib -ljemalloc
```

然后设置 `MALLOC_CONF` 并执行程序：

```shell
# export MALLOC_CONF="prof:true,prof_prefix:jeprof.out"
# LD_PRELOAD=/usr/local/jemalloc-5.1.0/lib/libjemalloc.so.2  ./a.out
# ls
a.out  jeprof.out.35307.0.m0.heap  jeprof.out.35307.1.m1.heap
```

## 稳定状态的内存分配

注意：需要 `include jemalloc` 的头文件并链接 `jemalloc` 库。

程序启动的时候，势必要分配内存，我们查找内存泄漏的时候，往往更关注程序在稳定状态时的内存分配：只要程序启动完成之后内存不再增长，就没有严重的泄漏问题。所以，稳定状态的内存 `profiling` 往往更有意义。设置 `MALLOC_CONF=prof_active:false`，使得程序在启动的时候 `profiling` 是 `disabled`；程序启动完成后，再通过 `mallctl(“prof.active”)` 来 `enable profiling`；或者定时 `enable`。

### 启动完成后enable profiling

```cpp
#include <stdio.h>
#include <stdlib.h>
#include <jemalloc/jemalloc.h>

void do_something(size_t i)
{
  // Leak some memory.
  malloc(i * 1024);
}

void do_something_else(size_t i)
{
  // Leak some memory.
  malloc(i * 4096);
}

int main(int argc, char **argv)
{
  size_t i, sz;

  //initialization ...

  for (i = 0; i < 80; i++)
  {
    do_something(i);
  }

  //enter into steady-state...

  bool active = true;
  mallctl("prof.active", NULL, NULL, &active, sizeof(bool));

  for (i = 0; i < 40; i++)
  {
    do_something_else(i);
  }

  mallctl("prof.dump", NULL, NULL, NULL, 0);

  return (0);
}
```

编译，设置环境变量，并执行：

```shell
# gcc -I/usr/local/jemalloc-5.1.0/include test2.c -L/usr/local/jemalloc-5.1.0/lib -ljemalloc
# export MALLOC_CONF="prof:true,prof_active:false,prof_prefix:jeprof.out"
# LD_PRELOAD=/usr/local/jemalloc-5.1.0/lib/libjemalloc.so.2  ./a.out
# ls
a.out  jeprof.out.36842.0.m0.heap 
```

用 `jeprof` 查看，发现只有 `steady-state` 之后的内存分配：

```shell
# /usr/local/jemalloc-5.1.0/bin/jeprof a.out jeprof.out.36842.0.m0.heap
Using local file a.out.
Using local file jeprof.out.36842.0.m0.heap.
Welcome to jeprof!  For help, type 'help'.
(jeprof) top
Total: 2.8 MB
     2.8 100.0% 100.0%      2.8 100.0% do_something_else
     0.0   0.0% 100.0%      2.8 100.0% __libc_start_main
     0.0   0.0% 100.0%      2.8 100.0% _start
     0.0   0.0% 100.0%      2.8 100.0% main
(jeprof)
```

### 定时enable profiling

还可以通过这样的流程定时 `dump`：

```cpp
bool active;

mallctl("prof.dump", NULL, NULL, NULL, 0);    //生成prof.1

active = true;
mallctl("prof.active", NULL, NULL, &active, sizeof(bool));

//sleep 30 seconds

active = false;
mallctl("prof.active", NULL, NULL, &active, sizeof(bool));

//sleep 30 seconds

mallctl("prof.dump", NULL, NULL, NULL, 0);   //生成prof.2
```

然后通过 `jeprof a.out --base=prof.1 prof.2` 来比较这两个 `dump`，这可以突显出稳定状态下程序的内存分配行为。

## 参考

- [jemalloc的heap profiling](https://www.yuanguohuo.com/2019/01/02/jemalloc-heap-profiling/)

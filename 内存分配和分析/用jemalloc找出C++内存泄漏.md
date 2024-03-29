# 用jemalloc找出C++内存泄漏

最近在查内存泄漏的问题，线上跑的服务内存持续增长，由于一直没有查到原因，所以都是通过定时重启来释放内存的。最近请求数量上来了，内存泄漏问题加剧，所以又开始重点查内存的问题。

之前是用valgrind来查内存泄漏的问题，valgrind类似虚拟机的技术，检测内存泄漏时程序会在valgrind虚拟出来的内存上面运行，valgrind挺强悍的，就是速度太慢的，用valgrind后程序运行效率下降好几倍。用valgrind在测试环境没跑出啥“definitely”的明确内存泄漏，都是一些“一次性”的泄漏。所以猜测是一些“still reachable”的内存越来越多导致的，“still reachable”指的是能被引用的内存，内存泄漏是内存无法被引用到，但是能被引用的内存不一定是还在使用的内存，比如不断向一个链表里面写数据而没有删除动作，那么这个链表就会一直增大，虽然可能只有最新的10个数据有在用，但是没有把旧的数据释放，这个虽然不是严格的内存泄漏，但也会造成了内存不断增大。由于服务有用内存池，而且一次请求产生的“still reachable”内存很小，可能只有几十个字节，所以需要大量的请求才能比较明显观察到哪个函数有泄漏的情况。前面说到，用valgrind会使程序变慢，处理请求的效率很低，而且测试环境可能会与线上不一致，所以很难通过valgrind来观察到这种细微的内存泄漏，比较好的办法是用一个对程序效率影响不大的内存检测工具到线上去观测。

google了一番，有些malloc库自带内存检测功能，比较常用的有两个tcmalloc与jemalloc。我这次用的是jemalloc，要使用jemalloc的内存检测功能，需要在编译jemalloc的时候打开--enable-prof选项。jemalloc的用法有两种，一种是在程序编译的时候将jemalloc一起编译进去，另一种是使用LD_PRELOAD，LD_PRELOAD指定jemlloc后，jemalloc中的函数会覆盖掉程序中的同名函数，比如malloc、free等。 编译好jemalloc后，通过环境变量MALLOC_CONF配置jemalloc运行时的参数。

```shell
MALLOC_CONF=prof:true,lg_prof_interval:32 LD_PRELOAD=/usr/local/lib/libjemalloc.so.2 ./a.out
```

其中prof:true表示打开堆检测，lg_prof_interval:32表示dump的频率，以2为底的指数，32表示2的32次方，即发生变化的内存到达4G时dump一次。 程序运行后，每隔一段时间会产生一个heap文件，heap文件产生速度与内存申请的频率有关，里面记录的当前堆内存的情况，还有调用栈信息，这些信息可以使用jeprof工具查看:

```shell
jeprof a.out heap文件
```

可以生成pdf文件查看调用栈信息

```shell
jeprof --pdf a.out heap文件 > a.pdf
```

全部的调用栈会比较多，可以对比两个heap文件只显示出那些内存增长的调用栈

```shell
jeprof --pdf a.out --base=1.heap 2.heap > 1_2.pdf
```

还可以通过加上--lines显示行号，--show_bytes显示字节数 让服务跑一段时间，产生多个heap文件后，比较时间间隔比较久的两个heap文件，重点看看那些内存涨得比较多的调用栈。如果程序自己设计了内存池来管理内存的话可能会看到比较奇怪的调用栈信息，所以建议关闭内存池进行检测。这次内存问题排查花的时间比较久，之前还怀疑过内存碎片的问题，但通过jemalloc看确实有越来越多的内存没有释放掉，所以肯定还有一些内存泄漏，经过反复分析代码，终于找出了“真凶”，修复上线后，内存比较平稳，所以可以排除内存碎片的影响，或者内存碎片其实没有那么大的影响。

## 参考

- [用jemalloc找出C++内存泄漏](https://tyrese-yang.github.io/c++/2020/08/05/jemalloc/)

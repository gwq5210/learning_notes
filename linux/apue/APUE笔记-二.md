- [第五章 标准IO库](#第五章-标准io库)
  - [流和FILE对象](#流和file对象)
  - [缓冲](#缓冲)
  - [打开流](#打开流)
  - [读和写流](#读和写流)

# 第五章 标准IO库

标准IO库是ISO C的标准，不仅仅UNIX系统提供了，很多其他操作系统也都实现了标准IO库

## 流和FILE对象

在第三章所有的文件IO都是围绕文件描述符的。对于标准IO库，其操作是围绕流（stream）进行的，打开或创建一个文件时，使一个流与一个文件相关联

标准IO文件流可用于单字节和多字节字符集。流的定向（stream's orientation）决定了读、写字符是单字节还是多字节的。

当一个流最初被创建时，它并没有定向。若在流上使用一个单字节IO函数，则将流设置为字节定向的。若在流上使用一个多字节IO函数，则将流设置为字宽定向的。

只有freopen和fwide这两个函数可以改变流的定向。

```cpp
#include <stdio.h>

#include <wchar.h>

int fwide(FILE* fp, int mode);

返回值: >0 : 宽定向；<0 字节定向；0 : 未定向
```

fwide并不能改变已定向流的定向。fwide无法返回出错。需要在调用fwide前清除errno，返回时再检查errno的值

一个流的结构（FILE*，通常称为文件指针）通常包含一些必要的信息，如实际IO的文件描述符，缓存区指针和长度，当前在缓冲区中的字符数和出错标志等

一个进程预定义了3个流，标准输入流，标准输出流，标准出错流(分别是stdin, stdout, stderr)可以自动被进程使用。分别对应文件描述符STDIN_FILENO, STDOUT_FILENO, STDERR_FILENO

## 缓冲

标准IO库提供缓冲的目的是尽可能减少read、write系统调用的次数。它对每个IO流自动进行缓冲管理，避免应用程序考虑应使用多大的缓冲区。

标准IO提供3中类型的缓冲

- 全缓冲。这种情况下，缓冲区满才进行实际的IO操作，磁盘文件通常是全缓冲的。当然我们可以通过fflush手动冲洗流的缓冲区
- 行缓冲。这种情况下，输入和输出遇到换行符执行IO操作。流涉及一个终端时通常使用行缓冲。行缓冲有以下两个限制
  - 缓冲区大小固定。缓冲区满时，即使没有换行符也进行IO操作
  - 任何时候，只要通过标准IO库要求从a）不带缓冲的流或b)一个行缓冲的流得到输入数据，那么就会冲洗所有行缓冲输出流
- 不带缓冲。标准IO库不对字符进行缓冲存储。标准错误流通常是不带缓冲的，这使得出错信息可以尽快的显示出来

ISO C要求

- 当且仅当标准输入和标准输出并不指向交互式设备时，它们才是全缓冲的
- 标准错误绝不会是全缓冲的

一般系统默认如下方案

- 标准错误流是不带缓冲的
- 若是指向终端的流，则是行缓冲的；否则是全缓冲的

我们可以通过如下函数修改系统默认的缓冲类型

```cpp
#include <stdio.h>

void setbuf(FILE* restrict fp, char* restrict buf);
int setvbuf(FILE* restrict fp, char* restrict buf, int mode, size_t size);

若成功，返回0；若出错，返回非0
```

以上函数应在流被打开后调用，且应在对流执行任何一个其他操作之前调用

可以使用setbuf打开或关闭缓冲机制。buf为NULL，则关闭缓冲；为了带缓冲进行IO，参数buf必须指向一个长度为BUFSIZ的缓冲区。一般在此之后流就是全缓冲的，但是如果一个流与一个终端设备相关，某些系统也可将其设置为行缓冲的

使用setvbuf可以通过mode精确的指定缓冲类型

- _IOFBF：全缓冲
- _IOLBF：行缓冲
  - 以上可以通过buf和size设置缓冲区和长度；如果buf为NULL，则标准IO库将自动分配合适的缓冲区，适当长度一般由BUFSIZ指定（GNU C使用stat结构中的st_blksize来决定最佳缓冲区长度）
- _IONBF：不带缓冲，忽略buf和size参数

![setbuf和setvbuf函数](https://gwq5210.com/images/setbuf和setvbuf函数.png)

一般而言我们应该由系统选择缓冲区的长度，并自动分配缓冲区，流关闭时，将自动释放缓冲区

任何时候我们可以强制冲洗一个流

```cpp
#include <stdio.h>

int fflush(FILE* fp);

若成功，返回0；若出错，返回EOF
```

此函数使所有未写的数据都传送至内核。如果fp是NULL，则导致所有的输出流被冲洗

## 打开流

以下3个函数打开一个标准流

```cpp
#include <stdio.h>

FILE* fopen(const char* restrict pathname, const char* restrict type);
FILE* freopen(const char* restrict pathname, const char* restrict type, FILE* restrict fp);
FILE* fdopen(int fd, const char* restrict type);

若成功，返回文件指针；若出错，返回NULL
```

说明如下

- fopen打开路径名为pathname的指定文件
- freopen在一个指定流上打开一个指定文件，如若流已经被打开，则先关闭该流。若流已经定向，则使用freopen清除该定向。此函数一般用于将一个指定文件打开为一个预定义的流：标准输入、标准输出、标准错误
- fdopen函数取一个已有的文件描述符（如从open、dup、dup2、fcntl、pipe、socket、socketpair或accept函数得到），并使一个标准的IO流与此文件描述符相结合

参数type有如下组合

![fopen的type](https://gwq5210.com/images/fopen的type.png)

使用字符b可以使得标准IO系统区分二进制和文本文件。UNIX内核并不区分这两种文件，所以在UNIX系统下并无作用

对于fdopen，type参数的作用稍有区别。因为该描述符已被打开，所有fdopen为写打开并不截断文件。标准IO追加写方式也不能用于创建该文件（该文件一定存在，fd引用一个文件）

当以读和写类型（type中+号）打开一个文件时，有如下限制

- 如果中间没有fflush、fseek、fsetpos或rewind，则在输出后边不能直接跟随输入
- 如果中间没有fseek、fsetpos或rewind或者一个输入操作没有到达文件尾端，则在输入操作之后不能直接跟随输出

![打开流的不同方式](https://gwq5210.com/images/打开流的不同方式.png)

在w和a类型创建一个文件时，我们无法指定文件的访问权限位，我们可以通过调整umask值来限制这些权限或创建之后修改权限

调用fclose可以关闭一个打开的流

```cpp
#include <stdio.h>

int fclose(FILE* fp);

若成功，返回0；若出错，返回EOF
```

在该文件被关闭之前，冲洗缓冲区中的输出数据，缓冲区中的任何输入数据被丢弃。如果分配和缓冲区，则自动释放缓冲区

进程正常终止时（直接调用exit或从main函数返回），则所有带未写缓冲数据的标准IO流都被冲洗，所有打开的标准IO流都被关闭

## 读和写流


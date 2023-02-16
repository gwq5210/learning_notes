# bcc使用

## 安装

## centos8安装

```shell
yum install bcc bcc-devel bcc-tools python3-bcc kernel-devel
```

安装完成以后，bcc工具在以下目录

```shell
rpm -ql bcc-tools
# /usr/share/bcc/tools/memleak
```

可以将`/usr/share/bcc/tools/`加入`PATH`中

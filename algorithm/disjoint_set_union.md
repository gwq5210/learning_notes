# 并查集

## 引入

并查集是一种用于管理元素所属集合的数据结构，实现为一个森林，其中每棵树表示一个集合，树中的节点表示对应集合中的元素。

顾名思义，并查集支持两种操作：

- 合并（Union）：合并两个元素所属集合（合并对应的树）
- 查询（Find）：查询某个元素所属集合（查询对应的树的根节点），这可以用于判断两个元素是否属于同一集合

并查集在经过修改后可以支持单个元素的删除、移动；使用动态开点线段树还可以实现可持久化并查集。

但并查集无法以较低复杂度实现集合的分离。

## 初始化

初始时，每个元素都位于一个单独的集合，表示为一棵只有根节点的树。方便起见，我们将根节点的父亲设为自己。

```cpp
class DisjointSetUnion {
 public:
  DisjointSetUnion(int n) : parents_(n) {
    std::iota(parents_.begin(), parents_.end(), 0);
  }

 private:
  std::vector<int> parents_;
};
```

## 查询

![disjoint-set-union-find](images/disjoint-set-union-find.svg)

我们需要沿着树向上移动，直至找到根节点。

```cpp
int Find(int x) {
  return parents_[x] == x ? x : Find(parents_[x]);
}
```

## 路径压缩

查询过程中经过的每个元素都属于该集合，我们可以将其直接连到根节点以加快后续查询。

![disjoint-set-compress](images/disjoint-set-compress.svg)

```cpp
int Find(int x) {
  return parents_[x] == x ? x : parents_[x] = Find(parents_[x]);
}
```

## 合并

要合并两棵树，我们只需要将一棵树的根节点连到另一棵树的根节点。

![disjoint-set-merge](images/disjoint-set-merge.svg)

```cpp
void Union(int x, int y) {
  parents_[Find(y)] = Find(x);
}
```

## 启发式合并

合并时，选择哪棵树的根节点作为新树的根节点会影响未来操作的复杂度。我们可以将节点较少或深度较小的树连到另一棵，以免发生退化。

在算法竞赛的实际代码中，即便不使用启发式合并，代码也往往能够在规定时间内完成任务。

## 完整代码

```cpp
class DisjointSetUnion {
 public:
  DisjointSetUnion(int n) : parents_(n) {
    std::iota(parents_.begin(), parents_.end(), 0);
  }

  int Find(int x) {
    return parents_[x] == x ? x : parents_[x] = Find(parents_[x]);
  }

  void Union(int x, int y) {
    parents_[Find(y)] = Find(x);
  }

 private:
  std::vector<int> parents_;
};
```

## 题目

[721. 账户合并](https://leetcode.cn/problems/accounts-merge/)

## 参考资料

- [并查集](https://oi-wiki.org/ds/dsu/)

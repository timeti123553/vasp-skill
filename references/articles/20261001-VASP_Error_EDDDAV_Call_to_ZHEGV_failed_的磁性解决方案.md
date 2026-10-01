# （VASP）Error EDDDAV: Call to ZHEGV failed.的磁性解决方案

- 来源: `https://zhuanlan.zhihu.com/p/351808487`（**与 `og:url` 核对一致**；页面内 `saved from url=(0038)…` 亦吻合）
- 作者: 知乎专栏文章（`p/351808487`），编辑于 2022-04-14
- 类型: html（用户另存网页后收录）
- 标签: 知乎, 他人文章, 报错, 磁性, ZHEGV, AMIX, 混合参数
- 正文字数: 7132

---
在VASP计算中可能会遇到：

- Error EDDDAV: Call to ZHEGV failed. Returncode = 7 1 8

相关的讨论可见：

[求助：EDDDAV: Call to ZHEGV failed. Returncode = 出现这种错误，该如何解决bbs.keinsci.com/thread-12444-1-5.html](http://bbs.keinsci.com/thread-12444-1-5.html)

在本文，讲从磁性的角度来解决这个问题。

我的计算报错如下：

其中average eigenvalue（使用命令：grep "average eigenvalue" OUTCAR）：

初步判断是由于磁性的导致的计算错误；

具体的解决方法就调节线性混合的AMIX系数，相关讨论可以参考一下文章：

http://www.yidianzixun.com/article/0MI8uSPQ

我转载部分内容：

AMIX：线性混合参数。在 IMIX = 4 时：

1) AMIX 参数的设置非常依赖于体系：对于金属体系，AMIX 通常相当小（AMIX = 0.02）。而对于半导体体系，从我目前的测试结果来看，使用 AMIX = 0.2 大部分情况下可以使得电子迭代快速收敛；

2) 对于某些磁性金属体系，使用过大的 AMIX 值（比如 AMIX = 0.3）时，虽然也会使得电子迭代快速收敛，但此时体系其实是收敛到更高的磁态上，当使用 AMIX = 0.02 进行迭代时，将获得能量更低的状态。具体例子见下面磁性金属 MIXING 测试结果；

3) 对于磁性材料，特别是结构较复杂、电子迭代不容易收敛的体系，建议扫描 AMIX 值。

4）在 PBE 计算时，OUTCAR 文件中会给出 “average eigenvalue” 的信息，见下面图片。对于“线性混合”，手册认为当该值为 1 时，对应的电荷密度混合最好，电子迭代最好。据此手册给出了一个获得最佳 AMIX 的方法：使用要给 AMIX 值进行迭代计算，然后搜索 OUTCAR 中“average eigenvalue”的数值 Γ，优化的 AMIX 为：AMIXopt = AMIXcurrent * Γ，然后用新的 AMIXopt 值做电子迭代，直至 Γ = 1。

5）相比于手册推荐的方法，我个人更推荐直接扫描 AMIX 值(比如从 0.02 扫到 0.2，间隔取 0.02)。对此磁性金属体系，使用手册的方法优化 AMIX，有时会给出相当糟糕的结果。见下文的测试例子。

本计算使用的AMIX是0.2，其他线性混合参数如下：

AMIX = 0.2 BMIX = 0.0001 AMIX_MAG = 0.8 BMIX_MAG = 0.0001

可见，

将AMIX是改成0.02后，线性混合参数如下：

AMIX = 0.02 BMIX = 0.0001 AMIX_MAG = 0.8 BMIX_MAG = 0.0001

最终的计算结果如图：

计算完成，其中average eigenvalue：

计算电子步数稍大，可以进一步调节AMIX的数值，由上图可知，可以调大AMIX的值，以达到快速收敛。新的AMIX=0.02*1.5=0.03（AMIXopt = AMIXcurrent * Γ；这里我的Γ取的比较小，为1.5）

AMIX = 0.03 BMIX = 0.0001 AMIX_MAG = 0.8 BMIX_MAG = 0.0001

电子步下降至63步收敛。

总结：

- 可以通过AMIX来调控磁性，解决“Error EDDDAV: Call to ZHEGV failed. Returncode = 7 1 8”的错误。

- 通过AMIXopt = AMIXcurrent * Γ，进一步改善收敛关系。

======================更新===========================

除了对磁性体系外，在非磁系统中遇到也可能遇到类似问题。以下是一个关闭SPIN的系统。系统报错：

在这个系统中，SYMPREC可能是导致报错的原因。

将SYMPREC去掉，计算可以继续进行


---

> ✂️ 已裁掉知乎页面 UI 与评论区。
> **提炼去向**：整篇并入 `errors.md` **§2.6（LAPACK：`ZPOTRF`/`ZHEGV` 失败）**，作为「**磁性解法**」子条目——包括**用 `grep` 查 `average eigenvalue` 做诊断**、**`AMIX` 扫描 vs `AMIX_opt = AMIX_current × Γ` 两种做法**、⚠️ **「`AMIX` 过大→收敛到更高磁态」这个静默陷阱**、可用的磁性混合参数组合，以及**非磁体系的 `SYMPREC` 成因**。`references/incar.md` 的混合参数行也补了指路。
> 本库注：原文第 4 点里 `average eigenvalue` 的中文解释提到「手册认为该值为 1 时混合最好」，本条与 VASP 手册的 `AMIX` 条目一致；文中**没给 Γ 的具体数值图**（是截图），**真正要用的 Γ 请自己 `grep` 出来**。

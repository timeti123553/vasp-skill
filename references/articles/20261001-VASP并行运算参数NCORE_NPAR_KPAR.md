# VASP并行运算参数NCORE,NPAR,KPAR

- 来源: `https://zhuanlan.zhihu.com/p/666602300`（与原始 HTML 的 `og:url` 核对一致）
- 作者: 知乎 @好好学习（liu-mei-56-86），发布于 2023-11-13
- 类型: html（用户另存网页后收录；zhida 搜索链接已在收录时压平）
- 标签: 知乎, 他人文章, 并行, NCORE, NPAR, KPAR
- ⚠️ 抓取说明：原文用三张**速度对比图**展示不同参数组合的差异（无参数 / `NPAR=6` / `NPAR=6+KPAR=2`），图未进入本文件；结论（合理设置 `KPAR`+`NPAR` 对速度影响显著）已收录。
- 正文字数: 4751

---
VASP为并行运算，合理设置并行运算参数可以极大提高计算速度，从而提高工作效率。

KPAR:同时计算多少K点数 体系的K点数可用grep irre OUTCAR查看，最大可设置为体系的不可约K点数

NPAR:每个K点同时计算多少条能带，NPAR一般取NBANDS的开根号附近,grep NBANDS OUTCAR 查看BANDS数，保证NPAR能被NBANDS整除。

NCORE:每条能带由多少个核计算，NCORE乘以NPAR等于总核数，所以设置NPAR的同时还需要保证NCORE为整数。

NPAR与NCORE设置其一即可，因为有NCORE乘以NPAR等于总核数，所以一个确定了，另一个就确定了。

对于中大体系，K点数相对较少，设置NPAR的同时，还需要测试KPAR，以提高计算速度。

不设置并行运算参数：

NPAR=6

NPAR=6 KPAR=2

可见，合理设置KPAR，NPAR对计算速度的提高尤为关键！


---

> ✂️ 已裁掉知乎页面自带的 UI（1 条评论 / 广告位 / 作者卡片）。
> 正文整理进 `references/performance.md` §四：**三层并行**（`KPAR` 分 k 点 / `NPAR` 分能带 / `NCORE` 分一条能带内的核）、**两个查询命令**（`grep irre OUTCAR`、`grep NBANDS OUTCAR`）、**约束**（`NPAR` 整除 `NBANDS`、`KPAR ≤` 不可约 k 点数、`NCORE × NPAR = 总核数`），以及**三条并存的经验规则**（并说明它们会冲突、以实测为准）。

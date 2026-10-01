# VASP输出文件OUTCAR OSZICAR

- 来源: `https://zhuanlan.zhihu.com/p/391279503`（**与原始 HTML 的 `og:url` 核对一致**；转载自公众号《VASP学习交流》）
- 作者: 知乎 @VASP学习交流（公众号运营者），编辑于 2021-07-27
- 类型: html（用户另存网页后收录；zhida 搜索链接已在收录时压平）
- 标签: 知乎, 他人文章, OUTCAR, OSZICAR, grep, 磁矩
- 正文字数: 7059

---
本文转载于微信公众号 VASP学习交流

OUTCAR

OUTCAR一开始告诉VASP的版本信息，在多少个核上运行, 以及服务器的相关情况VASP都会输出一个大大的WARNING，不用care，但是还需要辨别WARNING给出的信息

紧接着WARNING下面是POTCAR、INCAR、POSCAR、KPOINTS的基本信息

POTCAR该含有的全部在OUTCAR里都含有，包括POTCAR里面有各个元素的信息，包括价电子

grep POTCAR OUTCAR

grep TIT OUTCAR #查看有哪些元素

grep ENMAX OUTCAR

grep ZVAL OUTCAR #查看价电子数目

POSCAR的内容：坐标格式，原子位置，以及晶胞的形状大小，体系的对称性以及点群操作相关的信息，在这里我们的体系为C_1的点群

KPOINTS, K点基本信息，如果想查看K点个数，可以使用命令grep irreducible OUTCAR 或者 grep irre OUTCAR

INCAR基本信息

这里给的就是第一个离子步（Iteration 后面的数字）内，且还是第一个电子步（括号里的数字）的迭代。每一个电子步和离子步完成后，输出结果会在OSZICAR中同步更新

迭代结束，输出主要的结果：费米能级以及能级信息,所以可以通过grep E-fermi OUTCAR查看fermi能级能量

每一个离子步优化好之后的原子坐标，以及每个原子每个方向上的受力情况

OUTCAR中与OSZICAR中E0对应（相同）的是energy(sigma->0) = 后面的那个，可以使用命令grep without OUTCAR | tail -1 加tail -1表示取最后一个离子步的能量

最后一个离子步出现 grep required accuracy表示达到收敛标准了，计算可以正常结束,所以可以使用命令grep required OUTCAR命令，如果出现reached required accuracy - stopping structural energy minimisation那么就达到收敛标准了（使用这个命令判断有没有达到收敛）

LOOP+表示这个离子步用了多长时间，故而使用命令, grep LOOP+ OUTCAR 可以给出每一个离子步花去的时间

grep LOOP OUTCAR 可以给出每一个电子步以及离子步花去的时间

如果打开ISPIN=2， LORBIT=11那么就可以在接近末尾的地方得到每个原子的磁矩贡献，比OSZICAR里的磁矩信息更准确

末尾给出本次计算所用的内存，所用的时间

所以就可以使用tail OUTCAR （OUTCAR是vasp的主要输出文件）， 这个命令用以查看文件最后面的几行，如果你的OUTCAR 和图中的一样，说明任务已经完成

总结

查看所计算体系的费米能级，使用下面的命令grep fermi OUTCAR | tail -1

查看所计算体系的倒格子基矢,grep irreducible OUTCAR 或者 grep irre OUTCAR

查看所计算体系中原子的受力情况, 在采用vi对OUTCAR编辑时，用下面的命令来查找 ?TOTAL-FORCE

查看所计算体系的体积，使用下面的命令 grep volume OUTCAR

查看所计算体系的总能，使用下面的命令,grep without OUTCAR | tail -1 ，取E0的值

查看每一个离子步花去的时间grep LOOP+ OUTCAR

查看每一个电子步以及离子步花去的时间grep LOOP OUTCAR

查看有无收敛，使用命令grep required OUTCAR

OSZICAR

OSZICAR——优化过程中自洽循环的每一步所对应的能量（包括收敛速度和当前运行时间步信息）

N-电子时间步（循环次数）

150 F : 150表示一共跑了150个离子步，而这个第150步跑了有6个电子步

E-体系总能

dE-当前步与上一步能量差

E0:与OUTCAR中energy(sigma->0) = 后面的那个能量对应，一般取这个能量

mag给出磁矩

d eps-能带结构能量的变化

ncg-Ø波函数的优化次数

rms-波函数残差（每两步波函数变化）

rms(c)-电荷密度残差（前几步电荷密度不参与迭代）

DAV：blocked Davidson iteration scheme 的缩写，一个电子自洽算法的缩写，RMM (residual minimization scheme) 和 CG （conjugate-gradientalgorithm）等，这些是由INCAR中的ALGO 参数决定。

本文转载于微信公众号 VASP学习交流

未经授权，禁止转载


---

> ✂️ 已裁掉知乎页面自带的 UI（6 条评论 / 广告位 / 公众号二维码 / 话题链接）。
> 正文的查询命令整理进 `references/onboarding.md` **§9.2**（新增 `grep TIT/ZVAL/ENMAX`、`grep LOOP+`/`LOOP`、`grep fermi | tail -1`、`tail OUTCAR` 等），`OSZICAR` 的列补充（`mag` 磁矩、`rms(c)` 的解释）补进 **§九**，并把「从 `OUTCAR` 反查元素/价电子数/截断能」挂到 `errors.md` §1.4。
> ⭐ **两处独立印证**：本篇与 kkk 系列（六）**都指出 `OSZICAR` 的 `E0` 对应 `OUTCAR` 的 `energy(sigma->0)`**；本篇还补了一个关键细节——**`grep without` 只是定位那一行**（`energy without entropy` 与 `energy(sigma->0)` 在同一行），要取的是后者。
> 新增一条实用提示：**`ISPIN=2` + `LORBIT=11` 时，`OUTCAR` 接近末尾处有每个原子的磁矩贡献，比 `OSZICAR` 的总 `mag` 更准确**。

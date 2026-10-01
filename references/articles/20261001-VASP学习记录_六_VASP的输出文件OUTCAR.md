# VASP学习记录(六)：VASP的输出文件OUTCAR

- 来源: `https://zhuanlan.zhihu.com/p/579705300`（**与原始 HTML 的 `og:url` 核对一致**；收录时曾误填为 `p/580901041`，已更正）
- 作者: 知乎 @kkk（kkk-52-50-62）——「VASP 学习记录」系列**第六篇**，编辑于 2022-11-23；示例为单个 O 原子
- 类型: html（用户另存网页后收录；zhida 搜索链接已在收录时压平）
- 标签: 知乎, 他人文章, OUTCAR, 输出文件, 对称性, 应力
- 正文字数: 16124

---
​

目录

收起

第一部分：基础信息

第二部分：Warning 与 POTCAR

第三部分：基础分析部分

第四部分：INCAR

第五部分：正式计算前的总结

第六部分：正式计算记录

第七部分：费米能级以及能带信息

第八部分：各个方向力的大小、能量信息

第九部分：结尾

快速信息获取命令

隔了好久终于想起来接着更新了。。。

这是程序运行结束之后的文件夹，可见除去输入文件之外多了许多内容。我首先来写OUTCAR。

我觉得OUTCAR是所有输出文件中最重要的，毕竟是最长的（x)，一共有1555行。OUTCAR文件中包含了一次VASP计算所得到的大部分结果，还包含对计算过程的记录（每一步的迭代结果）。官网是这样说的：

The OUTCAR file gives detailed output of a VASP run, including:

- A summary of the used input parameters.

- Information about the electronic steps, KS-eigenvalues.

- Stress tensors.

- Forces on the atoms.

- Local charges and magnetic moments.

- Dielectric properties

- The amount of output written onto the OUTCAR file can be chosen by modifying the [NWRITE](https://www.vasp.at/wiki/index.php/NWRITE) tag in the [INCAR](https://www.vasp.at/wiki/index.php/INCAR) file.

这1500多行的内容看起来很多很让人头疼，所以我们每次想找自己需要的信息还是需要一定的方法的。我们要知道vasp使用长横虚线去分割一个文件中的不同部分，所以我们可以据此慢慢解读OUTCAR中的内容。由于水平十分有限，许多内容我只是截图或者复制了过来没有详细说明，等我了解了之后再来添加。如果有错误也十分欢迎指出。

### 第一部分：基础信息

OUTCAR的第一部分很短只有8行，内容是这次计算的基础信息，包括vasp的版本信息，在多少个核上运行等等。

### 第二部分：Warning 与 POTCAR

进入第二部分，第一眼看见的就是一个大大的warning!查阅资料说除非你的本次计算失败，否则这个warning就没有什么实际价值，并且无论计算成功与否它都会出现。仔细读一下里面的内容，是对设置NCORE的建议，确实对理解本次计算意义不大。

在warning的下方的内容是把POTCAR复制了一遍，就不额外说明了。

### 第三部分：基础分析部分

第三部分一开始是相关POSCAR的内容：坐标格式，原子位置，以及晶胞的形状大小。

然后是静态的初始位置的对称性分析、动力学对称性分析以及结构、动力学和磁对称性分析：

对于氧原子来说这两块内容及其相似，就放在一起了。内容大概是说我们的体系是一个简单正交晶胞，为D_2h的点群，有8个对称操作。注意我们在设置POSCAR的时候把三个边设置了不一样的长度，打破了对称性。如果三个边长一致的话，结果就是有48个对称操作，得到一个立方系统。

Analysis of symmetry for initial positions (statically): ===================================================================== Subroutine PRICEL returns: Original cell was already a primitive cell. Routine SETGRP: Setting up the symmetry group for a simple orthorhombic supercell. Subroutine GETGRP returns: Found 8 space group operations (whereof 8 operations were pure point group operations) out of a pool of 8 trial point group operations. The static configuration has the point symmetry D_2h. Analysis of symmetry for dynamics (positions and initial velocities): ===================================================================== Subroutine PRICEL returns: Original cell was already a primitive cell. Routine SETGRP: Setting up the symmetry group for a simple orthorhombic supercell. Subroutine GETGRP returns: Found 8 space group operations (whereof 8 operations were pure point group operations) out of a pool of 8 trial point group operations. The dynamic configuration has the point symmetry D_2h. Analysis of structural, dynamic, and magnetic symmetry: ===================================================================== Subroutine PRICEL returns: Original cell was already a primitive cell. Routine SETGRP: Setting up the symmetry group for a simple orthorhombic supercell. Subroutine GETGRP returns: Found 8 space group operations (whereof 8 operations were pure point group operations) out of a pool of 8 trial point group operations. The magnetic configuration has the point symmetry D_2h. Subroutine INISYM returns: Found 8 space group operations (whereof 8 operations are pure point group operations), and found 1 'primitive' translations

最后给了所有的点群操作以及K-points：

### 第四部分：INCAR

这一段有很多行，实在是太长了我就只放一部分。

要知道我们自己写的输入文件INCAR只有四行内容，那么多出来的部分使用的都是软件提供给我们的默认值。这说明我距离真正掌握Vasp还有很长的路。

### 第五部分：正式计算前的总结

在统计完任务的基本输入后，Vasp会总结一下本次计算的文字描述，任务类型，体系大小，K点数目，计算所需的内存等信息。然后才开始进入正式的计算部分.

energy-cutoff : 400.00 volume of cell : 534.00 direct lattice vectors reciprocal lattice vectors 7.500000000 0.000000000 0.000000000 0.133333333 0.000000000 0.000000000 0.000000000 8.000000000 0.000000000 0.000000000 0.125000000 0.000000000 0.000000000 0.000000000 8.900000000 0.000000000 0.000000000 0.112359551 length of vectors 7.500000000 8.000000000 8.900000000 0.133333333 0.125000000 0.112359551 k-points in units of 2pi/SCALE and weight: K-POINTS 0.00000000 0.00000000 0.00000000 1.000 k-points in reciprocal lattice and weights: K-POINTS 0.00000000 0.00000000 0.00000000 1.000 position of ions in fractional coordinates (direct lattice) 0.00000000 0.00000000 0.00000000 position of ions in cartesian coordinates (Angst): 0.00000000 0.00000000 0.00000000 -------------------------------------------------------------------------------------------------------- k-point 1 : 0.0000 0.0000 0.0000 plane waves: 9715 maximum and minimum number of plane-waves per node : 9715 9715 maximum number of plane-waves: 9715 maximum index in each direction: IXMAX= 12 IYMAX= 13 IZMAX= 14 IXMIN= -12 IYMIN= -13 IZMIN= -14 serial 3D FFT for wavefunctions parallel 3D FFT for charge: minimum data exchange during FFTs selected (reduces bandwidth) total amount of memory used by VASP MPI-rank0 39262. kBytes ======================================================================= base : 30000. kBytes nonl-proj : 777. kBytes fftplans : 848. kBytes grid : 7319. kBytes one-center: 6. kBytes wavefun : 312. kBytes INWAV: cpu time 0.0000: real time 0.0002 Broyden mixing: mesh for mixing (old mesh) NGX = 25 NGY = 27 NGZ = 29 (NGX = 80 NGY = 80 NGZ = 96) gives a total of 19575 points initial charge density was supplied: charge density of overlapping atoms calculated number of electron 6.0000000 magnetization 1.0000000 keeping initial charge density in first step -------------------------------------------------------------------------------------------------------- Maximum index for augmentation-charges 177 (set IRDMAX) -------------------------------------------------------------------------------------------------------- First call to EWALD: gamma= 0.218 Maximum number of real-space cells 3x 3x 3 Maximum number of reciprocal cells 3x 3x 3 FEWALD: cpu time 0.0019: real time 0.0019

### 第六部分：正式计算记录

下面的内容都是对正式计算迭代内容的记录。由于体系是O原子，我们仅有一个离子步内的所有电子步的计算。每一个迭代步长都会占据一块内容，格式相同。

上图是最后一个迭代步长后的输出结果，最后一行是体系的输出能量。

### 第七部分：费米能级以及能带信息

迭代结束后要输出主要的结果：费米能级以及能带信息。

average (electrostatic) potential at core the test charge radii are 0.7215 (the norm of the test charge is 1.0000) 1 -82.7739 E-fermi : -7.3678 XC(G=0): -0.7356 alpha+bet : -0.1402 spin component 1 k-point 1 : 0.0000 0.0000 0.0000 band No. band energies occupation 1 -25.1088 1.00000 2 -10.7856 1.00000 3 -10.7834 1.00000 4 -8.6836 1.00000 5 -0.5357 0.00000 6 1.4320 0.00000 7 1.5782 0.00000 8 1.7603 0.00000 9 1.9526 0.00000 10 2.0531 0.00000 11 2.2723 0.00000 12 3.6248 0.00000 13 3.7974 0.00000 14 3.8564 0.00000 15 3.9018 0.00000 16 4.0150 0.00000 17 4.1313 0.00000 18 4.2129 0.00000 19 4.2344 0.00000 20 4.3357 0.00000 21 4.5712 0.00000 22 4.5997 0.00000 23 4.8200 0.00000 24 6.3181 0.00000 25 6.3300 0.00000 26 6.4087 0.00000 27 6.4314 0.00000 28 6.5874 0.00000 29 6.5992 0.00000 30 6.6090 0.00000 31 6.8411 0.00000 32 7.1109 0.00000 33 7.1865 0.00000 34 8.4892 0.00000 35 8.8695 0.00000 36 9.1966 0.00000 37 9.2039 0.00000 38 9.4398 0.00000 39 9.4904 0.00000 40 9.6156 0.00000 spin component 2 k-point 1 : 0.0000 0.0000 0.0000 band No. band energies occupation 1 -21.4437 1.00000 2 -7.4287 1.00000 3 -6.3230 0.00000 4 -6.3222 0.00000 5 -0.2959 0.00000 6 1.5203 0.00000 7 1.7934 0.00000 8 2.1063 0.00000 9 2.1064 0.00000 10 2.4091 0.00000 11 2.4666 0.00000 12 3.7147 0.00000 13 3.8710 0.00000 14 3.9936 0.00000 15 4.1487 0.00000 16 4.1932 0.00000 17 4.3267 0.00000 18 4.4603 0.00000 19 4.5071 0.00000 20 4.5430 0.00000 21 4.7790 0.00000 22 4.8114 0.00000 23 4.9630 0.00000 24 6.4044 0.00000 25 6.4479 0.00000 26 6.5161 0.00000 27 6.6073 0.00000 28 6.6579 0.00000 29 6.8291 0.00000 30 6.8474 0.00000 31 6.9761 0.00000 32 7.3280 0.00000 33 7.4139 0.00000 34 8.7941 0.00000 35 9.0961 0.00000 36 9.3447 0.00000 37 9.4977 0.00000 38 9.6426 0.00000 39 9.6989 0.00000 40 9.7343 0.00000

因为我们在INCAR中加入了ISPIN=2这一行，即考虑了极化，我们得到了spin component1和2.氧原子最外层有6个电子，其中四个自旋向上，两个自旋向下，分别与component1、2相对应。费米能体现在这一行：

E-fermi : -7.3678 XC(G=0): -0.7356 alpha+bet : -0.1402

### 第八部分：各个方向力的大小、能量信息

------------------------ aborting loop because EDIFF is reached ---------------------------------------- CHARGE: cpu time 0.0237: real time 0.0239 FORLOC: cpu time 0.0004: real time 0.0004 FORNL : cpu time 0.0020: real time 0.0020 STRESS: cpu time 0.0247: real time 0.0247 FORCOR: cpu time 0.0302: real time 0.0303 FORHAR: cpu time 0.0038: real time 0.0039 MIXING: cpu time 0.0021: real time 0.0021 OFIELD: cpu time 0.0000: real time 0.0000 FORCE on cell =-STRESS in cart. coord. units (eV): Direction XX YY ZZ XY YZ ZX -------------------------------------------------------------------------------------- Alpha Z 0.26021 0.26021 0.26021 Ewald -22.67281 -28.53889 -38.73942 -0.00000 0.00000 0.00000 Hartree 97.82309 92.19406 95.39098 -0.00000 -0.00000 -0.00000 E(xc) -29.06756 -29.06766 -28.91266 -0.00000 0.00000 0.00000 Local -151.08308 -139.58570 -157.18277 -0.00000 0.00000 0.00000 n-local -18.49497 -18.49296 -25.31648 0.00000 -0.00000 0.00000 augment 4.51663 4.51622 8.35879 0.00000 0.00000 -0.00000 Kinetic 117.98466 117.98929 145.15900 -0.00000 -0.00000 0.00000 Fock 0.00000 0.00000 0.00000 0.00000 0.00000 0.00000 ------------------------------------------------------------------------------------- Total -0.73383 -0.72543 -0.98234 0.00000 0.00000 0.00000 in kB -2.20172 -2.17652 -2.94734 0.00000 0.00000 0.00000 external pressure = -2.44 kB Pullay stress = 0.00 kB VOLUME and BASIS-vectors are now : ----------------------------------------------------------------------------- energy-cutoff : 400.00 volume of cell : 534.00 direct lattice vectors reciprocal lattice vectors 7.500000000 0.000000000 0.000000000 0.133333333 0.000000000 0.000000000 0.000000000 8.000000000 0.000000000 0.000000000 0.125000000 0.000000000 0.000000000 0.000000000 8.900000000 0.000000000 0.000000000 0.112359551 length of vectors 7.500000000 8.000000000 8.900000000 0.133333333 0.125000000 0.112359551 FORCES acting on ions electron-ion (+dipol) ewald-force non-local-force convergence-correction ----------------------------------------------------------------------------------------------- -.108E-14 0.261E-14 -.674E-14 -.427E-16 -.713E-17 -.173E-16 0.000E+00 0.000E+00 0.000E+00 -.243E-13 0.199E-14 -.237E-13 ----------------------------------------------------------------------------------------------- -.108E-14 0.261E-14 -.674E-14 -.427E-16 -.713E-17 -.173E-16 0.000E+00 0.000E+00 0.000E+00 -.243E-13 0.199E-14 -.237E-13 POSITION TOTAL-FORCE (eV/Angst) ----------------------------------------------------------------------------------- 0.00000 0.00000 0.00000 0.000000 0.000000 0.000000 ----------------------------------------------------------------------------------- total drift: -0.000000 0.000000 -0.000000 -------------------------------------------------------------------------------------------------------- FREE ENERGIE OF THE ION-ELECTRON SYSTEM (eV) --------------------------------------------------- free energy TOTEN = -1.89219424 eV energy without entropy= -1.89219424 energy(sigma->0) = -1.89219424

我们所用的能量一般就是最后这个-1.89219424.

### 第九部分：结尾

结尾部分是实际计算的内存和时间等信息，一般来说没什么用。

### 快速信息获取命令

在实际计算中，我们肯定不想打开上千行的文档在里面闷头找我们需要的关键信息，下面写几个常用信息的快速获取命令：

获取能量信息：

grep without OUTCAR | tail -n 1 grep ' without' OUTCAR | tail -n 1 grep sigma OUTCAR | tail -n 1

获取费米能级：

grep E-fermi OUTCAR

获取k点个数：

grep irreducible OUTCAR

获取体系体积：

grep volume OUTCAR

出现了三个值是因为用到的单位不同。

参考：

1.VASP官网[Vienna Ab initio Simulation Package](https://www.vasp.at/)

2.[https://www.bigbrosci.com/categorie](https://www.bigbrosci.com/categories/LVASPTHW/page/2/)

3.VASP软件包入门指南--侯柱锋


---

> ✂️ 已裁掉知乎页面自带的 UI（评论 / 广告位 / 作者卡片 / 推荐阅读）。
> 正文整理进 `references/onboarding.md` **§9.1（`OUTCAR` 九个部分的导航）** 与 **§9.2（常用一行命令）**，并与库内多处挂钩：`§8.14`（FFT 网格 `NGX/NGY/NGZ`）、`§8.19`（开头那段 `NCORE` warning 可以忽略）、`workflows.md` §二十（能带/HOMO-LUMO 提取）。
> 💡 本篇有两条特别实用的观察已收录：① **`OUTCAR` 第 4 部分会把 INCAR 连同 VASP 补全的默认值一起回显**（想知道参数「实际取了多少」直接去那里看）；② **第 8 部分末尾那个数才是「我们要的能量」**。
> ⚠️ 原文的「快速信息获取命令」在抓取时被压成一行（多条命令粘连），整理版逐条拆开并补全了引号与管道。

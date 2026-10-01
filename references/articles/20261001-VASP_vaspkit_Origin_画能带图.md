# VASP vaspkit Origin 画能带图

- 来源: `https://zhuanlan.zhihu.com/p/564983969`
- 类型: html
- 来源: `https://zhuanlan.zhihu.com/p/564983969`（经知乎开放平台 CLI `me content --content-url` 读取，**本人文章**；`Data.Url` 与链接一致）
- 类型: html（zhihu-cli JSON → HTML 后收录；公式已内联）
- 标签: 知乎, 本人文章, 能带, Origin, VASPKIT, MnPS₃
- ⚠️ 抓取说明：两段 INCAR 在导出时**连空格一起丢了**，本库已按 VASP 语法重新排版；文末附「本库注」。
- 正文字数: 6782

---
如果计算步骤是：结构优化 \(\Rightarrow\) 静态自洽计算 \(\Rightarrow\) 能带计算；这么计算的结构会精确。

在本篇文章中，计算步骤是：结构优化 \(\Rightarrow\) 能带计算；这么计算是可以的，但是精确度不如上面。

结构优化过程中生成的 CHGCAR 和 WAVECAR 文件是对应于最后一步迭代的电荷密度和波函数，而不是对应于结构优化后的体系。结构优化后的体系可能与最后一步迭代的体系有微小的差别，导致电荷密度和波函数不完全一致。所以使用结构优化过程中生成的 CHGCAR 和 WAVECAR 文件进行计算的精确度比使用静态自洽计算生成的 CHGCAR 和 WAVECAR 文件进行计算的精确度有点差。

## 0 计算材料

本次能带计算我们选择的是 \( \rm MnPS_{3}\) 的二维纳米结构 。是一个铁磁半导体。由于 \(\rm Mn\) 的磁矩为 4.8 \(\rm \mu_{B}\) 左右，所以我们初始值设为 5 \(\rm \mu_{B}\) 。

## 1 结构弛豫

### 1.1 INCAR

Global Parameters
ISTART = 0             (The data in the WAVECAR file is not used)
ISPIN  = 2             (Spin polarised DFT)
MAGMOM = 2*5 2*0 6*0
NPAR   = 6
SYMPREC= 1E-4
LORBIT = 11
LREAL  = .FALSE.       (Projection operators: automatic)
ENCUT  = 400           (Cut-off energy for plane wave basis set, in eV)
LCHARG = .TRUE.        (Write CHGCAR or not)

Electronic Relaxation
ISMEAR = 0             (Gaussian smearing, metals:1)
SIGMA  = 0.05          (Smearing value in eV, metals:0.2)
NELM   = 90            (Max electronic SCF steps)
NELMIN = 6             (Min electronic SCF steps)
EDIFF  = 1E-05         (SCF energy convergence, in eV)

Ionic Relaxation
NSW    = 100           (Max ionic steps)
IBRION = 2             (Algorithm: 0-MD, 1-Quasi-New, 2-CG)
ISIF   = 3             (Stress/relaxation: 2-Ions, 3-Shape/Ions/V, 4-Shape/Ions)
EDIFFG = -2E-02        (Ionic convergence, eV/AA)

INCAR 文件可以自己写，也可以用 vaspkit 生成（生成的 INCAR 一般需要改改）。

### 1.2 POSCAR

- 在网站 [materialsproject](https://materialsproject.org/) 上找到自己想要的结构，也可以从其他网站上找。并下载相应的 .cif 文件。

- 使用 Materials Studio 进行相关的建模，并生成相应的 .cif 文件。

- 使用 VESTA 打开上一步的 .cif 文件，然后生成 .vasp 文件。

- 将相应的 .vasp 文件复制到做弛豫计算的目录中，并把文件复制成 POSCAR 。

注：网站 [materialsproject](https://materialsproject.org/) 也可以直接导出 POSCAR 格式的文件。之后将相应的文件拖入计算目录下，然后再把文件名改为 POSCAR 就可以了。

### 1.3 KPOINTS

通过 vaspkit 生成 KPOINTS 文件。

具体过程：vaspkit \(\rightarrow\) 1 \(\rightarrow\) 102 \(\rightarrow\) 2 \(\rightarrow\) 0.04。

注：在这一步中，vaspkit 会自动生成 POTCAR 。所以就不需要另外生成 POTCAR 了。

注：在选 K 点设置的方法中，vaspkit 有两种：Monkhorst-Pack Scheme 和 Gamma Scheme。当设定各维度的 K 点数为奇数时，两种方法的撒点是一样的，且都包含 K 空间的 Gamma 点；为偶数时，MP 撒点不包含Gamma 点，Gamma 撒点在 MP 撒点的基础上进行平移，保证采到 Gamma 点（根据自己的需要选取相应的撒点方式）。

通过上面准备的四个文件再加上我们的作业提交脚本，我们就可以提交作业进行计算了。

注：在进行弛豫计算的时候，我们一般要保证弛豫是在一个离子步内算完。因为在弛豫过程中，晶格的大小和基组可能会改变，一个离子步算完更精确。

在第一次弛豫的时候，我们往往难以一个离子步收敛，所以我们需要将 CONTCAR 复制成 POSCAR 再次进行弛豫，直到一个离子步内收敛。

在一个离子步收敛的时候，OSZICAR 会显示：

### 参数介绍

### ISTART = 0 | 1 | 2 | 3

默认值为 0

0：不使用 WAVECAR 文件中的数据。轨道的初始化由 INIWAV 所决定。

1：读取 WAVECAR 文件，并且平面波集会改变。计算时，会读取 INCAR 中设置的 ENCUT 数值和之前计算生成的 WAVECAR 中的 Orbitals。根据新的元胞（ POSCAR ）和新的平面波截断能（ INCAR 中）产生新的平面波基组。

2：读取 WAVECAR 文件，但是平面波集不变，并使其他参数发生改变（计算体积-能量相关曲线的时候用到）。

3：在重启分子动力学计算的时候使用，同时需要 WAVECAR 、CHGCAR（用于储存电荷密度信息）文件。

### ISPIN = 1 | 2

1：进行了非自旋极化计算。

2：进行了自旋极化计算。

### MAGMOM= [real array]

[real array]=原子1的原子数*对应原子的磁矩 原子2的原子数*对应原子的磁矩 ······

我们可以通过这个参数设置原子磁矩的初始值。好的初始值可以加快计算速度。对于一些简单的体系，我们可以直接设置 ISPIN=2，MAGMOM 可以不必进行设置。当设置 MAGMOM 值的时候，不一定必须是1，也可以是某些模糊或者精确的值。更多的时候，我们可以写一个和真实磁矩差不多的值。

### NPAR = [integer]

建议 NPAR \(\displaystyle\approx\sqrt{核数}\) 或者 NPAR \(\approx 每个节点的核数\) ，这样会加快计算速度。

### SYMPREC = [real]

改变体系的对称精度。默认值为 \(10^{-5}\) 。

### LORBIT=0 | 1 | 2 | 5 | 10 | 11 | 12

结合 RWIGS 标签确定是否输出 PROCAR 或 PROOUT 文件，当设置大于等于 10 时不需要设置 RWIGS 标签，一般设置成 11，会输出投影到各个原子各个轨道的分波态密度。

### LREAL = .FALSE. | Auto (or A) | On (or O) | .TRUE.

.FALSE. :在倒空间中完成投影。

.TRUE. :在实空间完成投影。采用的是一种最简单将高频组分与投影算符分开的方法。

On (or O)：采用优化过的实空间算符进行投影。

Auto (or A)：采用更好的优化。一般实空间原子数在 20 个以上才考虑（较老的 VAS P版本是 20，新的 VASP 版本是 30）。

### ENCUT = [real]

平面波的截断能。不需要明确 INCAR 中的 ENCUT 值，在 POTCAR 中有最大和最小的截断能。在两个或以上的物质进行计算时，会使用最大的截断能。出于一致性原因，我们仍然建议在 INCAR 文件中手动指定截断能的具体数值，并在一组计算中保持恒定。

### LCHARG=.TRUE. | .FALSE.

默认值是 .TRUE.

决定是否输出文件 CHG 和 CHGCAR（有关电荷密度的文件）。

### ISMEAR = -5 | -4 | -3 | -2 | -1 | 0 | [integer]>0

ISMEAR 决定每个轨道上的部分占有率

[integer]>0：N阶 Methfessel-Paxton 方法。对于 Methfessel-Paxton 方案，部分占有率可能为负，也可能大于 1。这可能会导致绝缘物质的错误计算结果。

0：高斯展宽。

-1：费米展宽。

-2：部分占用率从 WAVECAR 或 INVO 文件中读取，并在整个运行过程中保持固定。

-3：对 INCAR 文件中提供的展宽参数执行循环。

-4：不带布洛赫修正的四面体方法。

-5：带布洛赫修正的四面体方法。

### SIGMA = [real]

能量的展宽。其默认值为 0.2。当 ISMEAR = -5 是，该值无影响。

### NELM = [integer]

NELM 是电子步自恰计算的步数 ，一般使用默认值 60。

### NELMIN = [integer]

电子自恰的最小步数，一般使用默认值 2，在瞬时 MD 和离子弛豫时用 4-8。

### EDIFF = [real]

默认值为 \(10^{-4}\)

决定了电子计算循环过程中的收敛判据，当两步电子步中总能量和能量本征值的差值均小于设置值时，认为已经收敛，电子步循环结束。对于高精度计算，建议设为 1E-6 甚至 1E-7（例如声子）。

### NSW = [integer]

默认值：NSW = 0

NSW 是离子步的最大步数，随着每一个离子步，最多有 NELM 步电子自恰步（考虑到 EDIFF 收敛条件）。

### IBRION = -1 | 0 | 1 | 2 | 3 | 5 | 6 | 7 | 8 | 44

IBRION 决定了离子的移动问题。

-1：离子不移动。

0：分子动力学 。

1：RMM-DIIS 准牛顿力学。

2：共轭梯度算法 。

3：阻尼动力学 。

5&6：是属于二阶导数：Hessian 矩阵和声子频率。

7&8：密度泛函和微扰理论。

44：改进的 Dimer 法。

### ISIF = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7

ISIF 控制应力张量是否被计算的问题，ISIF 也决定是否改变离子位置，晶胞体积和晶胞形状。

### EDIFFG = [real]

决定了结构优化过程中弛豫循环结束的收敛要求。

如果是正值，代表两次离子步的能量变化小于该值,单位为 \(\rm eV\) ；

如果是负值，代表离子受力小于该值的绝对值，单位为 \(\rm eV/\mathring{A}\) ；

一般使用受力作为结构优化时的收敛判据。默认值为 EDIFF \(\times 10\) 。

## 2 能带计算

### INCAR

将之前弛豫得到的 INCAR 、CONTCAR 、POTCAR 、CHGCAR 文件复制到一个新的文件夹中。当然，提交作业的脚本一般也要拷贝进去。然后复制 CONTCAR 为 POSCAR 。一定要记得使 INCAR 中的 NSW=0。

Global Parameters
ISTART = 0             (The data in the WAVECAR file is not used)
ISPIN  = 2             (Spin polarised DFT)
MAGMOM = 2*5 2*0 6*0
NPAR   = 6
SYMPREC= 1E-4
LORBIT = 11
ICHARG = 11            (Non-self-consistent: GGA/LDA band structures)
LREAL  = .FALSE.       (Projection operators: automatic)
ENCUT  = 400           (Cut-off energy for plane wave basis set, in eV)
LCHARG = .FALSE.       (Write CHGCAR or not)

Electronic Relaxation
ISMEAR = 0             (Gaussian smearing, metals:1)
SIGMA  = 0.05          (Smearing value in eV, metals:0.2)
NELM   = 90            (Max electronic SCF steps)
NELMIN = 6             (Min electronic SCF steps)
EDIFF  = 1E-05         (SCF energy convergence, in eV)

Ionic Relaxation
NSW    = 0             (Max ionic steps)
IBRION = 2             (Algorithm: 0-MD, 1-Quasi-New, 2-CG)
ISIF   = 3             (Stress/relaxation: 2-Ions, 3-Shape/Ions/V, 4-Shape/Ions)
EDIFFG = -2E-02        (Ionic convergence, eV/AA)

### 补充参数介绍

### ICHARG = 0 | 1 | 2 | 4 | 11 | 12

如何产生电荷密度

0：从初始轨道计算电荷密度，但是如果 WAVECAR 文件是无效的那么 ISTART=0 并且 ICHARG=2。

1：从 CHGCAR 中获得电荷密度 并且使用原子电荷密度的线性组合，并且与磁矩有关。

2：原子电荷密度的超叠加。

4：从 POT 中读取电荷密度。

11：从给定的电荷密度（旧的 CHGCAR )获取能带划分后的本征值和 DOS 自恰计算。

12：用于 MD 过程的非自洽计算。

### vaspkit

- 这时做能带计算的文件夹中必须有：INCAR 、POTCAR 、POSCAR 、CHGCAR 和提交作业的脚本。

- 使用 vaspkit 生成K点路径，具体过程：vaspkit \(\rightarrow\) 3 \(\rightarrow\) 302。

- 然后就会生成文件 KPATH . in 。

- 将 KPATH . in 复制为 KPOINTS。

- 通过脚本提交作业。

- 脚本运行完后，开始生成能带数据，具体过程：vaspkit \(\rightarrow\) 21 \(\rightarrow\) 211。

- 然后将生成的文件 BAND.dat 移动到 Origin 中开始画图。

注：在 vaspkit \(\rightarrow\) 3 \(\rightarrow\) 302 这一步中，我们可以根据我们要算的结构进行选择。

因为我算的是二维的 \( \rm MnPS_{3}\) ，所以选择的是 302 。

注：在能带计算的目录中，我们可以通 BAND_GAP 文件查看带隙。

BAND_GAP内容

\(\rm MnPS_{3}\) 的总带隙为 \(\rm 0.6491eV\) 。

## 3 Origin 画能带

1. 将 BAND.dat 移动到 Origin 中：

2. 绘图 \(\rightarrow\) 折线图：

3. 根据下图设定 X , Y 轴，并点确定：

4. 在生成的图中直接点击 Y 轴，在刻度页面中更改刻度的起始值和主刻度的值，并点击确定。

5. 将 Y 轴标题改为 E(eV)。将线的宽度设为 2。B 线注释改为 up , C 线注释改为 down。

6. 在静态计算的文件夹中打开 KLABELS（改文件中储存着 K 点位置信息）。

7. 根据 K 点位置信息，将 X 轴取值范围设为 0.000~1.523（根据自己的结果设置）。

主刻度的类型改为“按自定义位置”，下面输入 K 点的位置信息。

在刻度线标签中，显示 \(\rightarrow\) 类型 \(\rightarrow\) 刻度索引字符串。下面按照 KLABELS 中的顺序输入 K 点。

最后点击确定。

8. 最后画出的能带图为：

如有错误，欢迎指正。

---

## 本库注（收录时补充，非原文内容）

1. ⭐ **本篇把前几篇里「要不要带 `WAVECAR`」的疑问收口了**：能带步用的是 **`ISTART = 0`（不用 `WAVECAR`）+ `ICHARG = 11`（读 `CHGCAR` 并固定）**，拷贝清单里也只有 `CHGCAR`——**这是最省事、无歧义的组合**，已写进 `workflows.md` 第三节。（对比：`ISTART=1` 却只拷 `CHGCAR` 的写法容易让人怀疑到底读进了什么。）
2. **`NPAR=6`**：文中参数介绍的规则是 `NPAR ≈ √核数` 或 `≈ 每节点核数`；本库已把这条与其它 NPAR 经验并列（见 `references/performance.md` §4.1/§4）。
3. **`SYMPREC=1E-4`**（默认 `1E-5`）：放宽对称性判据可让程序识别出更「整齐」的对称性——二维/畸变体系常这么用，但要意识到**这会影响后续用到的对称性**（见 `errors.md` §8.2）。
4. **`ISIF=3` 与 `NSW=0` 同现**（能带步）：`NSW=0` 不会弛豫，`ISIF≥3` 只是让程序顺带算应力——可省略。

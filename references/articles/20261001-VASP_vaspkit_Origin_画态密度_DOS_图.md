# VASP vaspkit Origin 画态密度（DOS）图

- 来源: `https://zhuanlan.zhihu.com/p/574160228`
- 类型: html
- 来源: `https://zhuanlan.zhihu.com/p/574160228`（经知乎开放平台 CLI `me content --content-url` 读取，**本人文章**；`Data.Url` 与链接一致）
- 类型: html（zhihu-cli JSON → HTML 后收录；公式已内联）
- 标签: 知乎, 本人文章, DOS, Origin, VASPKIT, Ru
- ⚠️ 抓取说明：两段 INCAR 在导出时**连空格一起丢了**（`GlobalParametersISTART=0…`），本库已按 VASP 语法重新排版；文末附「本库注」。
- 正文字数: 6477

---
如果计算步骤是：结构优化 \(\Rightarrow\) 静态自洽计算 \(\Rightarrow\) 态密度计算；这么计算的结构会精确。

在本篇文章中，计算步骤是：结构优化 \(\Rightarrow\) 态密度计算；这么计算是可以的，但是精确度不如上面。

结构优化过程中生成的 CHGCAR 和 WAVECAR 文件是对应于最后一步迭代的电荷密度和波函数，而不是对应于结构优化后的体系。结构优化后的体系可能与最后一步迭代的体系有微小的差别，导致电荷密度和波函数不完全一致。所以使用结构优化过程中生成的 CHGCAR 和 WAVECAR 文件进行计算的精确度比使用静态自洽计算生成的 CHGCAR 和 WAVECAR 文件进行计算的精确度有点差。

## 0 计算材料

该材料为钌（ \(\rm Ru\) ）元素构成，空间群是 \(\rm P6_{3}/mmc\) 的晶体。其中一个 \(\rm Ru\) 原子与周围 12 个 \(\rm Ru\) 原子构成十四面体。所形成的十二个键中，有 6 个短键（ \(\rm 2.67 \mathring{A}\) ）和 6 个长键（ \(\rm 2.73\mathring{A}\) ）。

## 1 结构弛豫

### POSCAR

POSCAR 内容可以直接从网站 [The Materials Project](https://materialsproject.org/) 上下载（如下图所示）。

选中 POSCAR 就可以下载相应形式的文件。

然后将下载的文件拖到服务器中，再将文件名改为 POSCAR 。

### KPOINTS

在准备好 POSCAR 后，通过 vaspkit 生成 KPOINTS 文件。

在命令行依次输入下面命令：

vaspkit \(\rightarrow\) 1 \(\rightarrow\) 102 \(\rightarrow\) 2 \(\rightarrow\) 0.04

注：在这一步中，vaspkit 会自动生成 POTCAR 。所以就不需要另外生成 POTCAR 了。

注：在选 K 点设置的方法中，vaspkit 有两种：Monkhorst-Pack Scheme和 Gamma Scheme 。当设定各维度的 K 点数为奇数时，两种方法的撒点是一样的，且都包含 K 空间的 Gamma 点；为偶数时，MP 撒点不包含Gamma 点，Gamma 撒点在 MP 撒点的基础上进行平移，保证采到 Gamma 点（根据自己的需要选取相应的撒点方式）。

### INCAR

Global Parameters
ISTART = 0             (Read existing wavefunction; if there)
ISPIN  = 1             (Non-Spin polarised DFT)
LREAL  = .FALSE.       (Projection operators: automatic)
ENCUT  = 400           (Cut-off energy for plane wave basis set, in eV)
PREC   = Normal        (Precision level)
LWAVE  = .FALSE.       (Write WAVECAR or not)
LCHARG = .TRUE.        (Write CHGCAR or not)
ADDGRID= .TRUE.        (Increase grid; helps GGA convergence)

Lattice Relaxation
NSW    = 300           (number of ionic steps)
ISMEAR = 0             (gaussian smearing method)
SIGMA  = 0.05          (please check the width of the smearing)
IBRION = 2             (Algorithm: 0-MD; 1-Quasi-New; 2-CG)
ISIF   = 3             (optimize atomic coordinates and lattice parameters)
EDIFFG = -1.5E-02      (Ionic convergence; eV/AA)
PREC   = Accurate      (Precision level)
EDIFF  = 1.0E-5

注：在进行弛豫计算的时候，我们一般要保证弛豫是在一个离子步内算完。因为在弛豫过程中，晶格的大小和基组可能会改变，一个离子步算完更精确。

在第一次弛豫的时候，我们往往难以一个离子步收敛，所以我们需要将 CONTCAR 复制成 POSCAR 再次进行弛豫，直到一个离子步内收敛。

注：金属体系结构弛豫的时候，不能使用 ISMEAR =-5，应为 ISMEAR \(\geq\) 0 。

### 参数介绍

### ISTART = 0 | 1 | 2 | 3

0：在没有 WAVECAR 文件时，默认值为 0 。轨道的初始化由 INIWAV 所决定。

1：读取 WAVECAR 文件，并且平面波集会改变。计算时，会读取 INCAR 中设置的 ENCUT 数值和之前计算生成的 WAVECAR 中的 Orbitals 。根据新的元胞（ POSCAR ）和新的平面波截断能（ INCAR 中）产生新的平面波基组。

2：读取 WAVECAR 文件，但是平面波集不变，并使其他参数发生改变（计算体积-能量相关曲线的时候用到）。

3：在重启分子动力学计算的时候使用，同时需要 WAVECAR 、CHGCAR（用于储存电荷密度信息）文件。

### ISPIN = 1 | 2

1：进行了非自旋极化计算。

2：进行了自旋极化计算。

### LREAL = .FALSE. | Auto (or A) | On (or O) | .TRUE.

.FALSE. :在倒空间中完成投影。

.TRUE. :在实空间完成投影。采用的是一种最简单将高频组分与投影算符分开的方法。

On (or O)：采用优化过的实空间算符进行投影。

Auto (or A)：采用更好的优化。一般实空间原子数在 20 个以上才考虑（较老的 VASP 版本是 20，新的 VASP 版本是 30 ）。

### ENCUT = [real]

平面波的截断能。不需要明确 INCAR 中的 ENCUT 值，在 POTCAR 中有最大和最小的截断能。在两个或以上的物质进行计算时，会使用最大的截断能。出于一致性原因，我们仍然建议在 INCAR 文件中手动指定截断能的具体数值，并在一组计算中保持恒定。

### PREC = Low | Medium | High | Normal | Single | Accurate

当且仅当在 INCAR 中没有给定 `ENCUT` 时（原文此处写作 `ENCAT`，系笔误），PREC 才决定截断能。在 PREC=High 的时候 ENCUT 是 POTCAR中的 1.3 倍。但是，我们只需手动增加 INCAR 文件中的 ENCUT 即可达到相同的效果。

受 PREC 影响的参数有四类：ENCUT；NGX，NGY，NGZ；NGXF，NGYF，NGZF；ROPT。如果设置了 PREC ，这些参数就都不需要出现了，当然直接设置相应的参数也有同样效果。

### LWAVE = [logical]

LWAVE 确定是否在运行结束时将波函数写入 WAVECAR 文件。

### LCHARG = [logical]

默认值是 .TRUE.

LCHARG 确定是否写入电荷密度（文件 CHGCAR 和 CHG ）。

### ADDGRID = .TRUE. | .FALSE.

默认值是 .FALSE.

ADDGRID 确定是否增加网格帮助收敛。

### NSW = [integer]

NSW 是离子步的最大步数，随着每一个离子步，最多有 NELM 步电子自恰步（考虑到 EDIFF 收敛条件）。

### ISMEAR = -5 | -4 | -3 | -2 | -1 | 0 | [integer]>0

ISMEAR 决定每个轨道上的部分占有率

[integer]>0：N 阶 Methfessel-Paxton 方法。对于 Methfessel-Paxton 方案，部分占有率可能为负，也可能大于 1 。这可能会导致绝缘物质的错误计算结果。

0：高斯展宽。

-1：费米展宽。

-2：部分占用率从 WAVECAR 或 INVO 文件中读取，并在整个运行过程中保持固定。

-3：对 INCAR 文件中提供的展宽参数执行循环。

-4：不带布洛赫修正的四面体方法。

-5：带布洛赫修正的四面体方法。

### SIGMA = [real]

能量的展宽。其默认值为 0.2 。当 ISMEAR = -5 是，该值无影响。

### IBRION = -1 | 0 | 1 | 2 | 3 | 5 | 6 | 7 | 8 | 44

IBRION决定了离子的移动问题。

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

### EDIFF = [real]

决定了电子计算循环过程中的收敛判据，当两步电子步中总能量和能量本征值的差值均小于设置值时，认为已经收敛，电子步循环结束。对于高精度计算，建议设为 1E-6 甚至 1E-7（例如声子）。默认值为 \(10^{-4}\) 。

## 2 态密度计算

将 POTCAR 、KPOINTS 、CHGCAR 、CONTCAR 和提交脚本复制到态密度计算的文件夹中。

将 KPOINTS 中的格点数量翻倍。

通过命名将 CONTCAR 复制为 POSCAR

cp CONTCAR POSCAR

### INCAR

Global Parameters
ISTART = 0             (Read existing wavefunction; if there)
ISPIN  = 1             (Non-Spin polarised DFT)
LREAL  = .FALSE.       (Projection operators: automatic)
ENCUT  = 400           (Cut-off energy for plane wave basis set, in eV)
PREC   = Normal        (Precision level)
LWAVE  = .FALSE.       (Write WAVECAR or not)
LCHARG = .TRUE.        (Write CHGCAR or not)
ADDGRID= .TRUE.        (Increase grid; helps GGA convergence)

Lattice Relaxation
NSW    = 0             (number of ionic steps)
ISMEAR = -5            (gaussian smearing method)
SIGMA  = 0.05          (please check the width of the smearing)
IBRION = -1            (Algorithm: 0-MD; 1-Quasi-New; 2-CG)
ISIF   = 3             (optimize atomic coordinates and lattice parameters)
EDIFFG = -1.5E-02      (Ionic convergence; eV/AA)
PREC   = Accurate      (Precision level)
EDIFF  = 1.0E-5

#DOS control:
EMIN   = -10
EMAX   = 30
NEDOS  = 1001
LORBIT = 11

注：参数 EMIN 和 EMAX 只能划定 DOS 图取值的大致范围，输出的结果并不会真的是从 -10 到 30 。

注：ISMEAR = -5 适用于所有体系的 DOS 计算。

### 补充参数介绍

### EMIN = [real]

DOS 能量范围的下限。

### EMAX = [real]

DOS 能量范围的上限。

### NEDOS = [integer]

默认值：301

NEDOS 确定 DOS 图横坐标Energy（eV）取点的数量。

### LORBIT=0 | 1 | 2 | 5 | 10 | 11 | 12

结合 RWIGS 标签确定是否输出 PROCAR 或 PROOUT 文件，当设置大于等于 10 时不需要设置 RWIGS 标签，一般设置成 11 ，会输出投影到各个原子各个轨道的分波态密度。

### 使用vaspkit

vaspkit 生成 DOS 数据的具体过程：

vaspkit \(\rightarrow\) 11 \(\rightarrow\) 114 \(\rightarrow\) Ru

之后生成的文件 PDOS_SUM.dat 就会有我们需要的各个轨道以及总共的 DOS 数据。

注：

在文件 SELECTED_ATOMS_LIST 会显示具体导入的是哪个原子，如下图所示：

如果在 vaspkit 中输入：

vaspkit \(\rightarrow\) 11 \(\rightarrow\) 114 \(\rightarrow\) 1

则会只导入代号为 1 的原子，SELECTED_ATOMS_LIST 中显示为：

### d轨道画一起

如果想将所有的 d 轨道的 DOS 加起来，我们需要在最后 vaspkit 处理的时候改变一下内容。

在使用 vaspkit 的时候，输入一下命令：

vaspkit \(\rightarrow\) 11 \(\rightarrow\) 115 \(\rightarrow\) Ru \(\rightarrow\) dxy dyz dz2 dxz dx2 \(\rightarrow\) Ru \(\rightarrow\) dxy \(\rightarrow\) Ru \(\rightarrow\) dyz \(\rightarrow\)

Ru \(\rightarrow\) dz2 \(\rightarrow\) Ru \(\rightarrow\) dxz \(\rightarrow\) Ru \(\rightarrow\) dx2

之后会生成数据文件 PDOS_USER.dat ，将文件拖入 Origin 作图就可以了。

## Origin画图

1、将生成的 PDOS_SUM.dat 文件拖入 Origin 。

2、点击界面左下角的图标（如下图所示）。

3、在弹出的界面中选中数据作为 x 轴和 y 轴的数据（如下图所示）。

4、弹出的图可能不是我们想要的（如下图所示）。

我们需要：

- 更改 x 、y 轴的标题；

- 更改 x 轴的取值范围；

- 添加有边框和上边框；

- 增加线的宽度；

最后的结果如下：

d轨道DOS图各个d轨道以及总共的d轨道的DOS图

## 问题

1、vapskit 111 生成的 .dat 文件放到 original 里面出来的图的费米能级就已经默认是在 0 处吗？

是的，画出的 DOS 图费米能级已经默认在 0 处。

如有错误，欢迎指正。

---

## 本库注（收录时补充，非原文内容）

1. **正文笔误**：`PREC` 那段里的「没有给定 `ENCAT`」应为 **`ENCUT`**（已订正）。
2. **同一个 INCAR 里 `PREC` 出现两次**（先 `Normal`、后 `Accurate`）：**建议只留一个**（`PREC` 会连带决定 `ENCUT`/`NGX-NGZ`/`NGXF-NGZF`/`ROPT` 四类参数，重复写容易让人误判实际生效值）。
3. **两段 INCAR 都没有显式写 `ICHARG`**，而拷贝清单里也没有 `WAVECAR`：若 DOS/能带结果与自洽步对不上，先确认是否真的读进了上一步的电荷密度（必要时显式 `ICHARG = 1` 或 `11`，见 `workflows.md` §30.4）。
4. **`ISIF=3` 与 `NSW=0` 同时出现**：`NSW=0` 时不会发生弛豫，`ISIF≥3` 只是让程序顺带计算应力张量——对 DOS 计算没有影响，但可以省略。
5. 本步**把 KPOINTS 格点翻倍**、`EMIN/EMAX/NEDOS` 与「费米能级默认已在 0」这几条已被提炼进 `workflows.md` §4.2。

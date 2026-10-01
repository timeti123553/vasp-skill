# VASP vaspkit 画 HSE06 能带图

- 来源: `https://zhuanlan.zhihu.com/p/590781664`
- 类型: html
- 来源: `https://zhuanlan.zhihu.com/p/590781664`（经知乎开放平台 CLI `me content --content-url` 读取，**本人文章**；`Data.Url` 与链接一致）
- 类型: html（zhihu-cli JSON → HTML 后收录）
- 标签: 知乎, 本人文章, HSE06, 能带, VASPKIT, SrMoO₄
- ⚠️ 抓取说明：知乎正文的 **LaTeX 公式是图片**，导出后只剩空位——本库已按 JSON 里的 `alt` 文本补齐（并把 `zhihu_json_to_html.py` 修好，以后知乎文章不再丢公式）；**代码块/INCAR 仍被压成单行**。
- 正文字数: 6840

---
## 0 计算材料

**SrMoO₄** 是锆石状结构，属于 **I4₁/a** 空间群。**Sr²⁺** 连接到 8 个 **O²⁻** 原子。**Sr–O** 键有两种键长，四个较短的键长 **2.61 Å**，四个较长的键长 **2.66 Å**。**Mo⁶⁺** 连接到 4 个等效的 **O²⁻** 原子，并形成四面体结构。**Mo–O** 键键长均为 **1.80 Å**。

> ⚠️ **本段公式在导出时丢失，已由本库按原文（知乎正文的 LaTeX 图片 `alt` 文本）补齐**。
> 📌 **本库注（结构原型名）**：按空间群 **`I4₁/a`（No. 88）** 判断，SrMoO₄ 属于**白钨矿（scheelite）型**；**锆石（zircon, ZrSiO₄）是 `I4₁/amd`（No. 141）**。两者同属四方晶系、配位方式相近，所以常被混称——**写论文时建议用「白钨矿型」或直接写空间群**。

## 1 结构弛豫

### POSCAR

1. POSCAR 从网站 [The Materials Project](https://materialsproject.org/) 上下载 的 POSCAR 文件（如下图所示）。

2. 将生成的 POSCAR 格式的文件拖入服务器对应的目录下。

### KPOINTS

在准备好 POSCAR 后，通过 vaspkit 生成 KPOINTS 文件。

在命令行依次输入下面命令：

vaspkit 1 102 2 0.03

注：在这一步中，vaspkit 会自动生成 POTCAR 。所以就不需要另外生成 POTCAR 了。

注：在选K点设置的方法中，vaspkit 有两种：Monkhorst-Pack Scheme 和 Gamma Scheme 。当设定各维度的K 点数为奇数时，两种方法的撒点是一样的，且都包含 K 空间的 Gamma 点；为偶数时，MP 撒点不包含 Gamma 点，Gamma 撒点在 MP 撒点的基础上进行平移，保证采到 Gamma 点（根据自己的需要选取相应的撒点方式）。一般选 Gamma 点比较稳妥。

### INCAR

INCAR 使用的是 vaspkit 默认生成的结构弛豫的 INCAR （有些地方改了一下）。

vaspkit 1 101 LR

Global Parameters ISTART = 1 (Read existing wavefunction; if there) ISPIN = 1 (Non-Spin polarised DFT) # ICHARG = 11 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 400 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) # LVTOT = .TRUE. (Write total electrostatic potential into LOCPOT or not) # LVHAR = .TRUE. (Write ionic + Hartree electrostatic potential into LOCPOT or not) # NELECT = (No. of electrons: charged cells; be careful) # LPLANE = .TRUE. (Real space distribution; supercells) NPAR = 4 (Max is no. nodes; don't set for hybrids) # Nwrite = 2 (Medium-level output) KPAR = 4 (Divides k-grid into separate groups) # NGX = 500 (FFT grid mesh density for nice charge/potential plots) # NGY = 500 (FFT grid mesh density for nice charge/potential plots) # NGZ = 500 (FFT grid mesh density for nice charge/potential plots) Lattice Relaxation NSW = 300 (number of ionic steps) ISMEAR = 0 (gaussian smearing method ) SIGMA = 0.05 (please check the width of the smearing) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 3 (optimize atomic coordinates and lattice parameters) EDIFFG = -1.5E-02 (Ionic convergence; eV/AA) #PREC = Accurate (Precision level)

注：NPAR 和 KPAR 相乘需要是核数的整数倍。

## 2 能带计算

将计算的 WAVECAR, CHGCAR, CONTCAR, POTCAR 和提交脚本复制到做 HSE06 的目录下。

将 CONTCAR 复制为 POSCAR 。

注：能带计算比较耗时，我们可以设置多个节点并行计算。

注：INCAR 中的参数 NPAR 和 KPAR 根据自身情况的修改可以显著的提高计算效率。

注：如果该步计算，第一次没有算完，然后停掉了。在没有删除第一步任何文件的情况下，重新提交作业，第二次计算的速度有时候会比第一次快一些。

### KPOINTS

使用 vaspkit 生成 KPOINTS 文件，具体过程如下：

vaspkit 303 KPATH . in

vaspkit 251 2 0.04 0.06 KPOINTS

### INCAR

Global Parameters ISTART = 1 (Read existing wavefunction; if there) ISPIN = 1 (Non-Spin polarised DFT) ICHARG = 1 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 400 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) # LVTOT = .TRUE. (Write total electrostatic potential into LOCPOT or not) # LVHAR = .TRUE. (Write ionic + Hartree electrostatic potential into LOCPOT or not) # NELECT = (No. of electrons: charged cells; be careful) # LPLANE = .TRUE. (Real space distribution; supercells) NPAR = 4 (Max is no. nodes; don't set for hybrids) # Nwrite = 2 (Medium-level output) KPAR = 6 (Divides k-grid into separate groups) # NGX = 500 (FFT grid mesh density for nice charge/potential plots) # NGY = 500 (FFT grid mesh density for nice charge/potential plots) # NGZ = 500 (FFT grid mesh density for nice charge/potential plots) Lattice Relaxation NSW = 0 (number of ionic steps) ISMEAR = 0 (gaussian smearing method ) SIGMA = 0.05 (please check the width of the smearing) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 3 (optimize atomic coordinates and lattice parameters) EDIFFG = -1.5E-02 (Ionic convergence; eV/AA) # PREC = Accurate (Precision level) HSE06 Calculation LHFCALC= .TRUE. (Activate HF) AEXX = 0.25 (25% HF exact exchange, adjusted this value to reproduce experimental band gap) HFSCREEN= 0.2 (Switch to screened exchange; e.g. HSE06) ALGO = ALL (Electronic Minimisation Algorithm; ALGO=58) TIME = 0.4 (Timestep for IALGO5X) PRECFOCK= Fast (HF FFT grid) ! NKRED = 2 (Reduce k-grid-even only, see also NKREDX, NKREDY and NKREDZ) # HFLMAX = 4 (HF cut-off: 4d, 6f) # LDIAG = .TRUE. (Diagnolise Eigenvalues)

注：NPAR 和 KPAR 相乘需要是核数的整数倍。

注：OUTCAR 中查看时间命令：

grep LOOP OUTCAR grep LOOP+ OUTCAR

注：下面这个三个参数都是默认值，不写也没有关系。

- LCHARG=.TRUE.（读取 CHGCAR ）

- LWAVE=.TRUE.（读取 WAVECAR ）

- NSW=0（设为只进行一次离子步）

### 参数介绍

### ISTART

ISTART = 0 | 1 | 2 | 3

0：在没有 WAVECAR 文件时，默认值为 0。轨道的初始化由 INIWAV 所决定。

1：读取 WAVECAR 文件，并且平面波集会改变。计算时，会读取 INCAR 中设置的 ENCUT 数值和之前计算生成的 WAVECAR 中的 Orbitals 。根据新的元胞（ POSCAR ）和新的平面波截断能（ INCAR 中）产生新的平面波基组。

2：读取 WAVECAR 文件，但是平面波集不变，并使其他参数发生改变（计算体积-能量相关曲线的时候用到）。

3：在重启分子动力学计算的时候使用，同时需要 WAVECAR 、CHGCAR（用于储存电荷密度信息）文件。

### LHFCALC

默认值是 .FALSE.

决定是否对杂化泛函进行调用，明确了 H-F 类型的计算是否开启。

### AEXX

当 LHFCALC= .TRUE. 时，AEXX 的默认值是 0.25 。

当 LHFCALC= .FALSE. 时，AEXX 的默认值是 0 。

代表交换能的分数。

### HFSCREEN

HFSCREEN 决定了分离杂化泛函范围的参数。在结合 PEB 势时，将会从 PEB0 泛函转换为 HSE03 或者 HSE06 泛函。HSE03 和 HSE06 泛函取代了缓慢衰减的 Fock 交换长程作用。

HFSCREEN= 0.2 HSE06

HFSCREEN= 0.3 HSE03

### ALGO

默认值：Normal

明确电子最简化的算法的选择。

### TIME

默认值：0.4

在 IALGO=4X 的初始（最陡下降）阶段，TIME控制 IALGO=5X 的试验时间步长。

### PRECFOCK

默认值：Normal

PRECFOCK= Low | Medium | Fast | Normal | Accurate

PRECFOCK 参数控制精确交换（Hartree Fock）例程的 FFT 网格，即可以为精确交换部分以及局部 Hartree 和 DFT 电势选择不同的网格。

### NKRED

NKRED 或 NKREDX 、NKREDY 和 NKREDZ 是可用于评估在 q 点的子网格上的 Hartree-Fock 核。

### HFLMAX

### LDIAG

默认值：.TRUE.

执行子空间旋转。

## 3 绘图

使用 vaspkit 进行绘图。

在绘图之前先确保 ~/.vaspkit 目录下装了相关 python 和画图的参数设置正确：

PYTHON_BIN ~/miniconda3/bin/python3.9 PLOT_MATPLOTLIB .TRUE.

在 HSE06 能带计算的目录下运行 vaspkit ：

vaspkit 252 0

之后就会生成相应的文件：

- BAND.dat

- REFORMATTED_BAND.dat

- KLINES.dat

- KLABELS

- BAND_GAP

- TDOS_EIG.dat

- band.png

画出的 band.png 图片为：

注：画能带图的具体过程在 vaspkit 的官网也有详细的过程介绍：

[https://vaspkit.com/tutorials.html#example-single-layer-mos2-1](https://vaspkit.com/tutorials.html#example-single-layer-mos2-1)

## 4 问题

1、结构优化、静态自洽计算和能带计算的区别是什么？

之前文章中说，进行结构优化后的步骤是静态计算，这样说确实有些不妥。可能是个人不好的习惯吧，会把 NSW=0 的计算都说成是静态计算。现在我已经把那一章节中的标题改为“能带计算”。

结构优化：对输入体系的原子坐标进行调整，得到一个相对稳定的基态结构。

静态自洽计算：在结构优化后固定原子坐标，对输入体系的电子密度进行迭代求解，得到 CHACAR 和 WAVECAR 文件。

能带计算：在静态自洽计算后读入 CHGCAR 文件，对输入体系的能量本征值进行非自洽求解，得到能带结构。

注：在静态自洽计算和能带计算中，我们不需要让离子移动（ NSW=0 ），只需要求解电子结构。

如果计算步骤是：结构优化 静态自洽计算 能带计算；这么计算的结构会精确。

在本篇文章中，计算步骤是：结构优化 能带计算；这么计算是可以的，但是精确度不如上面。

结构优化过程中生成的 CHGCAR 和 WAVECAR 文件是对应于最后一步迭代的电荷密度和波函数，而不是对应于结构优化后的体系。结构优化后的体系可能与最后一步迭代的体系有微小的差别，导致电荷密度和波函数不完全一致。所以使用结构优化过程中生成的 CHGCAR 和 WAVECAR 文件进行计算的精确度比使用静态自洽计算生成的 CHGCAR 和 WAVECAR 文件进行计算的精确度有点差。

2、静态计算和自洽计算的区别是什么？

静态计算：在原子位置固定的情况下，对电子进行自洽迭代，得到体系的最低能量和电荷密度。静态计算一般在结构优化后进行，用于计算体系的基本性质，如能带结构、态密度等。

自洽计算：自洽计算是指在每个离子步长中，对电子进行自洽迭代，得到体系的能量和电荷密度，并根据力或应力更新原子位置，直到达到收敛判据。自洽计算一般用于结构优化或分子动力学模拟，用于寻找体系的稳定结构或研究体系的动力学行为。

注：静态计算也叫静态自洽计算。

如有错误，欢迎指正。

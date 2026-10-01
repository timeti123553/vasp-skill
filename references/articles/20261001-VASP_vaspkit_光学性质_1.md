# VASP vaspkit 光学性质|1

- 来源: `https://zhuanlan.zhihu.com/p/625881446`（经知乎开放平台 CLI `me content --content-url` 读取，**本人文章**；`Data.Url` 与链接一致）
- 类型: html（zhihu-cli JSON → HTML 后收录；公式已内联 **17 处**）
- 标签: 知乎, 本人文章, 光学性质, VASPKIT, 二维材料, 710, InSe
- 📌 参考来源：作者明确说明本文参考 **贺勇的博客** <https://yh-phys.github.io/2019/10/12/vasp-optics/>（即本库 `articles/20261001-vasp计算光学性质教程.md` 的同一来源）。
- 正文字数: 5785

---
本文主要参考的文章为：

[vasp计算光学性质 | Physics](https://yh-phys.github.io/2019/10/12/vasp-optics/)

## 0 计算材料

Materials Project 网站上材料的代号：mp-20485

\(\rm InSe\) 是黑磷衍生结构，在六方 \(\rm P6_3/mmc\) 空间群中结晶。

该结构是二维的，由四个沿 \(\rm (0,0,1)\) 方向排列的 \(\rm InSe\) 层组成。

\(\rm In^{2+}\) 以扭曲的三角非共面几何结构与三个等效的 \(\rm Se^{2-}\) 原子键合。

所有 \(\rm In\verb|-|Se\) 键长均为 \(\rm 2.65~\mathring{A}\) 。

\(\rm Se^{2-}\) 以扭曲的三角非共面几何结构与三个等效的 \(\rm In^{2+}\) 原子键合。

## 1 结构优化

需要准备的文件：

- INCAR（vaspkit 生成再修改）

- POTCAR（vaspkit 生成）

- KPOINTS（vaspkit 生成）

- POSCAR（从 Materials Project 或其他数据库获取）

- 作业提交脚本

注：本文使用的 POTCAR 是 PBE 泛函。

### INCAR

Global Parameters ISTART = 0 (Read existing wavefunction; if there) ISPIN = 1 (Non-Spin polarised DFT) # ICHARG = 11 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 500 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .FALSE. (Write WAVECAR or not) LCHARG = .FALSE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) Electronic Relaxation ISMEAR = 0 (Gaussian smearing; metals:1) SIGMA = 0.02 (Smearing value in eV; metals:0.2) NELM = 90 (Max electronic SCF steps) NELMIN = 6 (Min electronic SCF steps) EDIFF = 1E-05 (SCF energy convergence; in eV) # GGA = PS (PBEsol exchange-correlation) Ionic Relaxation NSW = 100 (Max ionic steps) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 2 (Stress/relaxation: 2-Ions, 3-Shape/Ions/V, 4-Shape/Ions) EDIFFG = -1E-02 (Ionic convergence; eV/AA) # ISYM = 2 (Symmetry: 0=none; 2=GGA; 3=hybrids)

### KPOINTS

KPT-Resolved Value to Generate K-Mesh: 0.020 0 Gamma 15 15 3 0.0 0.0 0.0

## 2 静态自洽计算

需要准备的文件：

- INCAR（vaspkit 生成之后再修改，或者把结构优化的 INCAR 的内容修改一些）

- POTCAR（vaspkit 生成，或者把结构优化目录下的 POTCAR 粘贴到本目录下）

- KPOINTS（vaspkit 生成，或者自己写）

- POSCAR（将结构优化下的 CONTCAR 复制为本目录下的 POSCAR ）

- 作业提交脚本

### INCAR

Global Parameters ISTART = 0 (Read existing wavefunction; if there) ISPIN = 1 (Non-Spin polarised DFT) # ICHARG = 11 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 500 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) Electronic Relaxation ISMEAR = 0 (Gaussian smearing; metals:1) SIGMA = 0.02 (Smearing value in eV; metals:0.2) NELM = 90 (Max electronic SCF steps) NELMIN = 6 (Min electronic SCF steps) EDIFF = 1E-05 (SCF energy convergence; in eV) # GGA = PS (PBEsol exchange-correlation) Ionic Relaxation NSW = 0 (Max ionic steps) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 2 (Stress/relaxation: 2-Ions, 3-Shape/Ions/V, 4-Shape/Ions) EDIFFG = -1E-02 (Ionic convergence; eV/AA) # ISYM = 2 (Symmetry: 0=none; 2=GGA; 3=hybrids)

### KPOINTS

KPT-Resolved Value to Generate K-Mesh: 0.020 0 Gamma 25 25 3 0.0 0.0 0.0

## 3 光学性质计算

需要准备的文件：

- INCAR（vaspkit 生成之后再修改，或者把结构优化的 INCAR 的内容修改一些）

- POTCAR（vaspkit 生成，或者把结构优化目录下的 POTCAR 粘贴到本目录下）

- KPOINTS（vaspkit 生成，或者自己写）

- POSCAR（将结构优化下的 CONTCAR 复制为本目录下的 POSCAR ）

- WAVECAR（将自洽计算目录下的 WAVECAR 复制到本目录下）

- CHGCAR（将自洽计算目录下的 WAVECAR 复制到本目录下）

- 作业提交脚本

### INCAR

Global Parameters ISTART = 1 (Read existing wavefunction; if there) ISPIN = 1 (Non-Spin polarised DFT) ICHARG = 11 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 500 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .FALSE. (Write WAVECAR or not) LCHARG = .FALSE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) Electronic Relaxation ISMEAR = 0 (Gaussian smearing; metals:1) SIGMA = 0.02 (Smearing value in eV; metals:0.2) NELM = 90 (Max electronic SCF steps) NELMIN = 6 (Min electronic SCF steps) EDIFF = 1E-05 (SCF energy convergence; in eV) # GGA = PS (PBEsol exchange-correlation) Ionic Relaxation NSW = 0 (Max ionic steps) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 2 (Stress/relaxation: 2-Ions, 3-Shape/Ions/V, 4-Shape/Ions) EDIFFG = -1E-02 (Ionic convergence; eV/AA) # ISYM = 2 (Symmetry: 0=none; 2=GGA; 3=hybrids) Opt NBANDS = 96 LOPTICS= .TRUE. NEDOS = 2000 CSHIFT = 0.1

注：光学计算中 NBANDS 的取值一般为自洽计算 OUTCAR 中 NBANDS 值的 2~3 倍。

### NBANDS

默认值：max(NELECT/2+NIONS/2,NELECT*0.6)

NBANDS 指定了计算中 KS 或 QP 轨道的总数。

NBANDS 的正确选择强烈依赖于所执行计算的类型和系统。

作为最小值，VASP 需要所有占据态 + 一个空带，否则会发出警告。

### LOPTICS

默认值： .FALSE.

LOPTICS = .TRUE. 时，在确定电子基态状态后，计算与频率相关的介电矩阵。

### CSHIFT

默认值：0.1（线性相应计算）

默认值：OMEGAMAX*1.3 / max(NOMEGA,40)（GW 计算）

CSHIFT 分别在线性响应和 GW 计算中的 Kramers-Kronig 变换和 Hilbert 变换中设置（小）复位移 \(\eta\) 。

### KPOINTS

KPT-Resolved Value to Generate K-Mesh: 0.020 0 Gamma 30 30 3 0.0 0.0 0.0

注：k 点网格的取值一般为自洽值或者适当增加。

## 4 数据处理

使用 vaspkit.1.2.4 来进行后续数据的处理。

在 VASP 计算完成后，输入：

vaspkit \(\Rightarrow\) 71 \(\Rightarrow\) 710 \(\Rightarrow\) 1

（使用的能量单位为 \(\rm eV\) ）

注：因为我们计算的材料是二维材料，所以我们选择 710 。

输出的文件有：

- ABSORPTION_2D.dat（光吸收系数）

- IMAG_OPTICAL_CONDUCTIVITY_2D.dat（光学导电率虚部）

- real_OPTICAL_CONDUCTIVITY_2D.dat（光学导电率实部）

- REFLECTION_2D.dat（反射系数）

- TRANSMISSION_2D.dat（透射系数）

- IMAG. in（复介电函数虚部）

- real. in （复介电函数实部）

ABSORPTION_2D.dat 文件中 x 方向的光稀释系数如下：

我们可以看出在 \(\rm 3.7871~eV\) 和 \(\rm 4.0992~eV\) 出有吸收峰。

与其他人的计算结构对比：

我们可以发现，计算结果较为符合。

## 5 问题

1、计算的结果为什么在材料的带隙以下会有吸收系数？下面的参考图没有，是不是还得进行一个处理？

相同材料，其他人计算的结果在材料的带隙下没有吸收系数，我认为是我将真空层的厚度也做优化导致的。

我将所有步骤的输入文件调成与文章“ [vasp 计算光学性质](https://yh-phys.github.io/2019/10/12/vasp-optics/)”的一致（除了 OPTCELL 文件），我得到的输出结构如下：

注：vaspkit 使用的是 711 而不是 710 （为了与原文一致）。

注：OPTCELL 文件中的内容是为了固定基矢。这个文件需要更该并重新编译 VASP ，而我的 VASP 没有重新编译，所以不需要准备这个输入文件。

我们可以发现，在材料的带隙之下还是有吸收谱。

如果要设置在计算过程中不对真空层厚度做优化，我们需要将 VASP 的安装包重新进行编译。

VASP 安装包的详细说明在刘锦程的文章中有：

[VASP固定基矢优化结构方法](https://blog.shishiruqi.com//2019/05/05/constr/)

如有错误，欢迎指正。

---

## 本库注（收录时补充，非原文内容）

1. ⭐⭐ **本文的最大贡献：把 VASPKIT 的 `710` 与 `711` 分清楚了**——
   **低维材料用 `710`（输出 `ABSORPTION_2D.dat` 等 `*_2D.dat` 系列），`711` 是三维块体的线性光学**。这正好解释了上一轮那篇教程里**「VASPKIT 提示 711 不适用于低维材料，却仍用二维 InSe 演示」**的矛盾：**应该走 `710`**（本库已把这条写进 `workflows.md` §36.9，并回填到 §36.8 的语境里）。
2. ⭐ **两个默认值公式**（此前库里只有「默认 0.1」这类半截话）：**`NBANDS` 默认 `max(NELECT/2 + NIONS/2, NELECT×0.6)`**；**`CSHIFT` 线性响应默认 `0.1`**（GW 为 `OMEGAMAX×1.3/max(NOMEGA,40)`）——说明前两篇写 `0.1` 是照默认值，不是经验值。
3. ⚠️ **一处原文笔误**：「`CHGCAR`（将自洽计算目录下的 **`WAVECAR`** 复制到本目录下）」——括号里应为 **`CHGCAR`**（与库内另一篇 DOS 教程出现过的同一笔误相同）。
4. ⚠️ **一处前提补全**：原文提到 `OPTCELL` **需要改源码并重新编译 VASP**——这一条**上一轮 §36.8 漏了**，本库已补进 §36.9 与 `errors.md` §4.7（否则读者会以为随手写个 `OPTCELL` 就能固定真空层）。
5. 📌 **一处如实保留的未决**：**二维材料的吸收谱在带隙以下仍有吸收**——作者的归因（真空层被一起优化）**在他自己的对照实验中没有被证实**，本库按「未决」记录，并给出 4 条可优先排查的方向（见 §36.9 ⑤）。
6. 数据点：该 InSe 计算的吸收峰在 **3.7871 eV 与 4.0992 eV**，作者与文献对比「较为符合」。

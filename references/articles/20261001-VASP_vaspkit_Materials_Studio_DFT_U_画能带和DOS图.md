# VASP vaspkit Materials_Studio DFT+U 画能带和DOS图

- 来源: `https://zhuanlan.zhihu.com/p/579449491`
- 类型: html
- 来源: `https://zhuanlan.zhihu.com/p/579449491`（经知乎开放平台 CLI `me content --content-url` 读取，**本人文章**；`Data.Url` 与链接一致）
- 类型: html（zhihu-cli JSON → HTML 后收录；公式已内联，见 `zhihu_json_to_html.py`）
- 标签: 知乎, 本人文章, DFT+U, 能带, DOS, UO₂, vaspvis
- 作者注（本库注）：本文正文有若干笔误/待清理处，见文末「本库注」。
- 正文字数: 6811

---
如果计算步骤是：结构优化 \(\Rightarrow\) 静态自洽计算 \(\Rightarrow\) 非自洽计算；这么计算的结构会精确。

在本篇文章中，计算步骤是：结构优化 \(\Rightarrow\) 非自洽计算；这么计算是可以的，但是精确度不如上面。

结构优化过程中生成的 CHGCAR 和 WAVECAR 文件是对应于最后一步迭代的电荷密度和波函数，而不是对应于结构优化后的体系。结构优化后的体系可能与最后一步迭代的体系有微小的差别，导致电荷密度和波函数不完全一致。所以使用结构优化过程中生成的 CHGCAR 和 WAVECAR 文件进行计算的精确度比使用静态自洽计算生成的 CHGCAR 和 WAVECAR 文件进行计算的精确度有点差。

注：能带计算和 DOS 计算都是一种非自洽计算。

## 0 计算材料

\(\rm UO_{2}\) 是萤石结构的反铁磁绝缘体[1]，在 225 \(\rm Fm\verb|-|3m\) 空间群中结晶。晶格原胞包含一个铀原子和两个**氧**原子。（⚠️ 原文写作「氢原子」，系笔误——UO₂ 里是氧。）

铀原子的坐标为 \(\rm U(0,0,0)\) 。

氧原子坐标为 \(\rm O(0.25,0.25,0.25)\) , \(\rm O(0.75,0.75,0.75)\) [2]。

晶胞夹角为 \(\rm \alpha=\beta=\gamma=90^{\circ}\) 。

晶胞尺寸为 \(\rm a=b=c=5.468\mathring{A}\) 。

其晶体结构如下图所示：

## 1 结构弛豫

### POSCAR

1.打开 Materials Studio，新建文件

右击项目名称 \(\rightarrow\) New \(\rightarrow\) 3D Atomistic

2. 建立晶格

Build \(\rightarrow\) Crystals \(\rightarrow\) Build Crystal \(\rightarrow\) Enter group（输入空间群） \(\rightarrow\) Build

3. 添加原子

Build \(\rightarrow\) Add Atoms \(\rightarrow\) Element（选择元素种类） \(\rightarrow\) a b c（输入对应的晶格参数） \(\rightarrow\) Add

4. 将制作好的晶格保存为 cif 文件。然后用 VESTA 将文件转换为 VASP 的输入文件 POSCAR 的格式。

5. 将生成的 POSCAR 格式的文件拖入服务器对应的目录下。

### KPOINTS

在准备好 POSCAR 后，通过 vaspkit 生成 KPOINTS 文件。

在命令行依次输入下面命令：

vaspkit \(\rightarrow\) 1 \(\rightarrow\) 102 \(\rightarrow\) 2 \(\rightarrow\) 0.04

注：在这一步中，vaspkit 会自动生成 POTCAR。所以就不需要另外生成 POTCAR 了。

注：在选 K 点设置的方法中，vaspkit 有两种：Monkhorst-Pack Scheme 和 Gamma Scheme 。当设定各维度的 K 点数为奇数时，两种方法的撒点是一样的，且都包含 K 空间的 Gamma 点；为偶数时，MP 撒点不包含 Gamma 点，Gamma 撒点在 MP 撒点的基础上进行平移，保证采到 Gamma 点（根据自己的需要选取相应的撒点方式）。一般选 Gamma 点比较稳妥。

### INCAR

Global Parameters ISTART = 0 (Read existing wavefunction; if there) ISPIN = 2 (Non-Spin polarised DFT) MAGMOM = -1 1 -1 1 8*0 # ICHARG = 11 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 520 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) EDIFF = 1E-05 (SCF energy convergence, in eV) # LVTOT = .TRUE. (Write total electrostatic potential into LOCPOT or not) # LVHAR = .TRUE. (Write ionic + Hartree electrostatic potential into LOCPOT or not) # NELECT = (No. of electrons: charged cells; be careful) # LPLANE = .TRUE. (Real space distribution; supercells) # NPAR = 4 (Max is no. nodes; don't set for hybrids) # Nwrite = 2 (Medium-level output) # KPAR = 2 (Divides k-grid into separate groups) # NGX = 500 (FFT grid mesh density for nice charge/potential plots) # NGY = 500 (FFT grid mesh density for nice charge/potential plots) # NGZ = 500 (FFT grid mesh density for nice charge/potential plots) Lattice Relaxation NSW = 300 (number of ionic steps) ISMEAR = 0 (gaussian smearing method ) SIGMA = 0.05 (please check the width of the smearing) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 3 (optimize atomic coordinates and lattice parameters) EDIFFG = -1.5E-02 (Ionic convergence; eV/AA) PREC = Accurate (Precision level) #+U LDAU=.TRUE. LDAUTYPE=2 LMAXMIX=6 LDAUL=3 -1 LDAUU=3.70 0 LDAUJ=0.40 0

注：LDAUL，LDAUU 和 LDAUJ 这三个参数是一种元素对应一个参数。对应的元素顺序，我们需参考 POSCAR 的元素顺序。 \(\rm UO_{2}\) 的 DFT+U 计算主要考虑 \(\rm U\) 元素的5f轨道， \(\rm O\) 元素不考虑加 DFT+U ，所以 LDAUL 取 3 和 -1 。根据文献[2]， \(\rm U\) 元素电子库伦相互作用项取值为 3.70 ，交换相互作用项取值为 0.40 。既然 \(\rm O\) 元素不考虑 +U ,那对应位置的参数取值为 0 。

注：因为 \(\rm UO_{2}\) 材料是反铁磁材料，所以 MAGMOM 参数中 \(\rm U\) 元素的取值为-1，1 ，-1 ，1。

注：铀属于锕系元素, 有未填满的 5f 电子层并且具有磁性, 因此需要在计算中设置自旋极化 ISPIN = 2。

### 参数介绍

### LDAU = .TRUE. | .FALSE.

默认值是 .FALSE.

开启或者关闭 U 功能。

### LDAUTYPE = 1 | 2 | 4

默认值是 2

1： Liechtenstein 等人提出的旋转不变的 DFT+U ；

2：Dudarev 等人提出的 DFT+U 的简化（旋转不变）方法；

4：与 1 方法相同，但是没有交换分裂；

### LMAXMIX = [integer]

默认值是 2

加 U 计算时，该参数需大于轨道量子数。d 轨道应增加到 4 ，f 轨道应增加到 6 。

### LDAUL = [integer array]

默认值是 NTYP*2

-1：不加 U ；

1：对 p 轨道加 U ；

2：对 d 轨道加 U ；

3：对 f 轨道加 U ；

### LDAUU = [real array]

默认值是 NTYP*0.0

确定库仑相互作用的有效强度，及 U 值。

### LDAUJ = [real array]

默认值是 NTYP*0.0

确定交换相互作用的有效强度，及 J 值。

## 2 非自洽计算

将之前弛豫得到的 CONTCAR 、POTCAR 、CHGCAR 文件复制到一个新的文件夹中。当然，提交作业的脚本一般也要拷贝进去。然后复制 CONTCAR 为 POSCAR 。

### INCAR

Global Parameters ISTART = 1 (Read existing wavefunction; if there) ISPIN = 2 (Non-Spin polarised DFT) MAGMOM = -1 1 -1 1 8*0 # ICHARG = 11 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) ENCUT = 520 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) EDIFF = 1E-05 (SCF energy convergence, in eV) # LVTOT = .TRUE. (Write total electrostatic potential into LOCPOT or not) # LVHAR = .TRUE. (Write ionic + Hartree electrostatic potential into LOCPOT or not) # NELECT = (No. of electrons: charged cells; be careful) # LPLANE = .TRUE. (Real space distribution; supercells) # NPAR = 4 (Max is no. nodes; don't set for hybrids) # Nwrite = 2 (Medium-level output) # KPAR = 2 (Divides k-grid into separate groups) # NGX = 500 (FFT grid mesh density for nice charge/potential plots) # NGY = 500 (FFT grid mesh density for nice charge/potential plots) # NGZ = 500 (FFT grid mesh density for nice charge/potential plots) Lattice Relaxation NSW = 0 (number of ionic steps) ISMEAR = 0 (gaussian smearing method ) SIGMA = 0.05 (please check the width of the smearing) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 3 (optimize atomic coordinates and lattice parameters) EDIFFG = -1.5E-02 (Ionic convergence; eV/AA) PREC = Accurate (Precision level) #+U LDAU=.TRUE. LDAUTYPE=2 LMAXMIX=6 LDAUL=3 -1 LDAUU=3.70 0 LDAUJ=0.40 0 #DOS control NEDOS = 1001 LORBIT = 11

### KPOINTS

- 这时做静态计算的文件夹中必须有：INCAR、POTCAR、POSCAR、CHGCAR 和提交作业的脚本。

- 使用 vaspkit 生成 K 点路径，具体过程：vaspkit \(\rightarrow\) 3 \(\rightarrow\) 303（因为是三维结构）。

- 然后就会生成文件 KPATH . in 。

- 将 KPATH . in 复制为 KPOINTS。

- 通过脚本提交作业。

### 能带

- 脚本运行完后，开始生成能带数据，具体过程：vaspkit \(\rightarrow\) 21 \(\rightarrow\) 211。

- 然后将生成的文件 BAND.dat 移动到 Origin 中画图。

### DOS图

在本次计算中我们生成的是所有原子所有轨道总共的 DOS 图

vaspkit \(\rightarrow\) 11 \(\rightarrow\) 111

将得到的 tdot.dat 移动到 Origin 中画图。

我们也可以用python包来画图，这样更快更简单。下面是我用 python 包 vaspvis 画的能带图和 DOS 图与原文献数据的对比以及分析。

### 绘图并分析

文献结果

本次计算，能带的带隙为 1.8676eV ，文献[2]中结果为 1.95eV 。从以上两图可以看出，结果大致相同。

在 43.5 到 43.2 eV 之间, 主要为 U 的 6s 电子, 态密度曲线尖锐, 表明其原子态的轨道, 并未形成能带。

从态密度曲线可以看出, 价带主要是由 U 的 5f 和 O 的 2p 轨道组成, 而导带则由 U 的 6d 和 U 的 5f 轨道组成。

\(\rm UO_{2}\) 有两个价带，一个分布在 -20eV 附近，另一个分布在 -5eV 附近。

在 -20eV 附近的价带主要由 U 的 6p 轨道和 O 的 2s 轨道构成。

在 -5eV 附近的价带主要由O 的 2p, 以及少部分的 U 的 5f, 6d 轨道组成。

其中 O 的 2p 轨道态密度较高, 而且容易向 6d 和 5f 轨道进行跃迁。

成键情况：O 的 2p 轨道和 U 原子的 5f 部分轨道、6d 轨道有态密度共振, 表明有成键。

由于 U 原子 6d 轨道的带宽较宽, 所以态密度峰的跨度越大, 离域性越强, O 的 2p 与 U 的 6d 成键也就较强。

以上结果都和原文献[2]有较好的符合。

另外在我重复的文献[2]中有一个结论感觉挺重要的：

实验表明 \(\rm U_{eff}\) 值影响着 U 原子 5f 电子轨道的分布, 反过来, 也可以根据带隙宽度对 \(\rm U_{eff}\) 值进行修正。

如有错误，欢迎指正。

---

## 本库注（收录时补充，非原文内容）

1. **正文笔误**：「原胞包含一个铀原子和两个**氢**原子」——应为**氧**原子（已在正文订正）。
2. **同一个 INCAR 里 `PREC` 出现两次**（先 `Normal`、后 `Accurate`）：**建议只留一个**，不要依赖「后出现者生效」这类不确定行为（详见 `errors.md` §七）。
3. **非自洽步的 `ICHARG` 是注释掉的**（用默认值），而拷贝清单里只有 `CHGCAR`、没有 `WAVECAR`：
   若发现**费米能或能带与自洽步对不上**，先确认这一步是否真的读进了上一步的电荷密度，必要时**显式写 `ICHARG = 1`（读 `CHGCAR`）或 `11`（读并固定）**。
4. **`tdot.dat` 应为 `tdos.dat`**（`vaspkit 11 111` 的产物）。
5. **U/J 值有出处**（文献 U = 3.70 eV、J = 0.40 eV）——这一点很值得保留：**U 值不能随手设**。

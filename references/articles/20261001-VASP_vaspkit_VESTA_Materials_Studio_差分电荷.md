# VASP vaspkit VESTA Materials_Studio 差分电荷

- 来源: `https://zhuanlan.zhihu.com/p/576368649`
- 类型: html
- 标签: 知乎, 本人文章, 差分电荷, VASPKIT, VESTA, Materials Studio
- ⚠️ 抓取说明：本文正文里的 INCAR 等代码块来自网页高亮组件，**换行与空格在抓取时被压扁**（参数挤成一行），阅读时需自行断句，不要直接复制。
- 正文字数: 5893

---
## 0 计算材料

是金刚石结构，在四方 空间群中结晶。 与六个等效 原子键合，形成八面体。 键有两种键长，四个较短的键长 和两个较长的键长 。

## 1 结构弛豫

### POSCAR

1. POSCAR从网站 [The Materials Project](https://materialsproject.org/) 上下载 的cif文件（如下图所示）。

2. 将相应的 cif 文件拖入 Materials Studio 中，并进行下面相关步骤：

- Build Surfaces Cleave Surface（建立表面）。Cleave plane(h k l)（晶面方向）取 110 。Position 是取层数的一些相关参数，在这里我们取八层，最上面一层为二配位 原子。

- Build Crystals Build Vacuum Slab...（建立真空层）。Vacuum thickness 取 。

- 在最上面一层的氧原子上沿着 z 方向吸附上 C，然后在 C 原子上沿着 z 方向添加一个 O 原子（如下图所示）。

- File Export... 保存类型(T) Crystallographic Information Files(.cif;*.cmf)（保存为 cif 格式）

注：上面步骤必须按照顺序执行。

3. 将保存的cif文件用VESTA打开，然后按照下面顺序：

File Export Data... 保存类型(T) VASP (POSCAR;*.vasp)

将文件保存为 VASP 的 POSCAR 输入格式。

4. 将文件导入服务器中，并将文件名改为 POSCAR 。

5. 使用 vaspkit 将文件的最下面两层固定住。

老版 vaspkit ：

vaspkit 4 402 1（选择POSCAR为输入） 1（选择层数为固定标准） 0.9（设定原子之间距离的阈值，从而判断层数。根据列出的参考,选择 (8层)） 2 （选择固定下面多少层）

新版 vaspkit ：

vaspkit 4 402 1（选择POSCAR为输入） 2（选择层数为固定标准） 0.06 （设定原子之间距离的阈值，从而判断层数。根据列出的参考,选择( 8 层)） 1 2（选择固定的层数，本次选 1 层和 2 层） all （选择固定的方向，这里选择所有方向）

注：新版和老版选择层数的方式可能不一样。老版只有一种选择方式（从下往上），我们只要输入层数就好。新版可以一层一层的选，也可以连续的选（不一定非从下往上）。

注：在选择原子间距离的阈值时，vaspkit 会给出参考（如下图所示）：

6. 将生成的 POSCAR_FIX 文件文件名改为 POSCAR 。

### KPOINTS

在准备好 POSCAR 后，通过 vaspkit 生成 KPOINTS 文件。

在命令行依次输入下面命令：

vaspkit 1 102 2 0.04

注：在这一步中，vaspkit 会自动生成 POTCAR 。所以就不需要另外生成 POTCAR 了。

注：在选 K 点设置的方法中，vaspkit 有两种：Monkhorst-Pack Scheme 和 Gamma Scheme 。当设定各维度的 K 点数为奇数时，两种方法的撒点是一样的，且都包含 K 空间的 Gamma 点；为偶数时，MP 撒点不包含 Gamma 点，Gamma 撒点在 MP 撒点的基础上进行平移，保证采到 Gamma 点（根据自己的需要选取相应的撒点方式）。一般选 Gamma 点比较稳妥。

### INCAR

用 vaspkit 生成 INCAR 文件。

vaspkit 1 101 LR

注：为了取得有意义的结果，需要满足 INCAR 中的 ENCUT 大于 POTCAR 中的所有元素的 ENMAX 。我们可以通过下面命令查看

grep ENMAX POTCAR

我们发现，在本次计算中 ENMAX 最大值为 400（如下图所示）

所以 ENCUT 的是可设可不设。在不设置的时候，程序会自动将 ENCUT 设为 ENMAX 的最大值 。

INCAR 具体内容如下：

Global Parameters ISTART = 1 (Read existing wavefunction; if there) ISPIN = 1 (Non-Spin polarised DFT) # ICHARG = 11 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) # ENCUT = 400 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) # LVTOT = .TRUE. (Write total electrostatic potential into LOCPOT or not) # LVHAR = .TRUE. (Write ionic + Hartree electrostatic potential into LOCPOT or not) # NELECT = (No. of electrons: charged cells; be careful) # LPLANE = .TRUE. (Real space distribution; supercells) # NPAR = 4 (Max is no. nodes; don't set for hybrids) # Nwrite = 2 (Medium-level output) # KPAR = 2 (Divides k-grid into separate groups) # NGX = 500 (FFT grid mesh density for nice charge/potential plots) # NGY = 500 (FFT grid mesh density for nice charge/potential plots) # NGZ = 500 (FFT grid mesh density for nice charge/potential plots) Lattice Relaxation NSW = 300 (number of ionic steps) ISMEAR = 0 (gaussian smearing method ) SIGMA = 0.05 (please check the width of the smearing) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 3 (optimize atomic coordinates and lattice parameters) EDIFFG = -1.5E-02 (Ionic convergence; eV/AA) PREC = Accurate (Precision level)

## 2 静态计算

注：计算时，相应的 AB、A 和 B 要分别放在同样大小的空间格子中并保证 A 和 B 与 AB 中相应坐标不变。

注：在结构弛豫的时候，我选择 LCHARG = .TRUE. ，则在弛豫完成后，会自动生成 AB 的 CHGCAR 。之后，我们只需要生成 A 和 B 的 CHGCAR 就可以了。

注：在计算差分电荷时需要保持三次自洽计算所采用的 NGX，NGY，NGZ 一致，所以在结构弛豫完成并生成 CHGCAR 后，我们需要在当前目录下的命令行输入 grep NGX OUTCAR ，来检查 NGX，NGY，NGZ 为多少。之后再 A 和 B 的 INCAR 中，我们只要将 NGX，NGY，NGZ 设成相同的数值就可以了。

### KPOINTS

KPOINTS 和提交脚本都从结构弛豫的目录中复制。

### POSCAR

生成 A、B 的 POSCAR 的步骤。

- 结构弛豫的 CONTCAR 放在 VESTA 中，然后在 VESTA 中将文件转为 cif 格式。

- 在 Materials Studio 中，将 cif 格式的文件打开，删去想要删去的原子，并将处理后的文件保存为 cif 格式。

- 将处理后的 cif 格式的文件用 VESTA 转化为 VASP 的输入文件 POSCAR 的格式。

- 将 POSCAR 格式的文件放入服务器提交目录中，并重命名为 POSCAR 。

注：在 VESTA 中好像不能删去原子的位置，因为我发现虽然视图中删去了，但保存的文件还是原来的样子。有更好方法的小伙伴，可以直接告诉我。

### POTCAR

POTCAR 通过 vaspkit 生成：

vaspkit 1 103

### INCAR

注：计算时，要保证三次自洽计算所采用的 NGX，NGY，NGZ 一致。

注：计算时，要保证 LCHARG = .TRUE. ，也就是会生成 CHGCAR 文件。

Global Parameters ISTART = 1 (Read existing wavefunction; if there) ISPIN = 1 (Non-Spin polarised DFT) # ICHARG = 11 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) # ENCUT = 400 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) # LVTOT = .TRUE. (Write total electrostatic potential into LOCPOT or not) # LVHAR = .TRUE. (Write ionic + Hartree electrostatic potential into LOCPOT or not) # NELECT = (No. of electrons: charged cells; be careful) # LPLANE = .TRUE. (Real space distribution; supercells) # NPAR = 4 (Max is no. nodes; don't set for hybrids) # Nwrite = 2 (Medium-level output) # KPAR = 2 (Divides k-grid into separate groups) NGX = 16 (FFT grid mesh density for nice charge/potential plots) NGY = 32 (FFT grid mesh density for nice charge/potential plots) NGZ = 90 (FFT grid mesh density for nice charge/potential plots) Lattice Relaxation NSW = 0 (number of ionic steps) ISMEAR = 0 (gaussian smearing method ) SIGMA = 0.05 (please check the width of the smearing) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 3 (optimize atomic coordinates and lattice parameters) EDIFFG = -1.5E-02 (Ionic convergence; eV/AA) PREC = Accurate (Precision level)

## 3 差分电荷

在静态计算完成后，我们会得到 AB、A 和 B 的 CHGCAR 。

1.用 vaspkit 进行差分电荷：

vaspkit 31 314

在之后的界面依次输入 AB、A 和 B 的 CHGCAR 路径（用空格隔开）。

2. 将生成的 CHGDIFF.vasp 拖入到 VESTA 中（如下图所示）

默认青色部分电荷减小，黄色部分电荷增加。

3. 查看差分电荷的二维图

操作前先选中三个原子（建议选吸附的 CO 分子和一个临近的原子），然后再进行如下操作：

Utilities 2D Data Display... Slice... Calculate the best plane for the selected atoms OK

生成差分电荷的二维图:

4. 查看 z 方向的平均差分电荷密度的变化

将 CHGDIFF.vasp 文件重新命名为 CHGCAR ，然后使用 vaspkit ：

vaspkit 31 316 1（选择 CHGCAR 为读取形式） 3（选择 z 方向）

最后将生成的文件 PLANAR_AVERAGE.dat 拖到 Origin 去作图（结果如下）：

如有错误，欢迎指正。

# VASP vaspkit VESTA 电荷密度分布

- 来源: `https://zhuanlan.zhihu.com/p/576256133`
- 类型: html
- 标签: 知乎, 本人文章, 电荷密度, VESTA, VASPKIT, 可视化
- ⚠️ 抓取说明：本文 INCAR 等代码块来自网页高亮组件，**换行与空格在抓取时被压扁**（参数挤成一行），阅读时需自行断句，不要直接复制。
- 正文字数: 3708

---
## 0 计算材料

计算电荷密度分布的材料是： 和 。

材料： 为金刚石结构，在立方 空间群中结晶。 与四个等效 原子键合，形成共角四面体。 键长度均为 。

材料： 为立方结构，在 空间群中结晶。 与六个 形成八面体。晶体中，所有键的键长为： 。

## 1 结构弛豫

### POSCAR

POSCAR 内容可以直接从网站 [The Materials Project](https://materialsproject.org/) 上下载（如下图所示）。

### KPOINTS

在准备好 POSCAR 后，通过 vaspkit 生成 KPOINTS 文件。

在命令行依次输入下面命令：

vaspkit 1 102 2 0.03

注：在这一步中，vaspkit 会自动生成 POTCAR 。所以就不需要另外生成 POTCAR 了。

注：在选 K 点设置的方法中，vaspkit 有两种：Monkhorst-Pack Scheme 和 Gamma Scheme 。当设定各维度的 K 点数为奇数时，两种方法的撒点是一样的，且都包含 K 空间的 Gamma 点；为偶数时，MP 撒点不包含Gamma 点，Gamma 撒点在 MP 撒点的基础上进行平移，保证采到 Gamma 点（根据自己的需要选取相应的撒点方式）。一般选 Gamma 点比较稳妥。

### INCAR

用 vaspkit 生成 INCAR 文件。

vaspkit 1 101 LR

Global Parameters ISTART = 1 (Read existing wavefunction; if there) ISPIN = 1 (Non-Spin polarised DFT) # ICHARG = 11 (Non-self-consistent: GGA/LDA band structures) LREAL = .FALSE. (Projection operators: automatic) # ENCUT = 400 (Cut-off energy for plane wave basis set, in eV) PREC = Normal (Precision level) LWAVE = .TRUE. (Write WAVECAR or not) LCHARG = .TRUE. (Write CHGCAR or not) ADDGRID= .TRUE. (Increase grid; helps GGA convergence) # LVTOT = .TRUE. (Write total electrostatic potential into LOCPOT or not) # LVHAR = .TRUE. (Write ionic + Hartree electrostatic potential into LOCPOT or not) # NELECT = (No. of electrons: charged cells; be careful) # LPLANE = .TRUE. (Real space distribution; supercells) # NPAR = 4 (Max is no. nodes; don't set for hybrids) # Nwrite = 2 (Medium-level output) # KPAR = 2 (Divides k-grid into separate groups) # NGX = 500 (FFT grid mesh density for nice charge/potential plots) # NGY = 500 (FFT grid mesh density for nice charge/potential plots) # NGZ = 500 (FFT grid mesh density for nice charge/potential plots) Lattice Relaxation NSW = 300 (number of ionic steps) ISMEAR = 0 (gaussian smearing method ) SIGMA = 0.05 (please check the width of the smearing) IBRION = 2 (Algorithm: 0-MD; 1-Quasi-New; 2-CG) ISIF = 3 (optimize atomic coordinates and lattice parameters) EDIFFG = -1.5E-02 (Ionic convergence; eV/AA) PREC = Accurate (Precision level)

注：在计算 和 材料的时候，vaspkit 直接生成的文件一般够用。

注：在进行弛豫计算的时候，我们一般要保证弛豫是在一个离子步内算完。因为在弛豫过程中，晶格的大小和基组可能会改变，一个离子步算完更精确。

在第一次弛豫的时候，我们往往难以一个离子步收敛，所以我们需要将 CONTCAR 复制成 POSCAR 再次进行弛豫，直到一个离子步内收敛。

注：金属体系结构弛豫的时候，不能使用 ISMEAR =-5 ，应为 ISMEAR 0。

注：在进行结构弛豫的时候，我们把参数 LCHARG = .TRUE. ，这样在结束结构弛豫的时候，直接输出 CHGCAR文件。

## 2 VESTA

将生成的 CHGCAR 文件拖入 VESTA，结果如下：

可以发现， 的共价键中，电荷主要分布在原子之间。

材料的电子分布可能由于模型中原子尺寸画的太大，所有无法看清。

### 更改原子展示尺寸

我们可以通过以下步骤缩小原子尺寸：

Objects Properties Automs... Radius and color

也可以在界面左下侧直接找到 Properties 按钮。

在 Radius and color 中（如下图所示）：

左边选择原子种类,右边选择原子的半径。下面选择原子的颜色。

之后根据具体情况改小，然后点击 OK 按钮就可以了。

在更改了原子的展示尺寸后，我们可以很清晰的看到 NaCl 晶体的电荷分布：

NaCl晶体

电荷主要分布在 Na 原子一侧（就像电子从一个原子转移到另一个原子）。

### 二维电荷密度图

在 VESTA 画电荷密度图有两种方法。

方法一：

Edit Lattice Planes... Add lattice planes

之后，我们可以通过修改 Miller indices （hkl）（米勒指数）来建立二维电荷密度图。

也可以通过选中三个原子，然后再点击按钮 Calculate the best plane for the selected atoms 来建立二维电荷密度图。

上图为两种途径建立的二维电荷密度图。

方法二：

Utilities 2D Data Display... Slice

然后手动选择三个原子，之后再点击按钮 Calculate the best plane for the selected atoms，最后点击 OK 。

Si选中的三个原子以及2D电荷密度图NaCl选中的三个原子以及2D电荷密度图

画等高线：2D Data Display 页面中，Contours 栏下，选择 Draw contour lines 和 Logarithmic 。

如果将电荷的密度变成一个维度，那么我们可以画一个三维图。画三维图也很简单，只需要在画好上面二维图后，在 2D Data Display 页面中，General 栏下，勾选 Bird's-eye view ，我们就可以看见相应的三维图了。

左为Si,右为NaCl

问题1 有的朋友的电荷密度分布可能和我画的不一样的原因。

他们的结果可能如下：

如果你画出的是上述结果，不同的原因应该不是 INCAR 参数设置的问题。

不同的原因是 POTCAR 的不同。

当 POTCAR 中情况如下：

也就是有 7 个电子的时候，你的结果可能和我相同。

当 POTCAR 中情况如下：

也就是有 1 个电子的时候，你的结果可能和我不相同，和我上述图片相同。

问题2 CHGCAR 出现负值可能的原因。

我们以 的 CHGCAR 为例：

在红框中，我们发现最蓝色哪一部分是负值。

在图片中，我们可以看到蓝色搜集中在原子核的位置，所以我们猜测，电荷密度的负值代表正电荷的位置，因为电子带负电，原子核带正电。

我们以 的 CHGCAR 为例：

最蓝色的那一部分不是负的，所以除了原子核的其他位置也可能是蓝色的。

以上是关于问题 2 的原因的猜想。

如有错误，欢迎指正。

# 画能带（Band）和态密度（DOS）图--Python包

- 来源: `https://zhuanlan.zhihu.com/p/580857656`
- 类型: html
- 来源: `https://zhuanlan.zhihu.com/p/580857656`（经知乎开放平台 CLI `me content --content-url` 读取，**本人文章**；`Data.Url` 与链接一致）
- 类型: html（zhihu-cli JSON → HTML 后收录）
- 标签: 知乎, 本人文章, 能带, DOS, vaspvis, pymatgen
- ⚠️ 抓取说明：正文的 Python 代码在导出时**被压成单行（连空格一起丢）**，本库已按 Python 语法逐段重排（逻辑与参数值未改）；文末附「本库注」。
- 正文字数: 5373

---
## Python包

本篇文章主要介绍两个 Python 包：vaspvis 和 pymatgen。它们都可以独立的画能带和态密度，并且可以把这两张图画一起。

我使用的环境是：centos下的 anaconda 的 jupyter notebook。

注：这两个包都是 vasp 输出结果的处理软件。

## vaspvis

注：在画图时，必须确保相应的目录下有 EIGENVAL、PROCAR、KPOINTS、POSCAR 和 INCAR 文件。

### 下载方式

在 [PyPI](https://pypi.org/) 上，直接搜索 vaspvis 就可以直接搜索到相应的 python 包。

在连网的情况下，可以直接使用下面命令下载：

pip install vaspvis

### 说明书

vaspvis 有一个专门的说明书来解释这个包的所有内容，地址如下：

[Welcome to vaspvis’s documentation!](https://vaspvis.readthedocs.io/en/latest/index.html)

我们可以通这个网站来了解这个包具体怎么用。

### github

在 github 上，vaspvis 的作者提供代码的地址为：

[https://github.com/DerekDardzinski/vaspvis](https://github.com/DerekDardzinski/vaspvis)

如果对 vaspvis 有什么问题的话，我们可以直接在 github 的 Issues 栏对作者提出相关问题。我们也可以在这里看看其他使用者的问题，看看有没有问已经问过，并且作者已经回答过了。

### 示例1

画总的能带图

```python
from vaspvis import standard

band_folder = '../a'   # 自己 vasp 输出文件所处目录的位置
dos_folder  = '../a'

standard.band_plain(
    folder=band_folder,   # 输入读入数据的路径
    figsize=(5.5, 3),     # 设计图片的长宽比例
    save=True             # 将数据保存为 band_plain.png
)
```

注：如果x轴要有希腊字符，需要把 KPOINTS 文件中的 GAMMA 改为 \Gamma。

结果：

### 示例2

自旋向上和自旋向下分别显示

```python
standard.band_plain_spin_polarized(
    folder=band_folder,
    figsize=(6, 3),
)
```

结果：

### 示例3

每种元素分别显示

```python
standard.band_elements(
    folder=band_folder,
    elements=['U', 'O'],
    figsize=(6, 3),
    save=True
)
```

结果：

### 示例4

画每个轨道以及总的 DOS 图

```python
standard.dos_orbitals_spin_polarized(
    folder=dos_folder,
    orbitals=[0, 1, 2, 3, 4, 5, 6, 7, 8],
    energyaxis='x',
)
```

结果：

### 示例5

指定原子的 DOS 图

```python
standard.dos_elements_spin_polarized(
    folder=dos_folder,
    elements=['U', 'O'],
    energyaxis='x',
)
```

```python
standard.dos_elements_spin_polarized(
    folder=dos_folder,
    elements=['U'],
    energyaxis='x',
)
```

### 示例6

画指定原子的 DOS 图

```python
standard.dos_atom_orbitals_spin_polarized(
    folder=dos_folder,
    atom_orbital_dict={0: [1, 3], 1: [1, 7]},
    energyaxis='x',
    total=False
)
```

### 示例7

Band 和 DOS 画一起

```python
standard.band_dos_plain_spin_polarized(
    band_folder=band_folder,
    dos_folder=dos_folder,
    save=True
)
```

结果：

### 示例8

能带和 DOS 画一起，并显示处每个轨道。

```python
standard.band_dos_orbitals_spin_polarized(
    band_folder=band_folder,
    dos_folder=dos_folder,
    orbitals=[0, 1, 2, 3, 4, 5, 6, 7, 8],
    save=True
)
```

注：问什么会画两张图呢？因为颜色对应的是轨道那个维度。自旋向上和向下又是另一个维度，所以只能用两张图片显示了。

结果：

vaspvis 还有更多功能，github上有作者更多的示例。

## pymatgen

注：使用 pymatgen 画图的时候只要保证文件夹下有 vasprun.xml 就可以了。

### 下载方式

在 [PyPI](https://pypi.org/) 上，直接搜索pymatgen就可以直接搜索到相应的 python 包。

在连网的情况下，可以直接使用下面命令下载（最好使用 anaconda ）：

pip install pymatgen

### 说明书

pymatgen 有一个专门的说明书来解释这个包的所有内容，地址如下：

[https://pymatgen.org/index.html](https://pymatgen.org/index.html)

注：里面有 pymatgen 包的详细解释，以及详细的安装下载过程。

### github

在 github上，pymatgen 的作者提供代码的地址为：

[https://github.com/materialsproject/pymatgen](https://github.com/materialsproject/pymatgen)

如果对 pymatgen 有什么问题的话，我们可以直接在 github 的 Issues 栏对作者提出相关问题。我们也可以在这里看看其他使用者的问题，看看有没有问已经问过，并且作者已经回答过了。

### 示例1

画 DOS 图的 spdf 轨道投影

```python
from pymatgen.io.vasp import Vasprun
from pymatgen.electronic_structure.plotter import DosPlotter
import matplotlib.pyplot as plt

v = Vasprun('./vasprun.xml')
cdos = v.complete_dos
dos = cdos.get_spd_dos()
plotter = DosPlotter()
plotter.add_dos_dict(dos)
plotter.show(xlim=[-10, 5], ylim=[-25, 25])
plt.savefig('uo2_spd_dos.png')
```

结果：

### 示例2

画 DOS 的元素投影

```python
from pymatgen.io.vasp import Vasprun
from pymatgen.electronic_structure.plotter import DosPlotter
import matplotlib.pyplot as plt

v = Vasprun('./vasprun.xml')
cdos = v.complete_dos
dos = cdos.get_element_dos()
plotter = DosPlotter()
plotter.add_dos_dict(dos)
plotter.get_plot(xlim=[-10, 5], ylim=[-25, 25])
plt.savefig('uo2_element_dos.png')
```

结果：

### 示例3

画每个元素对应的某个轨道的 DOS 图

```python
import matplotlib.pyplot as plt
from pymatgen.electronic_structure.core import OrbitalType
from pymatgen.electronic_structure.plotter import DosPlotter
from pymatgen.io.vasp.outputs import Vasprun

# load data
result = Vasprun('./vasprun.xml', parse_potcar_file=False)
complete_dos = result.complete_dos
pdos_U = complete_dos.get_element_spd_dos('U')
pdos_O = complete_dos.get_element_spd_dos('O')

plotter = DosPlotter()
plotter.add_dos('Total DOS', result.tdos)
plotter.add_dos('U(f)', pdos_U[OrbitalType.f])
plotter.add_dos('O(s)', pdos_O[OrbitalType.s])
plotter.add_dos('O(p)', pdos_O[OrbitalType.p])
plotter.get_plot(xlim=(-10, 5), ylim=(-25, 25))
plt.savefig('uo2_dos.png')
```

结果：

### 示例4

将能带和 DOS 画一起

```python
import matplotlib.pyplot as plt
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.plotter import BSDOSPlotter, BSPlotter, BSPlotterProjected, DosPlotter

# read vasprun.xml，get band and dos information
bs_vasprun = Vasprun("./vasprun.xml", parse_projected_eigen=True)
bs_data = bs_vasprun.get_band_structure(line_mode=True)
dos_vasprun = Vasprun("./vasprun.xml")
dos_data = dos_vasprun.complete_dos

# set figure parameters, draw figure
banddos_fig = BSDOSPlotter(bs_projection=None, dos_projection=None,
                           vb_energy_range=5, fixed_cb_energy=5, fig_size=(16, 12))
banddos_fig.get_plot(bs=bs_data, dos=dos_data)
plt.savefig('banddos_fig.png')
```

结果：

### 示例5

将能带和 DOS 画一起，并显示各个元素。

```python
import matplotlib.pyplot as plt
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.plotter import BSDOSPlotter, BSPlotter, BSPlotterProjected, DosPlotter

dos_vasprun = Vasprun("./vasprun.xml")
dos_data = dos_vasprun.complete_dos
bs_vasprun = Vasprun("./vasprun.xml", parse_projected_eigen=True)
bs_data = bs_vasprun.get_band_structure(line_mode=1)

plt_1 = BSDOSPlotter(bs_projection="elements", dos_projection="elements", fig_size=(16, 12))
plt_1.get_plot(bs=bs_data, dos=dos_data)
plt.savefig('plt_1.png')
```

结果：

注：如果 x 轴要有希腊字符，需要把 KPOINTS 文件中的 GAMMA 改为 \Gamma（一定要同时都改为\Gamma）。如果只改了几个的话，所有的就不会显示希腊字符。

注：pymatgen 还有很多其他的功能，详情我们可以看看说明书。

如有错误，欢迎指出。

---

## 本库注（收录时补充，非原文内容）

1. ⭐ **两个包对输入文件的要求不同**（这是选包时的第一条判据）：
   - **`vaspvis` 需要 `EIGENVAL`、`PROCAR`、`KPOINTS`、`POSCAR`、`INCAR` 五个文件**都在同一目录下；
   - **`pymatgen` 只要 `vasprun.xml`**。
2. ⭐ **希腊字母必须是「全改或全不改」**：想让能带横轴显示 `Γ`，要把 `KPOINTS` 里的 `GAMMA` **全部同时改成 `\Gamma`**；只改一部分的话，**一个都不会显示**（原文两处强调，已提炼进 `workflows.md` 第三节）。
3. **`pymatgen` 画联合图/投影图时**，读 `vasprun.xml` 要带 **`parse_projected_eigen=True`**；价带/导带在图上留多少范围由 `vb_energy_range` 与 `fixed_cb_energy` 控制。
4. **`vaspvis` 的 `band_dos_orbitals_spin_polarized` 会出两张图**：颜色维度是「轨道」、自旋是另一个维度，只能分成上下自旋两张。
5. 本文所有示例图均为 UO₂（与库内 DFT+U 那篇同一材料）——**同一体系可用三条不同路线出图**（Origin、pymatgen、vaspvis），可按需要对照。

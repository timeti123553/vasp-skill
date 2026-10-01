# VASP vaspkit Python 画态密度（DOS）图

- 来源: `https://zhuanlan.zhihu.com/p/621750993`（经知乎开放平台 CLI `me content --content-url` 读取，**本人文章**；`Data.Url` 与链接一致）
- 类型: html（zhihu-cli JSON → HTML 后收录）
- 标签: 知乎, 本人文章, DOS, pymatgen, vaspkit
- ⚠️ 抓取说明：知乎正文的 **LaTeX 公式是图片**，导出后丢失（已由本库按原文补齐并标注）；**代码块/INCAR/KPOINTS 在导出时被压成单行**（换行缩进全丢），本库已按 shell/Python 语法重新排版。

---
本篇文章的步骤是：结构优化静态自洽计算DOS 计算

本篇文章使用的画能带的 Python 包是 pymatgen 。

## 0 计算材料

Materials Project 网站上材料的代号：mp-5951

> ⚠️ **本段公式在导出时丢失，以下由本库根据原文（知乎正文的 LaTeX 图片）补齐**；
> 其余文字未改动。

**CeMnNi₄** 是六角晶系 Laves 的衍生结构，在立方 **F̄43m** 空间群中结晶。

**Ce** 以 16 配位的几何结构与四个等价的 **Mn** 和十二个等价的 **Ni** 原子结合。

所有 **Ce–Mn** 键长均为 **3.00 Å**。

所有 **Ce–Ni** 键长均为 **2.88 Å**。

**Mn** 以 16 配位的几何结构与四个等效的 **Ce** 原子和十二个等效的 **Ni** 原子结合。

所有 **Mn–Ni** 键长均为 **2.87 Å**。

**Ni** 与三个等价的 **Ce**、三个等价的 **Mn** 和六个等价的 **Ni** 原子键合，
形成面、边和角共享 **NiCe₃Mn₃Ni₆** 立方八面体的混合物。

该物质中有三个较短的 ( **2.43 Å** ) 和三个较长的 ( **2.48 Å** ) **Ni–Ni** 键长。

## 1 结构优化

需要准备的文件：

- INCAR（vaspkit 生成再修改）

- POTCAR（vaspkit 生成）

- KPOINTS（vaspkit 生成）

- POSCAR（从 Materials Project 或其他数据库获取）

- 作业提交脚本

注：本文使用的 POTCAR 是 PBE 泛函。

注：若算磁性材料的时候没有出现磁性，我们可以在 INCAR 中加上 NUPDOWN 参数。NUPDOWN 所对应的数值是结构所对应的总磁矩（计算磁性材料基态的时候，一般不使用此参数）。

注：如果我们计算的是磁性材料，我们可以在INCAR中加入参数 LORBIT=11。计算完成后，我们可以在OUTCAR 中的 magnetization (x) 中查看每个原子所对应的磁矩。

### INCAR

Global Parameters
ISTART =  0            (Read existing wavefunction; if there)
ISPIN  =  2            (Spin polarised DFT)
MAGMOM = 4*0.5 4*6 16*0.5
LORBIT = 11
# NUPDOWN = 19.6936
# ICHARG =  11         (Non-self-consistent: GGA/LDA band structures)
LREAL  = .FALSE.       (Projection operators: automatic)
ENCUT  =  400          (Cut-off energy for plane wave basis set, in eV)
PREC   =  Normal       (Precision level)
LWAVE  = .FALSE.       (Write WAVECAR or not)
LCHARG = .FALSE.       (Write CHGCAR or not)
ADDGRID= .TRUE.        (Increase grid; helps GGA convergence)
NPAR   = 4             (Max is no. nodes; don't set for hybrids)

Electronic Relaxation
ISMEAR =  0            (Gaussian smearing; metals:1)
SIGMA  =  0.05         (Smearing value in eV; metals:0.2)
NELM   =  90           (Max electronic SCF steps)
NELMIN =  6            (Min electronic SCF steps)
EDIFF  =  1E-06        (SCF energy convergence; in eV)
# GGA  =  PS           (PBEsol exchange-correlation)

Ionic Relaxation
NSW    =  100          (Max ionic steps)
IBRION =  2            (Algorithm: 0-MD; 1-Quasi-New; 2-CG)
ISIF   =  2            (Stress/relaxation: 2-Ions, 3-Shape/Ions/V, 4-Shape/Ions)
EDIFFG = -2E-02        (Ionic convergence; eV/AA)
# ISYM =  2            (Symmetry: 0=none; 2=GGA; 3=hybrids)

### KPOINTS

```
KPT-Resolved Value to Generate K-Mesh: 0.030
0
Monkhorst-Pack
   5   5   5
0.0  0.0  0.0
```

## 2 静态自洽计算

需要准备的文件：

- INCAR（vaspkit 生成之后再修改，或者把结构优化的 INCAR 的内容修改一些）

- POTCAR（vaspkit 生成，或者把结构优化目录下的 POTCAR 粘贴到本目录下）

- KPOINTS（vaspkit 生成，或者自己写）

- POSCAR（将结构优化下的 CONTCAR 复制为本目录下的 POSCAR ）

- 作业提交脚本

### INCAR

Global Parameters
ISTART =  0            (Read existing wavefunction; if there)
ISPIN  =  2            (Spin polarised DFT)
MAGMOM = 4*0.5 4*6 16*0.5
LORBIT = 11
# ICHARG =  11         (Non-self-consistent: GGA/LDA band structures)
LREAL  = .FALSE.       (Projection operators: automatic)
ENCUT  =  400          (Cut-off energy for plane wave basis set, in eV)
PREC   =  Normal       (Precision level)
LWAVE  = .TRUE.        (Write WAVECAR or not)
LCHARG = .TRUE.        (Write CHGCAR or not)
ADDGRID= .TRUE.        (Increase grid; helps GGA convergence)
NPAR   = 4             (Max is no. nodes; don't set for hybrids)

Electronic Relaxation
ISMEAR =  -5           (Gaussian smearing; metals:1)
SIGMA  =  0.05         (Smearing value in eV; metals:0.2)
NELM   =  90           (Max electronic SCF steps)
NELMIN =  6            (Min electronic SCF steps)
EDIFF  =  1E-06        (SCF energy convergence; in eV)
# GGA  =  PS           (PBEsol exchange-correlation)

Ionic Relaxation
NSW    =  0            (Max ionic steps)
IBRION =  2            (Algorithm: 0-MD; 1-Quasi-New; 2-CG)
ISIF   =  2            (Stress/relaxation: 2-Ions, 3-Shape/Ions/V, 4-Shape/Ions)
EDIFFG = -2E-02        (Ionic convergence; eV/AA)
# ISYM =  2            (Symmetry: 0=none; 2=GGA; 3=hybrids)

### KPOINTS

```
KPT-Resolved Value to Generate K-Mesh: 0.030
0
Monkhorst-Pack
   5   5   5
0.0  0.0  0.0
```

## 3 态密度计算

需要准备的文件：

- INCAR（vaspkit 生成之后再修改，或者把结构优化的 INCAR 的内容修改一些）

- POTCAR（vaspkit 生成，或者把结构优化目录下的 POTCAR 粘贴到本目录下）

- KPOINTS（vaspkit 生成，或者自己写）

- POSCAR（将结构优化下的 CONTCAR 复制为本目录下的 POSCAR ）

- WAVECAR（将自洽计算目录下的 WAVECAR 复制到本目录下）

- CHGCAR（将自洽计算目录下的 **CHGCAR** 复制到本目录下）　⚠️ 原文此处写成 WAVECAR，系笔误——需要拷贝的是 `WAVECAR` 与 `CHGCAR` 两个文件。

- 作业提交脚本

注：在进行 DOS 计算的时候，ISMEAR = -5。

注：如果觉得 DOS 图取得点比较少，我们可以通增加参数 NEDOS 的赋值来增加。

### INCAR

Global Parameters
ISTART =  1            (Read existing wavefunction; if there)
ISPIN  =  2            (Spin polarised DFT)
MAGMOM = 4*0.5 4*6 16*0.5
LORBIT = 11
ICHARG =  11           (Non-self-consistent: GGA/LDA band structures)
LREAL  = .FALSE.       (Projection operators: automatic)
ENCUT  =  400          (Cut-off energy for plane wave basis set, in eV)
PREC   =  Normal       (Precision level)
LWAVE  = .FALSE.       (Write WAVECAR or not)
LCHARG = .FALSE.       (Write CHGCAR or not)
ADDGRID= .TRUE.        (Increase grid; helps GGA convergence)
NPAR   =  4            (Max is no. nodes; don't set for hybrids)

Electronic Relaxation
ISMEAR =  -5           (Gaussian smearing; metals:1)
SIGMA  =  0.05         (Smearing value in eV; metals:0.2)
NELM   =  90           (Max electronic SCF steps)
NELMIN =  6            (Min electronic SCF steps)
EDIFF  =  1E-06        (SCF energy convergence; in eV)
# GGA  =  PS           (PBEsol exchange-correlation)

Ionic Relaxation
NSW    =  0            (Max ionic steps)
IBRION =  2            (Algorithm: 0-MD; 1-Quasi-New; 2-CG)
ISIF   =  2            (Stress/relaxation: 2-Ions, 3-Shape/Ions/V, 4-Shape/Ions)
EDIFFG = -2E-02        (Ionic convergence; eV/AA)
# ISYM =  2            (Symmetry: 0=none; 2=GGA; 3=hybrids)

#DOS control:
EMIN   = -10
EMAX   =  30
NEDOS  = 1001

### KPOINTS

```
KPT-Resolved Value to Generate K-Mesh: 0.030
0
Monkhorst-Pack
   5   5   5
0.0  0.0  0.0
```

## 4 态密度

VASP 计算完成后，我们使用 Python 包 pymatgen 来画态密度。

按元素投影的态密度图对应的 Python 语言是：

```python
from pymatgen.io.vasp import Vasprun
from pymatgen.electronic_structure.plotter import DosPlotter
import matplotlib.pyplot as plt

v = Vasprun('./scf/nonscf/vasprun.xml')
cdos = v.complete_dos
dos = cdos.get_element_dos()
plotter = DosPlotter()
plotter.add_dos('Total DOS', v.tdos)
plotter.add_dos_dict(dos)
plotter.get_plot(xlim=[-4, 4], ylim=[-150, 350])
plt.savefig('ceni4mn_element_dos.png')
```

我们与文献中的数据进行对比[1]：

通过对比，我们发现计算所得的数据与原文献较为符合。

按不同元素的不同轨道投影的态密度图对应的 Python 语言是：

```python
from pymatgen.electronic_structure.core import OrbitalType
from pymatgen.electronic_structure.plotter import DosPlotter
from pymatgen.io.vasp.outputs import Vasprun
import matplotlib.pyplot as plt

# load data
result = Vasprun('./scf/nonscf/vasprun.xml', parse_potcar_file=False)
complete_dos = result.complete_dos
pdos_Ce = complete_dos.get_element_spd_dos('Ce')
pdos_Ni = complete_dos.get_element_spd_dos('Ni')
pdos_Mn = complete_dos.get_element_spd_dos('Mn')

plotter = DosPlotter()
plotter.add_dos('Total DOS', result.tdos)
plotter.add_dos('Ce(f)', pdos_Ce[OrbitalType.f])
plotter.add_dos('Ni(d)', pdos_Ni[OrbitalType.d])
plotter.add_dos('Mn(d)', pdos_Mn[OrbitalType.d])
plotter.get_plot(xlim=(-5, 2), ylim=(-150, 350))
plt.savefig('ceni4mn_element_dos_spd.png')
```

## 5 总结

计算过程总结成了下图：

如有错误，欢迎指正。

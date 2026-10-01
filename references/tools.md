# VASP 相关脚本与工具速查

本文件回答一个问题：**要做的这件事，有没有现成的脚本 / 工具，它是干什么的，入口在哪。**

收录范围（三类，都在本文件里登记）：

1. **外部脚本 / 工具**——第三方分享的小脚本、独立程序、GUI 软件（`chgdiff.pl`、`vtotav.f`、`idealdeform.sh`、`VASP2GRO`、`MEPSearcher`、VASPKIT、VESTA、GROMACS…）；
2. **本 skill 自带的 `scripts/`**——汇总一行，细节与参数以 `scripts/README.md` 为准；
3. **相关文献与外部链接**——用到的原理文章、原作者主页、下载入口。

> **约定**：只记录**功能**（用途 / 输入 → 输出 / 依赖 / 关键注意点 / 来源），不在这里抄实现。
> 要改脚本、要复刻成自带脚本时，回到对应 `workflows.md` 章节看流程细节，或按 `scripts/README.md` 第八节的自查清单新增。
> **登记要求**：以后每收录一篇文章、发现一个新脚本，都先在本文件的速查表里加一行，再写正文条目。

## 目录

1. [速查表（先看这个）](#一速查表先看这个)
2. [外部脚本：后处理小工具](#二外部脚本后处理小工具)
3. [外部脚本：自动化 / 流程类](#三外部脚本自动化--流程类)
4. [外部程序与软件](#四外部程序与软件)
5. [本 skill 自带 scripts/](#五本-skill-自带-scripts)
6. [相关文献与外部链接](#六相关文献与外部链接)

---

## 一、速查表（先看这个）

| 名称 | 类型 | 一句话功能 | 输入 → 输出 | 依赖 | 详见 |
| --- | --- | --- | --- | --- | --- |
| `idealdeform.sh` | 外部 bash | 准静态施加理想拉伸/剪切，自动串联多步晶胞优化，收集应力应变曲线 | VASP 四文件 → `engineeringstressstrain.all`、`truestressstrain.all`、`poscar.*` | Linux + `mpiexec` + gnuplot | [三](#31-idealdeformsh理想拉伸--剪切) |
| `vaspeqstress.sh` | 外部 bash | 迭代施加**任意**外压张量（VASP 自身只有 `PSTRESS` 静水压） | 每步 `OUTCAR` → 迭代更新 `POSCAR`；日志 `pressure.all`、快照 `poscar.*` | Linux + bash + `mpiexec` | [三](#32-vaspeqstresssh--vaspeqstresspy任意外压) |
| `mobility.sh` + PBS 脚本 | 外部 bash | 批量生成 `−2%~+2%` 应变目录、改晶格常数并串起 `opt→scf→band` | 基准目录 `IS/` → 各应变目录及输出 | bash + `sed` + `qsub` | [三](#33-mobilitysh二维迁移率批量应变) |
| `crecip.py` | 外部 Python | 由实空间基矢算倒格矢（常用单位换算，配套迁移率/能带流程） | 含 `_begin_vectors` 的文本 → 倒格矢文件 | Python | [三](#35-crecipy实空间--倒格矢换算) |
| `chgdiff.pl` | 外部 Perl | 两个 `CHGCAR` 相减，得到差分电荷密度 `CHGCAR` | `chgdiff.pl <要减去的> <总电荷>` → `CHGCAR_diff` | Perl | [二](#21-chgdiffpl差分电荷密度相减) |
| `vtotav.f`（改） | 外部 Fortran | 把三维数据沿 X/Y/Z 做**平面平均**，输出一维曲线（原版读 `LOCPOT`，改后可读 `CHGCAR`） | `CHGCAR` + 方向选择 → `PACHG` 一类文本 | `ifort` 编译 | [二](#22-vtotavf平面平均曲线) |
| `VASP2GRO` | 外部程序 | 从 `OUTCAR` 抽 AIMD 轨迹与速度，转成 GROMACS 的 `.gro` | `OUTCAR` → `XDATCAR.gro` + 伪 `.top`/`.mdp` | 可执行文件（Linux/Win） | [二](#23-vasp2groaimd-轨迹转-gromacs) |
| `XDATCAR_toolkit.py` | 外部 Python | AIMD 轨迹转 **PDB**（与 VASP2GRO 同作者，后者可带速度） | `XDATCAR` → `.pdb` | Python | [二](#24-xdatcar_toolkitpy轨迹转-pdb) |
| `xvg.py` | 外部 Python | 把 GROMACS 的 `.xvg` 数据文件画成图 | `*.xvg` → matplotlib 图 | Python + matplotlib | [二](#25-xvgpy画-gromacs-的-xvg) |
| `MEPSearcher` | 外部 Python | **string 法**在二维势能面上自动找 MEP | `PES.data` + `guess.data` → `out.data`（MEP 路径），`draw.py` 看图 | Python3 + ALGlib | [三](#35-mepsearcherstring-法找二维-mep) |
| VASPKIT | 外部程序 | VASP 前后处理瑞士军刀；`1.10.beta3+` 才**正确处理二维材料光学性质** | 各类 VASP 输出 → 数据/图 | VASPKIT | [四](#41-vaspkit) |
| VESTA | 外部 GUI | 看 `CHGCAR`/`LOCPOT`、做差分与等值面、2D 切面 | `CHGCAR` → 三维/二维图 | 图形界面 | [四](#42-vesta) |
| GROMACS (`gmx`) | 外部程序 | 借用分子模拟的分析功能处理 AIMD 轨迹（RDF/RMSD/VACF…） | `.gro`/`.trr` → `.xvg` 等 | GROMACS | [四](#43-gromacs) |
| 弹性矩阵后处理脚本（本文示例） | 外部 Python | 读 `OUTCAR` 弹性矩阵 → 下标重排 + 单位换算 → 各向异性 `E`/`ν`（3D 曲面 / 2D 极坐标） | `OUTCAR` / `ecs.dat` → 图 | numpy + pandas + matplotlib | [三](#36-弹性矩阵后处理脚本本文示例) |
| ELATE | 外部程序/在线 | 由弹性张量算并可视化**各向异性杨氏模量**（3D 曲面），可交叉验证自算结果 | 弹性矩阵 → 各向异性曲面图 | 网页 / 本地 | [四](#44-elate各向异性弹性可视化) |
| JARVIS-DFT | 数据库 | 提供含 `OUTCAR` 与弹性常数（`FD-ELAST`）的算例，适合练手与验证后处理脚本 | 结构 → `OUTCAR` / 弹性数据 | 网络下载 | [四](#45-jarvis-dft弹性与-outcar-数据源) |
| FitSNAP | 外部程序 | 训练 SNAP 机器学习势；吃「逐帧构型 + 能量 + 力 + 应力」的 JSON 数据集 | `vasprun.xml` → SNAP JSON → 势文件 | FitSNAP（python） | [四](#46-fitsnap机器学习势训练) |
| ALAMODE（`alm` / `anphon`） | 外部程序 | 提取力常数（含 LASSO 四阶）与算声子谱/热输运；`MODE=SCPH` 给**各温度**声子谱 | `alm.in`/`anphono.in` + MD 数据集 → XML 力常数 / `*.scph_bands` | ALAMODE（Fortran） | [四](#47-alamodealm--anphon) |
| Wannier90（+ `VASP2WAN90_v2_fix`） | 外部程序 | VASP 波函数 → 最大局域化 Wannier 函数 → 紧束缚模型 / 能带插值 / 拓扑量 | `WAVECAR`+`PROCAR` + `wannier90.win` → `.chk` / `_band.dat` | wannier90 1.2 或 2.1（需接口） | [四](#49-wannier90最大局域化-wannier-函数与紧束缚模型) |
| OVITO | 可视化 | 看 MD/AIMD 轨迹与结构变化（是否「散架」）、做 RDF/配位数等分析 | `XDATCAR`/`CONTCAR`/`.xyz`/LAMMPS dump | 免费（图形界面） | [四](#410-ovito轨迹与结构可视化) |
| AFLOW | 数据库/工具 | 提供**标准基矢形式**的原胞（换胞工具之一）；另有 AFLOW 数据库 | 单胞 ↔ 标准原胞 | 网站/AFLUX | [四](#411-aflow标准基矢原胞与材料数据库) |
| spglib | Python 库 | 对称性检测（空间群、对称操作）与**晶胞标准化**（原胞 ↔ 惯用胞） | Python 里给 `(lattice, positions, numbers)` 即可 | `pip install spglib` | [四](#412-spglib对称性检测与晶胞标准化) |
| `STM-2DScan.py` | 外部脚本（GPL） | 从 CHGCAR/PARCHG 体数据生成 **STM 二维图**；恒高 / **恒流** / 切面三种模式，可复制原胞、输出 PNG | `PARCHG`/`CHGCAR`/`CURRENT` → `.png` | Python + matplotlib | [六](#六相关文献与外部链接) |
| VTST 工具（`vef.pl` / `nebmake.pl` 等） | 外部脚本集 | NEB 路径与过渡态、**结构优化中查看受力收敛** | 配合 `IMAGES`/`IBRION=3` 的 NEB 计算；`vef.pl` 需 **VTST 版** VASP | Perl（随 VTST 分发） | [四](#413-vtst-工具vefplnebmakepl-等) |
| SeeK-Path | 在线工具 | 生成能带路径的高对称点（**只支持体相结构**） | 结构 → 高对称 k 路径 | 网页（<https://www.materialssimulation.com/seekpath/> 一类） | [六](#六相关文献与外部链接) |
| `vaspvis` | Python 包 | **直接画 VASP 的能带 / DOS / 两者联合图**（一行一个图） | ⚠️ 目录需 **`EIGENVAL`+`PROCAR`+`KPOINTS`+`POSCAR`+`INCAR`** → PNG | `pip install vaspvis` | [三](#能带与-dos-的-python-包路线vaspvis--pymatgen) |
| `pymatgen` | Python 库 | 读 VASP 输出（`vasprun.xml`）、**画 DOS / 能带 / 联合图**（`DosPlotter`/`BSPlotter`/`BSDOSPlotter`），也是本 skill `gen_inputs.py` 的依赖 | **只需 `vasprun.xml`** → PNG | `pip install pymatgen` | [三](#能带与-dos-的-python-包路线vaspvis--pymatgen) |
| `mpiPyMC` | Python 代码（GitHub） | 用**蒙特卡洛 + Landau-Ginzburg 拟合**求**铁电居里温度 `Tc`** | `ab initio` 拟合出的 L-G 系数 → `Tc` | 见仓库说明 | <https://github.com/Chengcheng-Xiao/mpiPyMC> |
| `mcsolver`（Mc solver） | 蒙特卡洛程序（含界面） | 由**交换参数 `J`** 模拟**磁居里温度 `Tc`**；支持 XY/Ising/Heisenberg，**铁磁与反铁磁均可** | 晶格基矢 + 超胞 + 原子位置 + `J` + 各向异性 | 见 GitHub | <https://github.com/golddoushi/mcsolver> |
| MTC | 蒙特卡洛程序（需编译） | **直接读 `POSCAR`** 自动建近邻表，由 `INPUT` 指定 `J`/各向异性/温度区间，求 `Tc`（及磁滞回线） | VASP 的 `POSCAR` + `INPUT` → 读 `OUTCAR` | 见课题组页面 | <https://physics.seu.edu.cn/jlwang_zh/mtc/list.htm>（引用 *Comput. Mater. Sci.* 2021, 197, 110638） |

---

## 二、外部脚本：后处理小工具

### 2.1 `chgdiff.pl`（差分电荷密度相减）

- **功能**：把两个 `CHGCAR` 逐格点相减，写出一个格式仍为 `CHGCAR` 的差分文件，供 VESTA 直接打开看等值面，或送去平面平均。
- **用法**：`chgdiff.pl <file1> <file2>`，**`file2` 是总电荷（AB）、`file1` 是要减去的（A 或 B）**；一次只减一个，所以要求 `Δρ = ρ(AB) − ρ(A) − ρ(B)` 得跑两次：
  `chgdiff.pl A AB` → 中间结果；再 `chgdiff.pl B <上一步结果>` → `Δρ`。
- **输入 → 输出**：两个 `CHGCAR` → `CHGCAR_diff`。
- **依赖**：Perl。
- **关键注意点**：
  - 脚本会检查两个文件的 FFT 格点数是否一致，不一致直接 `die`——所以 AB/A/B 必须显式统一 `NGX/NGY/NGZ`；
  - 教程里的版本对输出格式做了一处小修改（`%` 前加空格），使其与 VASP 的 `CHGCAR` 格式严格一致；用原版如果 VESTA 读不进去，先检查这一处；
  - 脚本**不做单位换算、不判断正负号方向**，符号约定由 `file1`/`file2` 的先后顺序决定。
- **来源**：网络流传版本（教程作者做过格式修改），出处见 `articles/20260930-差分电荷密度和平面平均差分电荷密度计算教程.md`。
- **对应流程**：`workflows.md` 第十五节。若要用纯 Python 复刻（免 Perl），按 `scripts/README.md` 第五节的 `post/chgdiff.py`（planned）落地。

### 2.2 `vtotav.f`（平面平均曲线）

- **功能**：把三维格点数据沿某一个方向做平均，输出「该方向格点数 → 平均值」的一维曲线。原版是处理 `LOCPOT` 算功函数的 `vtotav.f`。
- **改了什么**：源码被改成读 **`CHGCAR`**（而不是 `LOCPOT`）——教程给出了改后源码。
- **用法**：`ifort -o vtotav.x vtotav.f` 编译，然后 `./vtotav.x`，运行时交互选择方向（`1=X、2=Y、3=Z`）；输出 `PACHG` 一类文本文件。
- **依赖**：Fortran 编译器（`ifort`；`gfortran` 通常也能编）。
- **关键注意点**：
  - **横坐标是所选方向的格点数，不是 Å**，要自己用晶胞长度换算；**纵坐标是电荷密度 × cell 体积**，单位也要自行转换；
  - 数组上限写死在源码里（`NGXM=256`、`NOUTM=1024`），格点太大要改参数重编；
  - **等价路线**：用 `vtotav.x` 分别处理 AB/A/B 的 `CHGCAR`，再在 Origin/Excel 里做列相减，结果与「先 chgdiff 再平均」一致；用 VASPKIT 的 **Planar-Average CHG** 更省事（见 4.1）。
- **来源/提醒**：教程附了改后源码；文中引用朱全喜老师的提醒——**后处理不要张口就要现成脚本，读懂它到底做了什么再动手**，尤其这种「改别人的脚本去读另一种文件」的做法，切忌刻舟求剑。
- **对应流程**：`workflows.md` 第十五节。

### 2.3 `VASP2GRO`（AIMD 轨迹转 GROMACS）

- **功能**：从 `OUTCAR` 读 AIMD 的原子位置与受力，**用向后差分近似出每一帧的原子速度**，写出 GROMACS 的 `.gro` 轨迹；同时生成伪拓扑 `XDATCAR.top` 与伪输入 `XDATCAR.mdp`，让 `gmx` 的后处理工具能直接吃这份轨迹。
- **输入 → 输出**：`OUTCAR` → `XDATCAR.gro`（含位置+速度）、`XDATCAR.top`、`XDATCAR.mdp`。
- **依赖**：Linux 版 `VASP2GRO.exe` / Windows 版 `VASP2GRO_WIN.exe`，源码同仓库。
- **关键注意点**：
  - 速度是**差分近似**，不是 VASP 直接输出（VASP 只输出最后一帧速度），因此**第一帧速度被舍去**；要做速度相关性质（VACF 等）就要接受这个近似；
  - 程序做了**周期性处理**，避免跨周期性边界时速度出现异常跳变；
  - `.gro`/`.top`/`.mdp` **不能用来真的跑分子动力学**，只是给分析功能当输入；
  - 与 `XDATCAR_toolkit.py` 的分工：后者产出 PDB（**不带速度**），所以只能做 RDF/RMSD 这类不依赖速度的分析。
- **来源**：作者 Tamas 的 GitHub <https://github.com/tamaswells/VASP_script/tree/master/VASP2GRO>；文章 `articles/20260930-用强大的GROMACS分析工具分析VASP的动力学结果.md`。
- **对应流程**：`workflows.md` 第十一节。

### 2.4 `XDATCAR_toolkit.py`（轨迹转 PDB）

- **功能**：把 VASP 的 `XDATCAR` 轨迹转成 PDB 格式，交给 VMD / MDAnalysis 做 RDF（径向分布函数）与 RMSD（均方根偏差）。
- **输入 → 输出**：`XDATCAR` → `.pdb`。
- **依赖**：Python。
- **关键注意点**：**PDB 格式不承载速度**——凡与速度相关的量（VACF、扩散系数按速度定义、声子态密度…）都用不了，得换 `VASP2GRO`（2.3）。
- **来源**：同 2.3 文章中提到的前序工具。

### 2.5 `xvg.py`（画 GROMACS 的 `.xvg`）

- **功能**：读 GROMACS 输出的 `.xvg`（自带 `@ title/xaxis/yaxis` 元数据行与 `#`/`&` 注释行），用 matplotlib 画图；它会把 `xaxis label` / `yaxis label` / `title` 解析出来当坐标轴标签与标题。
- **输入 → 输出**：`.xvg` → matplotlib 图（脚本里是 `plt.show()`，要存图自己加 `savefig`）。
- **依赖**：Python + numpy + matplotlib。
- **关键注意点**：脚本是**命令行参数或交互输入**二选一（`python xvg.py file.xvg`，无参数时提示输入文件名）；解析时用 `eval` 处理引号包裹的标签，标签里有奇怪字符时可能失败。
- **来源**：同 2.3 文章。

---

## 三、外部脚本：自动化 / 流程类

### 3.1 `idealdeform.sh`（理想拉伸 / 剪切）

- **功能**：按固定应变间隔**连续施加应变矩阵**，每一步只做「晶胞 + 原子」优化（`ISIF=4`），把每步应力收集起来，最后自动用 gnuplot 画工程应力应变曲线。用来取弹性模量、理想强度。
- **输入 → 输出**：工作目录里的 VASP 四文件（`POSCAR` **必须是分数坐标**）→ `engineeringstressstrain.all`（工程曲线）、`truestressstrain.all`（真实曲线）、每步 `poscar.*`；默认画图（单位 GPa，**正号 = 拉应力**）。
- **依赖**：bash + `mpiexec`（脚本内 `mpiexec` 变量按本机 MPI 改）+ gnuplot（画图；把 `plot.sh` 复制到当前目录可换画法）。
- **头部参数**：
  - `orientation`：`XX`/`YY`/`ZZ` 拉伸，`XY`/`XZ`/`YZ` 剪切；
  - `initial`（初始应变）、`step`（步长）、`num`（次数）——`initial=0, step=0.01, num=100` 表示 0 → 1.000（100%）；
  - `mpiexec`：运行命令。
- **关键注意点**：
  - `INCAR` 用 `ISIF=4`，**不要用 3**（体积变化会让曲线失真）；并用 **`OPTCELL` 关闭变形方向的弛豫**；
  - 脚本与输入文件放同一目录；
  - **某一步不收敛时程序会停**：先在 `OUTCAR` 里查原因，修好后**从当前阶段继续**，不要从头重跑；
  - **不要把 DFT 的理想应力应变曲线与宏观曲线混为一谈**：宏观曲线来自位错运动与塑性变形，不是同一个概念，写作与解释必须说清用的哪一种；
  - 有表面的体系一般**不需要**真实应力应变曲线（真实/工程换算只在颈缩初期之前成立）。
- **来源**：ponychen，<https://github.com/ponychen123/Vasptools>；文章 `articles/20260930-计算应力应变曲线脚本idealdeform_sh使用指南.md`。
- **对应流程**：`workflows.md` 第十三节。

### 3.2 `vaspeqstress.sh` / `vaspeqstress.py`（任意外压）

- **功能**：VASP 只能加静水压（`PSTRESS`），这个脚本通过**迭代调晶格**把体系逼到目标外压张量（可含剪切分量），研究单轴/剪切加载下的晶胞响应。
- **原理**（广义胡克定律）：读当前 `OUTCAR` 的外压矩阵 → 与目标相减得 `Mad` → 用杨氏模量 `E`、泊松比 `v` 把应力组元换成应变组元 → 更新应变矩阵 `Mnew = (I + Mad·P) · Mold`（`P` 为阻尼系数）→ 重复直到「当前外压 − 目标外压」小于收敛标准。
- **输入 → 输出**：每步 `OUTCAR` → 迭代更新 `POSCAR`；过程日志 `pressure.all`（每步外压与收敛情况）、快照 `poscar.*`。
- **依赖**：bash + `mpiexec`；`INCAR` **必须 `ISIF=2`**。
- **头部参数**：`Setpress`（目标外压六分量 `XX YY ZZ XY YZ ZX`）、`presscirt`（应力差收敛标准，`0.1` 够用别乱改）、`E`（杨氏模量）、`v`（泊松比）、`imax`（最大迭代步数，`100` 够）、`P`（阻尼系数）、`mpiexe`（执行 VASP 的命令）。
- **关键注意点**：
  - **VASP 的外压正号 = 压应力，负号 = 拉应力**（与直觉相反，写论文时注意）；
  - **建议分两次做**：第一次固定原子只弛豫晶胞，收敛后再放开原子弛豫；
  - `E`、`v` 只是初值：实际材料是多晶，与 DFT 结果不严格对应，**意思到位即可**；
  - **VASP 对应力/压应力的计算是出了名的差**，解读这类结果要保守；
  - 脚本里已带 PBS 参数，需要就把行首 `#` 去掉；
  - **尽量用正交胞**：VASP 的应力/压力基于笛卡尔坐标系，最好让三个基矢沿 `X/Y/Z`。
- **版本关系**：原作者（小侯飞氘）的 python2 版 → ponychen 改写成 `vaspeqstress.py`（python3）→ 又用 bash 重写为 `vaspeqstress.sh`（考虑服务器未必部署 python3，且 bash 更适合与作业系统配合）。用例：bcc Ni 静水压 34 次迭代收敛；改成 `(0.0 100 0.0 0.0 0.0 0.0)` 并放开原子弛豫后 46 次收敛。
- **来源**：ponychen / Vasptools；文章 `articles/20260930-vasp定压计算脚本vaspeqstress_sh使用教程.md`。
- **对应流程**：`workflows.md` 第十四节。

### 3.3 `mobility.sh`（二维迁移率批量应变）

- **功能**：为形变势法迁移率批量造输入——用 `cp -r ../IS ./$i` 复制一份基准目录，再用 `sed` 把 `POSCAR` 的晶格常数按应变因子改掉，对 x、y 方向分别扫 `−2% ~ +2%`（步长 0.005）。
- **输入 → 输出**：基准目录 `IS/`（含优化输入与 `2_scf/`，其内含 `band/`）→ 每个应变一个目录；配套 PBS 脚本把 `opt → scf → band` 串起来并沿途复制 `CONTCAR`/`WAVECAR`。
- **依赖**：bash + `sed` + `bc` + `qsub`。
- **关键注意点**：
  - **x 方向改 `POSCAR` 第 3 行、y 方向改第 4 行**（脚本里 `sed -i "3s/..."` / `"4s/..."`），换成别的胞要重核行号；
  - **必须考虑泊松效应**：对 x 施加应变时固定 x 与 z、只优化 y（`OPTCELL` = `000/010/000`），对 y 施加时反之（`100/000/000`）；
  - 脚本里 `qsub` 行默认被注释掉（作者环境不支持批量调用），按自己机器决定是否放开。
- **来源**：文章 `articles/20260930-VASP计算二维材料的载流子迁移率.md`。
- **配套脚本**：`crecip.py`（实空间 → 倒格矢换算，见 3.4）——k 路径长度与有效质量拟合前会用到。
- **对应流程**：`workflows.md` 第十六节。

### 3.4 `crecip.py`（实空间 → 倒格矢换算）

- **功能**：读一份实空间晶格矢量，算**倒格矢**并按指定单位写出——迁移率/能带流程里换算 k 路径长度、倒格矢长度时用得上（原始出处是 Berkeley 一脉流传的老脚本，教程中随迁移率文章一起给出）。
- **输入 → 输出**：
  - 输入：文本文件，含 `inunit ang|bohr` 行与 `_begin_vectors` / `_end_vectors` 包裹的三行基矢（**基矢按行写**）；
  - 输出：`crecip.py infile outfile` 写出倒格矢。
- **依赖**：Python（脚本为 python2 风格，见注意点）。
- **关键注意点**：
  - **单位制必须显式给**：`ang` 或 `bohr`（脚本内部 `Ang2Bohr` 用 1.8897261246，bohr→Å 用 0.5291772109253）；
  - 定义按 `b_j·a_i = 2π δ_ij`，即输出**含 2π**；若上游代码约定「不含 2π」需自行除掉；
  - 脚本里 `CrossProduct` 的注释明确警告 `v3 = v1` 这类写法会给出错误结果——**不要就地改这个函数的别名赋值逻辑**；
  - 老代码（`print` 语句、整数除法、`sys` 未导入等 python2 痕迹）在 python3 下大概率要小改；**改前先核对单位与 2π 约定**。
- **来源**：文章 `articles/20260930-VASP计算二维材料的载流子迁移率.md`（随文给出的 `crecip.py`）。
- **对应流程**：`workflows.md` 第十六节（k 路径长度 / 有效质量拟合前的换算）。

### 3.5 `MEPSearcher`（string 法找二维 MEP）

- **功能**：在**二维势能面**上自动搜索最小能量路径（MEP）。把一串珠子撒在 PES 上让它们自由向能谷跑，稳定后即 MEP。原理为 string 法（E, Ren & Vanden-Eijnden, *Phys. Rev. B* **66**, 052301 (2002)），与 NEB 同属 chain-of-states 方法。
- **输入 → 输出**：
  - `PES.data`：三列 `x, y, 势能值`；
  - `guess.data`：第一行珠子个数（**30–40 个为宜**），第二行起点 `x y`，第三行终点 `x y`（不需要很精确，只要不跑到别的能谷）；
  - 输出 `out.data`（格式同 `PES.data`），用 `draw.py` 画图（红线=初始路径，黑线=MEP）。
- **依赖**：Python3 + **ALGlib** 库。
- **可调参数**：`MEPsearcher.py` 里的 `h`（每次位移步长，默认即可）、`o`（`sd` 或 `cg` 算法，默认 sd；收敛不好就试 cg）。程序**每 30 步报一次进度**，收敛后报告总步数，`diff` 为当前收敛差值。
- **关键注意点**：
  - string 相对 NEB 的**优势是初末态不固定**，方便搭初猜路径，但这个优势仅限二维情形；
  - 作者在 Xin Chen 的 C 版基础上**用 python3 重写并加了 CG 算法**（测试中 CG 略优于 SD），加 `draw.py` 与 3 个例子；三次样条插值够好使，暂无 B 样条；
  - pymatgen 也集成了画 MEP 的功能（三维 + 动画）——**要三维展示用它，讲精度用 string 法**。
- **来源**：Xin Chen 原始版 <https://github.com/chenxin199261/MEPSearcher>；ponychen 重写版见 `articles/20260930-string法自动寻找二维势能面上的MEP.md`。
- **对应流程**：`workflows.md` 第十二节。

### 3.6 弹性矩阵后处理脚本（本文示例）

- **功能**：把 VASP 算出的弹性矩阵变成**方向依赖的杨氏模量与泊松比**并出图——读取 `TOTAL ELASTIC` 块，
  按 Voigt 重排下标、做单位换算，求柔度矩阵，再在球面（3D）或面内（2D）采样求 `E`/`ν`。
- **输入 → 输出**：`OUTCAR`（或 `grep -A 8 "TOTAL ELASTIC" OUTCAR | tail -6 > ecs.dat`）→
  3D 杨氏模量曲面图 / 2D 极坐标 `E(φ)`、`ν(φ)` 图。
- **依赖**：Python + numpy + pandas + matplotlib。
- **关键注意点**：
  - **下标必须重排**：VASP 的 6×6 矩阵顺序不是 Voigt 顺序（`3,4 → +1`；`5 → 3`），不重排就全错；
  - **单位**：矩阵原始单位 kBar（`×0.1` 得 GPa）；**2D 要写成 `C_2D = C_3D × 0.01 × c_z`** 才是 N/m；
  - **2D 的 `c_z` 从 `OUTCAR` 里抓**（示例用 `grep -A 3 'lattice vectors' OUTCAR | tail -1` 取第三个分量），
    别写死；
  - 3D 要先把 6×6 柔度矩阵按 Voigt 规则展开成 `3×3×3×3`（`i=j,k=l → S`；`i≠j,k≠l → S/4`；其余 `→ S/2`）；
  - **网页抓取版代码的空格/缩进丢失**（`for m inrange(6)` 一类），必须按逻辑重写后再跑；
  - 验证：与 **ELATE**（3D）或文献自带弹性矩阵（2D）对比。
- **来源**：文章 `articles/20261001-VASP计算材料的弹性矩阵和杨氏模量.md`。
- **对应流程**：`workflows.md` 第十八节；自带复刻版计划为 `scripts/` 的 `post/elastic.py`（planned）。

---

## 四、外部程序与软件

### 4.1 VASPKIT

- **功能**：VASP 的前后处理工具集（pre- and post-processing）。
- **本 skill 关注的两个能力**：
  1. **二维材料光学性质**：`1.10.beta3` 起可**正确处理二维材料光学性质**（见下方注意点）；旧版本按 3D 处理是错的；
  2. **Planar-Average CHG**：很方便地做平面平均电荷，再手动相减即得平面平均差分电荷（替代 `chgdiff.pl` + 改版 `vtotav.f` 路线）。
  3. **STM 模拟出图（功能号 `325`）**：读带分解电荷密度 `PARCHG`，画**恒定高度模式** STM 图（`vaspkit 325 1 <高度> <na> <nb>`；多高度用 `325 2 <起点> <张数> <步长> <na> <nb>` 便于做动态图）。**必须先打开 `~/.vaspkit` 里的 `AUTO_PLOT=.TRUE.`**，样式在首次运行生成的 `PLOT.in` 里改。见 `workflows.md` 第十九节。
  4. **差分电荷与平面平均（功能号 `31`）**：`31 314` 依次喂 AB、A、B 的 `CHGCAR` → 出 `CHGDIFF.vasp`（VESTA 里青色 = 电荷减少、黄色 = 增加）；把 `CHGDIFF.vasp` 改名为 `CHGCAR` 后用 `31 316` 选方向 → `PLANAR_AVERAGE.dat`——**免 Perl/Fortran 的差分+平面平均路线**。另有 `4 402` 固定底层原子、`1 101/102/103` 生成 INCAR / KPOINTS（顺带 POTCAR）/ POTCAR。见 `workflows.md` 第十五节路线 B。
  5. **POTCAR / KPOINTS / INCAR 生成（功能号 `1`）**：`1 102` 由 POSCAR 生成 `KPOINTS` 并**按预设自动完成 POTCAR**；`1 104` 可**手动指定** POTCAR；`1 101` 生成 INCAR；`1 103` 单独生成 POTCAR。选变体时核对 **POTCAR 第二行的价电子数**（见 `errors.md` §1.4）。
  6. **有效质量（功能号 `9`）**：`911` 找带边位置；`912`/`913` 生成带边附近的 `KPOINTS`/`POTCAR`（**INCAR 要自己写**）→ 跑 VASP → 把 `VPKIT.in` 第一行改成 `2` 再跑一次 `913` → 输出电子/空穴有效质量。官方教程 <http://vaspkit.cn/index.php/52.html>；见 `workflows.md` 第二十七节。
  7. **原胞与其它辅助功能**：**`6 602` 把单胞转成「标准基矢形式」的原胞**（算弹性/介电/压电前必备，见 `workflows.md` §18.0）；`2 203` 从 `OUTCAR` 提取弹性矩阵（并报出晶系与独立常数个数）。
- **关键注意点**：**二维材料的介电常数/光学性质不能直接套用 3D 定义**——程序不报错，但数值不是 well-defined 的物理量。这是典型的**静默错误**：国内相当多已发表工作都没处理真空层效应。
- **引用**：Wang, V.; Xu, N.; Liu, J.-C.; Tang, G.; Geng, W. T. *VASPKIT: A Pre- and Post-Processing Program for VASP code*, arXiv:1908.08269 (2019)。
- **来源文章**：`articles/20260930-二维材料静态介电常数和光学性质计算Tips.md`（另见 `errors.md` 第七节末尾）。
- **对应流程**：`workflows.md` 第十五节（平面平均替代路线）。

### 4.2 VESTA

- **功能**：三维可视化与体积数据处理。
- **本 skill 关注的用法**：
  - **差分电荷密度三维图**：打开 AB 的 `CHGCAR` → `Edit → Edit Data → Volumetric Data → Import` 选 A 的 `CHGCAR` → 勾 `Subtract from current data` → OK；对 B 重复；用 `Properties…` 调等值面；
  - **二维切面**：`Utilities → 2D Data Display`；
  - 成键可视化：`Edit → Bonds → New`（`search molecules` / `Do not search atoms…`，`Max. length` 按需），可取消 `Volumetric data` 下的 `Show sections`。
- **关键注意点**：VESTA 的相减是**交互式、顺序敏感**的：先导入总的、再依次减去各组分；导入的三个 `CHGCAR` 必须同格子（否则先是假条纹，然后是错的图）。
- **另一个坑**：**VESTA 里「删原子」不会写回文件**（视图里删掉了，导出/保存出来的还是原样）——需要删原子请回 Materials Studio 等建模软件处理后再导出。
- **二维切面的限制**：`Utilities → 2D Data Display → Slice` 出的面图**能显示 colorbar，但显示不了原子**；要在切面上标原子请改用 `Edit → Lattice Planes...`（见 `workflows.md` 第十五节）。
- **来源文章**：`articles/20260930-差分电荷密度和平面平均差分电荷密度计算教程.md`。

### 4.3 GROMACS

- **功能**：生物模拟领域常用 MD 软件，**运行快、后处理功能强**；这里被当作 AIMD 后处理的「分析引擎」用（AIMD 自身后处理工具尚不完善）。
- **安装**：Ubuntu `apt-get install gromacs`；CentOS `yum install gromacs`；也可并行编译安装（参考 sobereva.com/457）。装好 `gmx`（或并行版 `gmx_mpi`）即用。
- **典型命令链**（配合 2.3 的 `VASP2GRO` 产物）：
  1. `gmx trjconv -f XDATCAR.gro -o XDATCAR.trr`：转成二进制轨迹；
  2. `gmx grompp -f XDATCAR.mdp -c XDATCAR.gro -p XDATCAR.top -o em.tpr`：预编译引擎打包输入；
  3. `gmx make_ndx -f XDATCAR.gro`：分组（如 `a H`、`a O`，`3 | 4` 合并，`q` 保存 `index.ndx`）；
  4. `gmx velacc -f XDATCAR.trr -o vacf.xvg -n index.ndx`：速度自相关函数 VACF（按提示选组）。
- **关键注意点**：并行安装时命令要写 `gmx_mpi`；`.xvg` 用 `xvg.py`（2.5）或 xmgrace/Origin 作图。
- **教程**：李继存老师博客 <https://jerkwin.github.io/GMX/GMXprg/>。
- **来源文章**：`articles/20260930-用强大的GROMACS分析工具分析VASP的动力学结果.md`；流程见 `workflows.md` 第十一节。

### 4.4 ELATE（各向异性弹性可视化）

- **功能**：输入弹性张量（`C` 或 `S`），计算并可视化**方向依赖的杨氏模量**（三维曲面）、泊松比、剪切模量等，
  是验证自写后处理脚本的现成参照。
- **输入 → 输出**：弹性矩阵 → 各向异性曲面图（在线版或本地版）。
- **关键注意点**：ELATE 要的是**完整且已转成标准单位的弹性张量**——送进去之前先确认下标顺序与单位
  （见三.6 的两条换算），否则会用错误的输入得到"看起来合理"的图。
- **对应流程**：`workflows.md` 第十八节（3D 结果交叉验证）。

### 4.5 JARVIS-DFT（弹性与 OUTCAR 数据源）

- **功能**：公开数据库，除结构外还提供弹性常数（`FD-ELAST`）与配套 `OUTCAR`，适合用来**练手与验证**
  弹性后处理脚本（原文即用 #7974 的 `OUTCAR` 做的测试）。
- **输入 → 输出**：网页下载结构 / `OUTCAR` / 弹性数据。
- **关键注意点**：下载的是**他人算好的结果**，用于验证脚本逻辑；真正做科研仍要自己按 `workflows.md`
  第十八节的参数（`IBRION=6` / `ISIF=3` / `NFREE=4` / `NSW=1`）算。
- **入口**：<https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/>（示例文件 `JVASP-7974.xml`）。


### 4.6 FitSNAP（机器学习势训练）

- **功能**：训练 SNAP（Spectral Neighbor Analysis Potential）机器学习势，输入是**逐帧构型数据集**
  （每个构型含晶格、原子种类、位置、受力、应力与总能量）。
- **本 skill 关注的接口**：数据从 VASP 的 `vasprun.xml` 抽出来后，按 SNAP 的字段约定写成 JSON：
  `LatticeStyle=angstrom`、`EnergyStyle=electronvolt`、`StressStyle=bar`、
  `ForcesStyle=electronvoltperangstrom`、`AtomTypeStyle=chemicalsymbol`。
- **关键注意点**：
  - **单位声明必须与数据真实单位一致**（典型坑：`vasprun.xml` 的应力是 kBar，SNAP 要 bar → ×1000）；
  - 数据集要覆盖足够多的构型与形变（否则势外推能力差），帧的抽取间隔（`d_step`）决定数据量；
  - 用"数行偏移"解析 `vasprun.xml` 的老脚本换版本就会错位，优先用 `iterparse` / `pymatgen.Vasprun`。
- **来源文章**：`articles/20261001-vasprun_xml_to_json_file_天帝君豪的个人博客.md`
  （原文 2020 年，脚本为 python2 风格）。
- **对应流程**：`workflows.md` 第二十一节。


### 4.7 ALAMODE（`alm` / `anphon`）

- **功能**：从第一性原理数据里提取**力常数**，并据此计算声子色散、声子-声子相互作用与晶格热输运。
  两种常用模式：**有限位移法**（谐近似，见 `workflows.md` 第六节）与 **SCPH 自洽声子理论**
  （处理非谐、给出**各温度**声子谱，见第二十二节）。
- **本 skill 关注的用法**：
  - `alm alm.in > alm.log`：拟合力常数 → XML（示例 `Nb.xml`）；四阶力常数可用 **LASSO**
    （`&optimize LMODEL=enet` + `CV`/`L1_*`/`STANDARDIZE`/`CONV_TOL`）；
  - `anphon anphono.in > anphono.log`：`MODE=SCPH` 时输出 `scph.scph_bands`（各温度声子谱）；
    `TMIN/TMAX/DT` 控制温度扫描。
- **配套脚本**：原文用 `extract_disp.py` / `extract_force.py` 从 MD 的 `vasprun.xml` 提取位移与受力，
  再拼成 `Dfile`（**原文未提供源码**，只给了用法）。
- **关键注意点**：
  - **`&cell` 的晶格常数是 Bohr 单位**（`1 Bohr = 0.529177208 Å`，见 `references/constants.md`）；
  - `Dfile` 的**列序固定**：`disp_x disp_y disp_z force_x force_y force_z`，每行一个原子；
  - `anphono.in` 里**建议用原胞**（原文注明 "primitive cell is best"）；
  - 版本差异明显，用前对照所装版本的官方手册核对字段名。
- **来源文章**：`articles/20261001-alamode_scph计算高温声子谱_天帝君豪的个人博客.md`
  （另有同站 TDEP 路线，未收录）。
- **对应流程**：`workflows.md` 第六节（有限位移）、第二十二节（SCPH）。


### 4.8 ABINIT（另一个第一性原理代码）与 feram 参数库

- **ABINIT**：与 VASP 同类的平面波 DFT 代码。**输入文件的对应关系**（原作者笔记里的说法）：
  - `xxx.in`：输入文件，**相当于 VASP 的 `INCAR` + `KPOINTS` + `POSCAR` 三件套**；
  - `xxx.files`：告诉程序"本目录里哪些文件要被用到"；
  - 剩下是赝势文件；把这些放在同一目录即可运行。
- **feram**：基于 ABINIT 做铁电/晶格动力学计算的配套工具，其 **parameters 页面**收集了**大量材料的收敛参数**
  （`ENCUT`、k 点等的收敛性测试结果）**以及对应的输入文件**，是该笔记推荐的核心资源。
- **可用性**：原作者（2017 年）称按该页参数复算，**结果前十个有效数字一致**——这类"别人公布参数 + 你复现数值"
  的做法，本身就是检查自己收敛设置是否可信的好办法。
  ⚠️ 站点为 SourceForge 上的老项目（`loto.sourceforge.net`），**现在可能已不可访问**，引用前先试一下。
- **来源文章**：`articles/20261001-VASP的个人笔记_五.md`
- **对应登记**：`references/tools.md` 六（外部链接表）。


### 4.9 Wannier90（最大局域化 Wannier 函数与紧束缚模型）

- **功能**：把 DFT 波函数变换成**最大局域化 Wannier 函数（MLWF）**，用于**能带插值**、构造**紧束缚（TB）模型**、
  计算拓扑不变量与输运量（如自旋霍尔电导）。
- **与 VASP 的接口（选版本是关键）**：
  - **wannier90 1.2**：接口开箱可用；**缺点**是做不了自旋向上/向下分别的能带（无 SOC 的铁磁/反铁磁体系）。
  - **wannier90 2.1**：与 VASP 结合的最新版，但**默认接口不好**，需用肖承诚的
    `VASP2WAN90_v2_fix`（<https://github.com/Chengcheng-Xiao/VASP2WAN90_v2_fix>，**针对 VASP 5.4.4**）；
    编译要点：`patch -p0 < mlwf.patch`，`makefile.include` 加 `CPP_OPTIONS+=-DVASP2WANNIER90v2`
    与 `LLIBS+=.../libwannier.a`。
- **关键注意点**：**INCAR 里不要用 `NPAR`**；`num_bands` 必须等于 INCAR 的 `NBANDS` 且 ≥ `num_wann`；
  `num_wann` 由投影轨道数与原子数算出来（s=1、p=3、d=5，SOC 时翻倍）。
- **来源文章**：`articles/20261001-一文搞定VASP_wannier90构造紧束缚模型.md`
- **对应流程**：`workflows.md` 第二十五节。


### 4.10 OVITO（轨迹与结构可视化）

- **功能**：看分子动力学/AIMD 的**轨迹**（结构随时间怎么变、有没有"散架"），做**径向分布函数（RDF）**、
  配位数、键角统计等分析；也能读 `CONTCAR`/`XDATCAR`（转成 `.xyz`/`POSCAR` 后）、LAMMPS dump、`.cif` 等。
- **在 VASP 流程里的位置**：`workflows.md` 第二十六节（AIMD 验证稳定性）的第二步——
  能量曲线看"有没有漂移"，OVITO 看"结构有没有被破坏"，两者合起来才能判断稳不稳。
- **入口**：<https://www.ovito.org/>（免费版即可满足结构可视化与基本分析）。
- **小提示**：`XDATCAR` 直接拖进 OVITO 若不被识别，可先用 VASP 后处理脚本或
  `ase`/`pymatgen` 转成 `.xyz` 再打开。


### 4.11 AFLOW（标准基矢原胞与材料数据库）

- **功能**：材料数据库 + 一系列命令行工具（AFLUX 等）。**对本 skill 最有价值的一点**：它给出的原胞
  是**「标准基矢形式」**（standard primitive cell），与 VASPKIT 的 `6 602` 一致。
- **为什么重要**：**VESTA / Materials Studio / Materials Project 给出的原胞通常不是标准基矢形式**，
  用它算**弹性常数、介电、压电**会得到**不符合晶体对称性、但不报错**的结果（详见 `workflows.md` §18.0）。
- **入口**：<https://aflow.org/>（另见其换胞工具与数据库检索）。
- **来源文章**：`articles/20261001-原胞转化方法以及标准原胞在计算中的重要性.md`（作者 obaica）。


### 4.12 spglib（对称性检测与晶胞标准化）

- **功能**：晶体对称性分析（空间群、对称操作、等价原子）与**晶胞标准化**——把结构在
  **原胞（primitive）/ 惯用胞（conventional）/ 标准化胞**之间来回转换。
- **在 VASP 流程里的位置**：与 §4.11 的 AFLOW、VASPKIT 的 `6 602` 一样，是**换胞工具**之一；
  做**弹性/介电/压电**等对称性敏感的性质前，用它得到标准胞更稳妥（见 `workflows.md` §18.0）。
- **两个关键 API**（本库参考脚本 `scripts/reference/cellconv_*.py` 用的就是它们）：

```python
import spglib
cell = (lattice, positions, numbers)          # 晶格(3×3)、分数坐标(N×3)、原子序号(整数，按元素分组)
spglib.get_symmetry_dataset(cell, symprec=1e-3)["number"]        # 空间群号
spglib.standardize_cell(cell, symprec=1e-3, to_primitive=False)  # False=惯用胞；True=原胞
```

  ⚠️ `numbers` 必须是**按元素分组**的整数序列（同一元素同一编号），长度要与 `positions` 一致——
  这是最常见的踩坑点（本库收集的参考脚本里就有一处只按第一种元素生成序号的写法）。
- **来源文章**：`articles/20261001-晶胞转换_天帝君豪的个人博客.md`
- **参考脚本**：`scripts/reference/cellconv_read_poscar.py`、`cellconv_reposcar.py`、`cellconv_run.py`。


### 4.13 VTST 工具（`vef.pl`、`nebmake.pl` 等）

- **这是什么**：**VTST Tools** 是一套给 VASP 打补丁的扩展（NEB/CI-NEB、dimer 等），随它分发一批 Perl 脚本：
  - **`nebmake.pl`**：由初末态结构插值生成 NEB 的中间 `POSCAR`（配 `IMAGES`）；
  - **`vef.pl`**：**查看结构优化/过渡态搜索中各离子步的受力**（能看到最大受力）；
  - 其它：`nebbarrier.pl` / `nebspline.pl` 等用于提取 NEB 能垒与路径。
- ⚠️ **前提**：`vef.pl` 等脚本**只适用于用 VTST 版 VASP 编译的程序**——**非 VTST 版用不了**
  （官方脚本页：<https://theory.cm.utexas.edu/vtsttools/scripts.html>）。
- **不想装 VTST 怎么办**：用本库参考脚本 `scripts/reference/force_conv.sh`（纯 bash+awk+gnuplot，
  会把固定原子排除掉，并直接在终端画出"离子步 vs 最大受力"曲线），见 `workflows.md` 第一节。
- **相关**：`workflows.md` §二十四（迁移能垒 / NEB 起步），`errors.md` §3.x（离子步报错）。


### 4.14 PWmat（另一个第一性原理代码，含结构优化建议文档）

- **是什么**：国产平面波 DFT 代码（PWmat），与 VASP/ABINIT 同类。**对 VASP 用户的价值主要在它的文档**：
  官方有一页**结构优化建议**（`relaxtentips`），讲的全是通用经验——SCF 与结构收敛的关系、金属加展宽 /
  绝缘体加混合、大体系不要做晶格优化、固定基体下层、HSE 先 PBE 预优化、收敛判据的"适可而止"
  （本库已提炼进 `workflows.md` 第一节与 `errors.md` §3.1，并给出 VASP 对应手段）。
- **入口**：<https://hongzhentian.github.io/PWmat-doc/#/PWmat/relaxtentips>（结构优化建议页）。
- **来源文章**：`articles/20261001-计算大牛教你优化结构.md`
  （注意：原文是**带推广性质**的文章——开头与结尾都有"购买请加微信"，本库只提取其中的通用技术建议）。

---

## 五、本 skill 自带 `scripts/`

**只列功能，参数/字段/退出码一律以 `scripts/README.md` 为准**（那里是索引与编写约定）。

| 脚本 | 功能 | 依赖 |
| --- | --- | --- |
| `gen_inputs.py` | 读结构（POSCAR/CIF…）生成 `INCAR`/`KPOINTS`/`POSCAR`，按需拼 `POTCAR`；工作流 `opt`/`scf`/`band`/`dos`/`mag` | L3 |
| `gen_lobsterin.py` | 统计键长并生成 LOBSTER 的 `lobsterin`（COHP/COOP） | L3 |
| `search_kb.py` | 全库关键词检索（`errors.md`、`workflows.md`、`articles/`、`scripts/**/*.py`） | L0 |
| `add_article.py` | 收录文章进 `references/articles/`：本地文件或 http(s) 链接（HTML 转正文抓题录，PDF 需 `pypdf`） | L0 |
| `parse/parse_oszicar.py` | `OSZICAR` → 离子步/电子步/MD 步数据（CSV/JSON） | L0 |
| `parse/parse_outcar.py` | `OUTCAR` → 关键参数、能量、受力、警告与致命行（JSON；`--forces` 出 CSV） | L0 |
| `parse/parse_cohpcar.py` | `COHPCAR.lobster` → 能量/平均 COHP/ICOHP（CSV；`--pairs` 出逐键列） | L0 |

**规划中（尚未落地）的脚本**——包括 `chgdiff.py`、`effmass.py`、`mobility_dp.py`、`stress_strain.py`、`eq_stress.py`、`ideal_deform.py`、`plot_*`、`elastic.py`、`check_convergence.py` 等，完整清单与状态见 `scripts/README.md` 第五节；**其中的每一个，本质上都是本文件第二/三节某个外部脚本的纯 Python 复刻**，功能定义以对应外部脚本条目为准。

---

## 六、相关文献与外部链接

| 主题 | 链接 / 出处 | 备注 |
| --- | --- | --- |
| ponychen / Vasptools（`idealdeform.sh`、`vaspeqstress`、MEP 等脚本） | <https://github.com/ponychen123/Vasptools> | 本文多个自动化脚本的来源 |
| VASP2GRO（AIMD → GROMACS） | <https://github.com/tamaswells/VASP_script/tree/master/VASP2GRO> | Linux/Windows 可执行 + 源码 |
| MEPSearcher（string 法） | <https://github.com/chenxin199261/MEPSearcher> | 原始版本（C 版） |
| GROMACS 中文教程（李继存） | <https://jerkwin.github.io/GMX/GMXprg/> | `gmx` 各分析工具的用法 |
| GROMACS 并行安装 | <http://sobereva.com/457> | 安装参考 |
| VASPKIT | arXiv:1908.08269 | 引用要求见原文 |
| GROMACS 速度自相关函数做法参考 | <http://blog.sciencenet.cn/blog-3102863-1159419.html> | VASP2GRO 采用的向后差分思路来源 |
| 二维材料介电/光学性质（为什么 3D 定义不适用） | *Nano Lett.* DOI 10.1021/acs.nanolett.9b02982；*New J. Phys.* DOI 10.1088/1367-2630/16/10/105007 | 静默错误的原理文章 |
| 二维迁移率形变势理论 | Bardeen & Shockley, *Phys. Rev.* **80**, 72 (1950)；结果见 *J. Phys. Chem. C* **2019**, *123*, 12781 | 公式与系数的原始出处 |
| string 法 | E, Ren & Vanden-Eijnden, *Phys. Rev. B* **66**, 052301 (2002) | MEP 搜索原理 |
| 差分电荷密度图例 | DOI 10.1039/C7TA02109G | 平面平均曲线示意 |
| ReMoC（人大迁移率软件包） | <https://gitee.com/jigroupruc> | 迁移率计算参考实现 |
| 原文作者的迁移率博客 | <https://yh-phys.github.io>；<https://chempeng.github.io/2017/09/01/The-Calculation-of-Carrier-Mobility/> | 操作细节补充 |
| 各向异性杨氏模量/泊松比的公式推导 | <https://www.sciencedirect.com/science/article/pii/S0010465521003076> | 6×6 → 3×3×3×3 的 Voigt 展开与方向依赖公式（原文引用） |
| ELATE（弹性张量可视化） | <https://progs.coudert.name/elate> | 3D 各向异性曲面，交叉验证用 |
| VASP 编译教程汇编（按版本） | `articles/20261001-VASP_编译相关链接集锦.md`（原文 <https://zhuanlan.zhihu.com/p/703247045>） | 约 60 条编译教程/视频，按 4.4.5 / 5.2.0–5.4.4 / 6.1.0–6.4.0 分组；覆盖 Intel oneAPI、GPU、VTST、Wannier90、WSL/Windows、Docker、HDF5 等专题 |
| 知乎开放平台 CLI（`zhihu-cli`） | 由 `zhihu` skill 提供；`me content --content-url <链接>` 读**本人**文章全文 | 抓取知乎被 403 时的正路，配套流程见 `SKILL.md` 第四节 |
| ML 势数据集准备（`vasprun.xml` → JSON） | `articles/20261001-vasprun_xml_to_json_file_天帝君豪的个人博客.md`（原文 <https://tiandijunhao.github.io/2020/07/10/grep-config-to-json-from-vasprunxml/>） | 逐帧提取能量/晶格/位置/受力/应力；含 SNAP 字段约定与单位坑 |
| 高温声子（SCPH）与单位常数 | `articles/20261001-alamode_scph计算高温声子谱_天帝君豪的个人博客.md`；`articles/20261001-常用物理单位与物理常数_天帝君豪的个人博客.md` | SCPH 流程见 `workflows.md` 第二十二节；单位换算速查见 `references/constants.md` |
| 个人笔记六篇（zjtt）：铁电畸变 / 波恩有效电荷 / POTCAR / EDDRMM（两篇）/ ABINIT-参数库 | `articles/20261001-VASP计算的个人笔记.md`、`…_二.md`、`…_三.md`、`…_四.md`、`…_五.md`、`…_六.md`（原文 <https://zhuanlan.zhihu.com/p/27711867>、<https://zhuanlan.zhihu.com/p/27729576>、<https://zhuanlan.zhihu.com/p/27908849>、<https://zhuanlan.zhihu.com/p/28029551>、<https://zhuanlan.zhihu.com/p/30002605>、<https://zhuanlan.zhihu.com/p/30402826>） | 作者自述为个人笔记、**不保证正确性**；要点进 `workflows.md` 第一/二十三节、`errors.md` §1.4 与 §2.6（含 `ALGO=F` 两阶段策略），外部参数库见 `tools.md` 四.8 |
| 材料收敛参数参考（feram / ABINIT） | <http://loto.sourceforge.net/feram/parameters/parameters.html>（2017 年记录，站点可能已失效） | 列出大量材料的 `ENCUT`/k 点等收敛参数与输入文件；原作者称按其复算前十个有效数字一致 |
| 上手教程（实验人员入门，含三个算例） | `articles/20261001-材料科学实验人员_如何入门_第一性原理计算_计算材料学_VASP_从0到上手.md`（原文 <https://zhuanlan.zhihu.com/p/97102012>） | 提炼成 `references/onboarding.md`；三个算例的公式进 `workflows.md` 第二十四节 |
| 材料数据源（热力学/结合能/表面张力/单位换算） | NIST <https://physics.nist.gov/cuu/Constants/index.html>；CRC <http://hbcponline.com/faces/contents/ContentsSearch.xhtml>；结合能 <http://www.knowledgedoor.com/2/elements_handbook/cohesive_energy.html>；表面张力 <http://www.surface-tension.de/> | 清单与说明见 `references/onboarding.md` 第六节 |
| MatCloud+（云计算平台） | <http://www.matcloudplus.com/> | 浏览器界面即可跑 VASP，不必自己装环境；见 `references/onboarding.md` 第二节 |
| 电荷密度差分的三种形式与 vaspkit 实操 | `articles/20261001-第一性原理_VASP计算电荷密度差分并绘制电荷密度差分图.md`（原文 <https://zhuanlan.zhihu.com/p/396877339>） | 三种「差分」的概念区分与 `ICHARG=12` 变形电荷密度做法进 `workflows.md` 第十五节；FFT 网格报错进 `errors.md` §8.14 |
| Wannier90 紧束缚模型完整教程 | `articles/20261001-一文搞定VASP_wannier90构造紧束缚模型.md`（原文 <https://zhuanlan.zhihu.com/p/355317202>） | 版本选择/编译打补丁/三步流程/`num_wann` 算法/窗口与 spread 判据/三种自旋情形 → `workflows.md` 第二十五节 |
| VASP 运行效率（标度律与并行取舍） | `articles/20261001-vasp运行效率.md`（原文 <https://zhuanlan.zhihu.com/p/397533516>） | 时间 ∝ `ENCUT³`/`NELECT³`；`LREAL`/`ALGO`/`NPAR`/`KPAR` 怎么取 → `references/performance.md` |
| VASP 报错及解决方法整理 -01（几何优化/ZPE/NEB/能带 DOS） | `articles/20261001-VASP报错及解决方法整理-01.md`（原文 <https://zhuanlan.zhihu.com/p/449755288>） | 9 条新报错进 `errors.md` §8.15–§8.23（含 `No initial positions read in`、NEB 原子不匹配、`LREAL` 小胞提示、`SYMPREC=0.001` 等） |
| 电荷密度分布（`CHGCAR` 结构 + VESTA 判读） | `articles/20261001-VASP计算电荷密度分布.md`（原文 <https://zhuanlan.zhihu.com/p/405655888>，转载自公众号《VASP学习交流》） | `CHGCAR` 逐段结构（`8+原子数` 行 → 空行 → `NGXF NGYF NGZF` → 数据）、价电子/自旋密度、键性与梯度的判读 → `workflows.md` 第十五节 |
| AIMD 验证结构热稳定性 | `articles/20261001-第一性原理分子动力学分析结构稳定性_VASP-AIMD.md`（原文 <https://zhuanlan.zhihu.com/p/359874915>） | NVT/NPT 的 `ISIF` 配套、`vasp_gam` Γ-only 加速、能量-时间判据、`EDIFFG` 在 MD 中不生效 → `workflows.md` 第二十六节；OVITO 见 `tools.md` 四.10 |
| 《Learn VASP The Hard Way》（李强博士） | 中文 VASP 入门教程（从 Linux 基础到完整流程）；社区（含本 skill 收录的编译指南）反复把它列为入门首选、其作者被称作启蒙者 | 适合从零开始；配合 `references/onboarding.md` 使用 |
| VASP 官方资源 | 站点 <https://www.vasp.at/>；**wiki / 手册 / tutorials** <https://vasp.at/wiki/>；论坛 <https://www.vasp.at/forum/> | **查参数定义以 wiki 为准**（本 skill 的 `ICHARG`/`LEPSILON`/`MDALGO` 等条目都引用它）；报错与疑难优先搜官方论坛 |
| 新手学习记录（第一次跑 VASP） | `articles/20261001-VASP学习记录_二_VASP的第一次尝试_1.md`（原文 <https://zhuanlan.zhihu.com/p/556071342>） | 官方 O 原子算例的四个输入文件 + 逐行说明 + Windows 新手陷阱 → `references/onboarding.md` 第八节 |
| 新手学习记录（VASP 中常用的 Linux 命令） | `articles/20261001-VASP学习记录_三_VASP中常用的Linux命令.md`（原文 <https://zhuanlan.zhihu.com/p/556163899>） | 整理为 `references/linux.md`（含 `for`/`seq`、`sed -i`、通配符、extglob 反选前提与安全提醒） |
| 新手学习记录（Vim 文本编辑器） | `articles/20261001-VASP学习记录_四_Vim文本编辑器.md`（原文 <https://zhuanlan.zhihu.com/p/557009386>） | Vim 三模式、移动/查找/替换速查 → `references/linux.md` 第六节 |
| 新手学习记录（awk 命令） | `articles/20261001-VASP学习记录_五_awk命令.md`（原文 <https://zhuanlan.zhihu.com/p/558122542>） | awk 通用形式/BEGIN-主体-END/`-F`/内置变量 → `references/linux.md` 第七节 |
| PAW 算法介绍（理论，面向应用者） | `articles/20261001-PAW_Projected_augmented_wave_算法介绍.md`（原文 <https://zhuanlan.zhihu.com/p/575479762>） | `PBE`/`PAW`/`PW` 三者关系、`POTCAR` 里存的是什么、PAW 精度来源 → `references/onboarding.md` §3.1 |
| 电子/空穴有效质量（能带拟合法 + VASPKIT 法） | `articles/20261001-基于vasp的电子和空穴的有效质量计算方法.md`（原文 <https://zhuanlan.zhihu.com/p/570826907>） | 带边取点与 2 阶拟合、`m*=1/(2C)` 的由来、**横坐标单位换算的争议**、VASPKIT 911/912/913 两步走 → `workflows.md` 第二十七节 |
| 原胞转化与标准基矢的重要性（obaica／学术之友） | `articles/20261001-原胞转化方法以及标准原胞在计算中的重要性.md`（原文 <https://mp.weixin.qq.com/s/NBWI1l-8ZY7WWvOhVOelXA>） | 四种换胞方法对比（AFLOW/VASPKIT 才是标准基矢）、非标准原胞导致弹性矩阵静默错误 → `workflows.md` §18.0、`errors.md` §七 |
| K 点/ENCUT 收敛性测试脚本（June976） | `articles/20261001-自动进行K点和ENCUT测试bash脚本.md`（原文 <https://www.jun997.xyz/2021/10/19/fa8688fdb49b.html>） | 脚本收集于 `scripts/reference/kpoint_encut_test.sh`（已做最小修复）；流程说明见 `workflows.md` 第二十八节 |
| VASP 赝势简介（目录/后缀/精度权衡） | `articles/20261001-VASP赝势简介.md`（原文 <https://zhuanlan.zhihu.com/p/146280554>，转载自 52souji.net） | `paw`/`paw_gga`/`paw_pbe`/`pot`/`pot_GGA` 与泛函的对应、`_s`/`_h`/`_sv`/`_pv` 后缀、USPP vs PAW → `references/onboarding.md` §3.2 |
| VASP 参数含义（opt 阶段逐参数讲解） | `articles/20261001-VASP参数含义.md`（原文 <https://zhuanlan.zhihu.com/p/618286143>） | 整理为 `references/incar.md`（INCAR 参数速查；已订正原文 `ICHARG`/`ISIF`/拼写等笔误） |
| VASP 并行参数 NCORE/NPAR/KPAR | `articles/20261001-VASP并行运算参数NCORE_NPAR_KPAR.md`（原文 <https://zhuanlan.zhihu.com/p/666602300>） | 三层并行的维度、`grep irre OUTCAR`/`grep NBANDS OUTCAR`、整除约束 → `references/performance.md` §四；经验清单见 `errors.md` §8.11 |
| vasp 并行参数设置（含 VASP6 混合并行，lipai） | `articles/20261001-vasp并行参数设置.md`（原文 <https://zhuanlan.zhihu.com/p/485153538>） | 按体系规模的三档策略、`KPAR` 优先于 `NPAR`、`vasp_gam` 省内存实测、hybrid MPI/OpenMP 何时有用 → `references/performance.md` §4.2–§4.4 |
| VASP K 点问题（MP 与 Gamma 撒点，lipai） | `articles/20261001-VASP_K点问题.md`（原文 <https://zhuanlan.zhihu.com/p/397873103>） | 「不宜采 Γ」与「六方例外（不可约 k 点约 3 倍）」两派经验的调和 → `errors.md` §8.20、`workflows.md` 第十五节 |
| VASP 输入文件 KPOINTS（五行式与密度估算） | `articles/20261001-VASP输入文件KPOINTS.md`（原文 <https://zhuanlan.zhihu.com/p/390793069>） | 四种 k 点密度估法 + 三条例外（真空层取 1、`ISMEAR=-5` 需 ≥`2 2 2`、六方用 Γ）→ `workflows.md` §28.5；五行式逐行陷阱见 `references/onboarding.md` §8.2 |
| VASP 官网 `IBRION` 参数说明（Wiki 翻译，June976） | `articles/20261001-VASP官网关于IBRION参数的说明.md`（原文 <https://www.jun997.xyz/2022/07/20/4b7c346573e6.html>，译自 <https://www.vasp.at/wiki/index.php/IBRION>） | 各取值语义与选择指南、DFPT（`7`/`8`）的局限、**从 `trialstep` 反推最佳 `POTIM`**、`IBRION=44` 二聚体法 → `references/incar.md` §三附、`workflows.md` §二十四/§二十六 |
| VASP 中 POTCAR 使用指南（Wiki 翻译，June976） | `articles/20261001-VASP中POTCAR使用指南.md`（原文 <https://www.jun997.xyz/2022/04/14/ba8ff0b84c20.html>，译自 <https://www.vasp.at/wiki/index.php/POTCAR> 与 `Available_PAW_potentials`） | 整理为 `references/potcar.md`（组装规矩、后缀官方定义、**按元素分区/按计算类型的选势建议**、版本差异与类氢势的坑） |
| 晶胞转换（spglib 用法，天帝君豪） | `articles/20261001-晶胞转换_天帝君豪的个人博客.md`（原文 <https://tiandijunhao.github.io/2020/04/25/jing-bao-zhuan-huan/>） | 用 `spglib.standardize_cell` 在原胞↔惯用胞间转换；三个脚本收于 `scripts/reference/cellconv_*.py`；工具条目见 `tools.md` §4.12 |
| 新手学习记录（VASP 的其它输出文件） | `articles/20261001-VASP学习记录_七_VASP的其它输出文件.md`（原文 <https://zhuanlan.zhihu.com/p/580994211>） | `CONTCAR`/`CHGCAR`/`OSZICAR`/`IBZKPT` 的用途与格式细节 → `references/onboarding.md` §九 |
| 提取 OUTCAR 中的能带数据（郭麒麟） | `articles/20261001-提取OUTCAR中的能带数据.md`（**用户粘贴正文，未提供链接**） | 三个 bash 脚本（本征值 / k 路径两种单位 / HOMO-LUMO）收于 `scripts/reference/outcar_*.sh`；方法见 `workflows.md` §二十 |
| 新手学习记录（VASP 的输出文件 OUTCAR） | `articles/20261001-VASP学习记录_六_VASP的输出文件OUTCAR.md`（原文 <https://zhuanlan.zhihu.com/p/579705300>） | `OUTCAR` 九个部分的逐段导航（含对称性分析、INCAR 回显、内存统计、应力块）与常用 `grep` → `references/onboarding.md` §9.1–§9.2 |
| VASP 输出文件 OUTCAR/OSZICAR（公众号《VASP学习交流》） | `articles/20261001-VASP输出文件OUTCAR_OSZICAR.md`（原文 <https://zhuanlan.zhihu.com/p/391279503>） | 一批查询命令（`grep TIT/ZVAL/ENMAX`、`grep LOOP+`/`LOOP`、`grep required`）与`E0` ↔ `energy(sigma->0)` 的对应 → `references/onboarding.md` §9.2 |
| STM 图像模拟的 Python 代码（`STM-2DScan.py`，@叠加态/lipai） | `articles/20261001-用vasp的输出文件PARCHG模拟STM图像的python代码.md`（原文 <https://zhuanlan.zhihu.com/p/538950799>） | 恒高/恒流/切面三种模式；恒流对表面落差大的体系可能不稳健；脚本收于 `scripts/reference/stm_2dscan.py`；说明见 `workflows.md` 第十九节 |
| 查看结构优化中的能量与力收敛（@叠加态/lipai） | `articles/20261001-VASP结构优化计算中查看能量和力收敛情况.md`（原文 <https://zhuanlan.zhihu.com/p/376360440>） | `EDIFFG` 只管非固定原子这条坑、`force_conv.sh`（终端画图）→ `workflows.md` 第一节；脚本收于 `scripts/reference/force_conv.sh` |
| 聊一聊结构优化（公众号《学术之友》，中科大无缺） | `articles/20261001-聊一聊结构优化.md`（原文 <https://mp.weixin.qq.com/s/uxynS5bzLfVpXHtEL7_3Zg>） | **分步优化（粗→精）两套参数**、对称性经验（TM 共面陷阱、P1 起点）、`POSCAR`/`CONTCAR` 差 > 1% 再优化、优化后指标清单 → `workflows.md` 第一节、`references/onboarding.md` §9.3 |
| 固定晶格优化（`constr_cell_relax.F` + `OPTCELL`） | <http://blog.wangruixing.cn/2019/05/05/constr/> | 刘锦程的博文；注意 `OPTCELL` 里 `0`/`1` 间不能有空格、上三角置零防转动有风险 → `errors.md` §4.7 |
| 计算大牛教你优化结构（PWmat 推广文，田洪镇） | `articles/20261001-计算大牛教你优化结构.md`（原文 <https://zhuanlan.zhihu.com/p/64738565>） | **11 条结构优化通用建议**（SCF 不收敛就别跑结构、金属加展宽/绝缘体加混合、大体系别做晶格优化、固定基体下层、HSE 先 PBE 预优化、适可而止的判据）→ `workflows.md` 第一节、`errors.md` §3.1；原文是 PWmat 的推广文，本库只提取通用部分并给出 VASP 对应手段 |
| VASP + VASPKIT 的 HSE06 能带教程（Vei Wang / 学术之友） | `articles/20261001-VASP计算杂化能带详细步骤教程.md`（原文 <https://mp.weixin.qq.com/s/v5pR3jffP5owYcUmWTLg5g>） | VASPKIT 八步流程（302/303 → 251 → 252）与官网「0-weight fake SC」混合 KPOINTS 做法 → `workflows.md` 第二十九节 |
| HSE06 经典教程（小木虫 / 科学网） | <http://muchong.com/bbs/viewthread.php?tid=4232787&fpage=1>；<http://muchong.com/bbs/viewthread.php?tid=6105659>；<http://blog.sciencenet.cn/blog-567091-732988.html> | 原文文末推荐的三篇 HSE06 教程（经典帖，年代较早，参数请与现行手册核对） |
| HSE06 计算带隙（公众号《VASP学习交流》） | `articles/20261001-HSE06计算带隙.md`（原文 <https://zhuanlan.zhihu.com/p/446453016>） | 可直接照做的「`scf/` + `hse/` 两目录」流程、**VASPKIT `251` 的交互步骤与推荐密度**（K-Mesh 0.02~0.04、K-path 0.04~0.06）、HSE 的 INCAR 增量 → `workflows.md` §29.1b、`references/incar.md` §二附 |
| VASP 计算能带结构（HSE 杂化泛函，四步路线） | `articles/20261001-VASP计算能带结构_HSE杂化泛函.md`（原文 <https://zhuanlan.zhihu.com/p/412484430>） | **`opt`→`gamma-scf`→`hse-scf`→`band`** 四步路线、`251` 路径精度 `0.03`/`0.02` 与「不可约 k 点约 20 个」、以及**一条真实报错**（非自洽步改了 `ENCUT` → `CHGCAR` 维数不同）→ `workflows.md` §29.4、`errors.md` §8.24 |
| VASPKIT 官方教程页 | <https://vaspkit.com/tutorials.html> | 官方 tutorials（含**单层 MoS₂ 杂化泛函**示例）；与本节 HSE 流程互为参考 |
| VASP vaspkit 画 HSE06 能带图（本人文章） | `articles/20261001-VASP_vaspkit_画_HSE06_能带图.md`（原文 <https://zhuanlan.zhihu.com/p/590781664>） | **每条 VASPKIT 命令连参数**（`1 101 LR`/`1 102 2 0.03`/`303`/`251 2 0.04 0.06`/`252 0`）、`ALGO=ALL` 变体、`NPAR×KPAR` 规则、**`~/.vaspkit` 必须配 `PYTHON_BIN`/`PLOT_MATPLOTLIB`** → `workflows.md` §29.5；参数语义 → `references/incar.md` §二附 |
| VASP vaspkit Materials Studio DFT+U 画能带和 DOS 图（本人文章） | `articles/20261001-VASP_vaspkit_Materials_Studio_DFT_U_画能带和DOS图.md`（原文 <https://zhuanlan.zhihu.com/p/579449491>） | **DFT+U 六参数**（`LDAU/LDAUTYPE/LMAXMIX/LDAUL/LDAUU/LDAUJ`）、AFM 的 `MAGMOM` 写法、`vaspkit 3 303` / `21 211` / `11 111` 命令、UO₂ 的带隙与 DOS 分析（1.8676 vs 文献 1.95 eV）→ `workflows.md` 第三十节、`references/incar.md` §二附2 |
| VASP vaspkit Origin 画态密度（DOS）图（本人文章） | `articles/20261001-VASP_vaspkit_Origin_画态密度_DOS_图.md`（原文 <https://zhuanlan.zhihu.com/p/574160228>） | **Origin 路线**：`vaspkit 11 111/114/115`（`tdos.dat`/`PDOS_SUM.dat`/`PDOS_USER.dat`）→ Origin 四步美化；DOS 步要**把 KPOINTS 格点翻倍**、**费米能级默认已在 0**；另有「迭代弛豫到一步收敛」与多条参数语义 → `workflows.md` §4.2、第一节，`references/incar.md` §二附3 |
| VASP vaspkit Origin 画能带图（本人文章） | `articles/20261001-VASP_vaspkit_Origin_画能带图.md`（原文 <https://zhuanlan.zhihu.com/p/564983969>） | **Origin 画能带 8 步**（用 `KLABELS` 把 X 轴刻度改成高对称点）、`vaspkit 3 302/303` + `21 211` → `BAND.dat`、**带隙查 `BAND_GAP`**（MnPS₃ 0.6491 eV）、二维铁磁案例的 `MAGMOM` 取法 → `workflows.md` 第三节 |
| 画能带和 DOS 图 -- Python 包（本人文章） | `articles/20261001-画能带_Band_和态密度_DOS_图--Python包.md`（原文 <https://zhuanlan.zhihu.com/p/580857656>） | **`vaspvis` 与 `pymatgen` 的 API 速查**（8 + 5 个示例，含 `BSDOSPlotter` 联合图）、两包对输入文件的不同要求、**`KPOINTS` 里 `GAMMA`→`\Gamma` 必须全部同时改** → `workflows.md` 第三节 |
| VASP+vaspkit 计算能带+态密度（社区教程） | `articles/20261001-VASP_vaspkit计算能带结构_态密度.md`（原文 <https://zhuanlan.zhihu.com/p/526969630>） | 三步 INCAR 模板（`scf` 用 `ICHARG=2`+`LVTOT`，`band`/`dos` 用 `ICHARG=11`）、**`vaspkit 211` 与投影能带 `212`~`216`**、DOS 的 KPOINTS 取 scf 的 2 倍（20~40）、以及评论区三条高频疑问的答案（`ISTART`/费米能级是否归零/`LCHARG`）→ `workflows.md` 第三节 |
| VASP 之铁电极化计算（社区教程） | `articles/20261001-VASP之铁电极化计算.md`（原文 <https://zhuanlan.zhihu.com/p/358517335>） | **FE − NP 两相法**（`LCALCPOL`/`DIPOL`/`IDIPOL`）、⚠️ **不要用 `LDIPOL=.T.`**（评论区更正）、参考相非半导体的镜像法/线性插值法、L-G 系数与 `Tc`（AIMD / **`mpiPyMC`**）→ `workflows.md` 第三十一节、`references/incar.md` §二附4 |
| VASP 如何计算居里温度？（知乎问答，4 个回答） | `articles/20261001-VASP如何计算居里温度_-_知乎.md`（原文 <https://www.zhihu.com/question/386477636>） | **DFT 求 `J`（FM/AFM 能量差）+ 非共线磁性设置**、三个 MC 工具（`mcsolver`/MTC/公众号代码）、`1 meV ≈ 11.6 K`、由 `C`/`χ` 峰值定 `Tc`、✂️ **VASP 本身不算 `Tc`** → `workflows.md` 第三十二节 |
| Error EDDDAV: Call to ZHEGV failed 的磁性解决方案 | `articles/20261001-VASP_Error_EDDDAV_Call_to_ZHEGV_failed_的磁性解决方案.md`（原文 <https://zhuanlan.zhihu.com/p/351808487>） | **用 `AMIX` 治 ZHEGV**：金属 `0.02`/半导体 `0.2`、⚠️ **AMIX 过大→收敛到更高磁态**、`AMIX_opt = AMIX_current × Γ`（Γ 取 `average eigenvalue`）vs 直接扫描、`SYMPREC` 这条另类成因 → `errors.md` §2.6、`references/incar.md` 混合参数行 |
| 第一性原理‖VASP 计算自旋轨道耦合与相关参数 | `articles/20261001-第一性原理_VASP计算自旋轨道耦合与相关参数.md`（原文 <https://zhuanlan.zhihu.com/p/538131764>） | **SOC 参数与 MAE 流程**：`LSORBIT` 只对 PAW 有效、`SAXIS` 默认 `(0⁺,0,1)`、两种指方向的写法、`NBANDS`×2 / `ISYM=-1` / `GGA_COMPAT=.FALSE.`、用 `E_soc` 验证 → `workflows.md` 第三十三节、`references/incar.md` §二附5 |
| VASP+SOC 自旋轨道耦合效应的计算 | `articles/20261001-VASP_SOC自旋轨道耦合效应的计算.md`（原文 <https://zhuanlan.zhihu.com/p/572584164>） | 操作层面补充：⚠️ **SOC 必须用 `vasp_ncl` 提交**（从写下 `LSORBIT` 的那一步起）、两种流程变体、非共线 `MAGMOM` 写法（每原子 3 个数）、对称性报错的三条办法（含 **`SYMPREC=1E-8`**）→ `workflows.md` §33.6 |
| VASP 中的非线性磁性计算总结 | `articles/20261001-VASP中的非线性磁性计算总结.md`（原文 <https://zhuanlan.zhihu.com/p/586969248>） | **`SAXIS` 的 α/β 角公式与旋转矩阵**、两种转向方式在数学上的区别（**写法 B 本质是共线 + 整体可转向 → MAE 更优**）、`MAGMOM` 只在 `ICHARG=2` 时生效、非共线的官方两步法（先非磁性）→ `workflows.md` §33.7 |
| vasp 磁各向异性计算（MAE） | `articles/20261001-vasp_磁各向异性计算.md`（原文 <https://zhuanlan.zhihu.com/p/436260128>） | **磁矩单位（`μ_B`，共线时 = 上下自旋电子数之差）**、**`m`/`s` 的泡利矩阵视角**（`MAGMOM = 0 0 m` 不表示指向 z）、一套可抄的 MAE 两步 INCAR（含 **`LORBMOM`**、`NBANDS` 取法、`MAGMOM` 混写 `24*0`）→ `workflows.md` §33.8。⚠️ 该文作者自述不擅长磁性，本库按参数示例收录 |
| 加快磁性材料电子迭代收敛经验小结（学术之友，无缺） | `articles/20261001-加快磁性材料电子迭代收敛经验小结.md`（原文 <https://mp.weixin.qq.com/s/CsHrfXkSD0vtdHTp5_gNMA>） | ⭐ **`EENTRO/原子数` 判断金属/半导体**（>1 meV 金属 / <0.1 meV 半导体）、**`ALGO` 五档的 `IALGO` 对应与各自的坑**（含 `WEIMIN=0`、`NSIM`）、**`TIME` 的 1.2× 优化法**、**磁性 MIXING 实战**（线性混合、`AMIX` 0.02/0.2、**默认 0.4 过大**、扫描优于手册公式）→ `workflows.md` §一、`errors.md` §2.1、`references/incar.md` §二附6 |
| 如何在 VASP 中约束磁矩（本人文章，译自 Tharindu 博客） | `articles/20261001-如何在_VASP_中约束磁矩.md`（原文 <https://zhuanlan.zhihu.com/p/716322801>；英文原帖 <http://thauwa.me/2023/12/08/how-to-constrain-magnetic-moments-in-vasp/>） | **`I_CONSTRAINED_M` 1/2/4 的区别**、**必须走非共线（`vasp_ncl`）**、`M_CONSTR` 要与 `MAGMOM` 一致、**`RWIGS`/`LAMBDA` 的收敛测试**、⚠️ **总能要减 `E_p`**、用 `LORBIT=11` 验证磁矩、脚本生成磁矩串 → `workflows.md` 第三十四节、`references/incar.md` §二附7、`errors.md` §七 |
| VASP 中的磁性设置（本人文章） | `articles/20261001-VASP中的磁性设置.md`（原文 <https://zhuanlan.zhihu.com/p/716023597>） | **磁性设置总纲**：`T_C`/`T_N`/居里定律/居里-韦斯、**只设 `ISPIN=2` 时每原子默认磁矩 `1`**、**初值取预期 × 1.2~1.5**、**磁态依赖初值（局部极小）**、`MAGMOM` 三种写法（含**反斜杠续行**）、O₂ 的洪特规则例子、⭐ **「非磁起步」总时间反而多 22.5% 的实测** → `workflows.md` 第三十五节、`references/performance.md`、`references/incar.md` 的 `MAGMOM` 行 |
| VASP 的光学性质计算及 vaspkit 的安装与使用（社区教程） | `articles/20261001-VASP_的光学性质计算及_vaspkit_的安装与使用.md`（原文 <https://zhuanlan.zhihu.com/p/26836978>） | **`LOPTICS` 光学流程**（`NBANDS`×2、`NPAR` 调小、`ISYM=0`）、`OUTCAR` 实部/虚部段的**「独立粒子、无局域场」前提**、VASPKIT 后处理（老版 `51` + `REAL.IN`/`IMAG.IN` → 五个 `.dat`）与**新版流程差异**、**VASPKIT 安装步骤**（`Makefile`/`make`、VASP 4.x 设 `vasp5=.false.`）→ `workflows.md` 第三十六节、`references/incar.md` §二附8 |
| VASP 计算光学性质（公众号《计算物理》，InSe 实例） | `articles/20261001-VASP计算光学性质.md`（原文 <https://zhuanlan.zhihu.com/p/580548050>） | ⭐ **`CSHIFT = 0.1`**、`NEDOS` 控频率网格、`NBANDS = 120` 的量级、**`ALGO=Exact` 官方推荐但实测「算不动」**、**光学对带隙极敏感 → 一般用 HSE**、**「直接在 SCF 里加光学参数」与「另建目录」差别很小**、**现代 VASPKIT 用 `711` → `ABSORPTION.dat`** → `workflows.md` §36.7、`references/incar.md` §二附8 |
| vasp 计算光学性质教程（学术之友转载贺勇博客） | `articles/20261001-vasp计算光学性质教程.md`（原文 <https://mp.weixin.qq.com/s/waTzUdwZZUqbe1e9VtDX_g>；作者个人博客 <https://yh-phys.github.io>） | ⭐ **三步流程与各自 KPOINTS**（`13 13 1` → `25 25 1` → `29 29 1`）、**`NBANDS` 取自洽默认值的 2~3 倍 + k 网格加密**、`vaspkit 71→711`（及 `716`/`717` JDOS）、**吸收系数单位 `cm⁻¹`**、⚠️ **VASPKIT 自己提示「该模块不适用于低维材料」而教程用二维 InSe**、2D 光学理论出处 `DOI: 10.1021/acsnano.9b06698` → `workflows.md` §36.8、参考脚本 `scripts/reference/optics_extract_awk.sh` |
| VASP vaspkit 光学性质｜1（本人文章） | `articles/20261001-VASP_vaspkit_光学性质_1.md`（原文 <https://zhuanlan.zhihu.com/p/625881446>） | ⭐⭐ **低维材料要用 `710`（2D，输出 `*_2D.dat`），`711` 是三维的**——**这解决了 §36.8 里「711 不适用于低维材料却仍被使用」的矛盾**；`NBANDS` 默认值公式、**`CSHIFT` 默认 `0.1`**、`OPTCELL` 必须重编译 VASP 的前提、**二维吸收谱「带隙以下仍有吸收」这一未决现象** → `workflows.md` §36.9、`references/incar.md` §二附8 |
| VASP vaspkit 光学性质｜2（本人文章，理论篇） | `articles/20261001-VASP_vaspkit_光学性质_2.md`（原文 <https://zhuanlan.zhihu.com/p/669635613>） | ⚠️ **只含带间直接跃迁 ⇒ 半导体/绝缘体适用，金属不适用**、**五个导出量的完整公式**（`n`/`k`/`α`/`L`/`R`）、**2D 该用光学电导率 `σ_2D = L·σ_3D`**（含 `A+T+R=1` 与 `A≈Reσ_2D/(ε₀c)`）、**DFT→GW→GW-BSE 的方法层级**、**GW-BSE 四步 INCAR**（`ALGO=EXACT/GW0/BSE`、`WAVEDER`/`WAVECAR.chi`）、石墨烯 `710` 流程（纵轴 % / `σ_2D/σ₀`）→ `workflows.md` §36.10–36.11、`references/incar.md` §二附8、脚本 `scripts/reference/optical_plot_pdf.py` 等 |
| TDEP 计算高温声子谱（天帝君豪博客） | `articles/20261001-TDEP计算高温声子谱_天帝君豪的个人博客.md`（原文 <https://tiandijunhao.github.io/2020/06/28/tdep-ji-suan-sheng-zi-pu/>） | ⭐ **有限温度声子的 TDEP 路线**：两条数据来源（LAMMPS+机器学习势 / VASP AIMD 的 `IBRION=0` INCAR）、**六个 `infile.*` 输入文件**、`extract_forceconstants -rc2/-rc3` → `phonon_dispersion_relations` → `lineshape` 命令链、高对称路径文件写法、⚠️ **`infile.ssposcar` 必须与 MD 超胞一致** → `workflows.md` 第三十七节、脚本 `scripts/reference/grep_dump*.sh`、`lineshape_sqe_plot.py` |
| vasp 计算声子谱教程（学术之友／贺勇） | `articles/20261001-vasp计算声子谱教程.md`（原文 <https://mp.weixin.qq.com/s/E5NBkgpSMt-qVzHCulU7hw>；作者博客 <https://yh-phys.github.io>） | **直接法 vs DFPT 的原理与取舍**、**phonopy 源码安装**、**`IBRION=8` 让 VASP 自己算 Hessian**、`phonopy -d` 产物（`SPOSCAR` vs `POSCAR-00x`）如何区分、`band.conf`/`PBAND.dat` 细节、⭐ **虚频判读经验（Γ 点小虚频 + 二维材料）** → `workflows.md` 第三十八节、§六 指针 |
| vasp+phonopy 计算声子谱（June976） | `articles/20261001-vasp_phonopy计算声子谱.md`（原文 <https://www.jun997.xyz/2022/07/14/276373048e9d.html>） | ⭐ **两条路线的产物对照**（`phonopy -f` → **`FORCE_SETS`** vs `--fc` → **`FORCE_CONSTANTS`**）、**支数规则 `m` 声学 + `m(n-1)` 光学**、⚠️ **有限位移单点 `ISIF` 不能为 0**、⚠️ **`IBRION=8` 要关并行参数**、**`ISYM=2` 可减少位移数**、`band.conf` 进阶（`BAND_POINTS`/`BAND_LABELS`/逗号分段）与 **`phonopy -p -s` 直接出图** → `workflows.md` §38.9、`errors.md` §3.3 |
| 基于 Shell+VASP 实现自动计算 DFT+U 中的 U 值（SuYun Wang） | `articles/20261001-基于Shell_VASP实现自动计算DFT_U中的U值_附源代码.md`（原文 <https://zhuanlan.zhihu.com/p/422716387>） | ⭐ **线性响应法求 `Ueff`**（官方教程的自动化版）：**`LDAUTYPE = 3`**、**扫描 `U ∈ [-0.2, 0.2]` 步长 `0.05`**、每个 U 值做 NSCF+SCF、`output.wsy` 最后一行即 `U`；⚠️ **赝势不同结果不同**；⚠️ 自动生成的 INCAR **`MAGMOM` 要自己设** → `workflows.md` 第三十九节、`references/incar.md` 的 `LDAUTYPE` 行、脚本 `scripts/reference/vasp_Ueff-1.0.wsy` |
| VASP 计算之 DFT+U（转载：VASP学习交流） | `articles/20261001-VASP计算之DFT_U.md`（原文 <https://zhuanlan.zhihu.com/p/412474991>） | ⭐⭐ **判断 `U` 是否合适的五项判据**（磁矩 / 磁基态 / `Tc`·`Tn` / 能带定性 / 对关心的性质有多敏感）、⚠️ **别追求能隙吻合**、**PBE+U 仍写 `LDAU` 系列（类型由赝势决定）**、**d+f 混合体系按元素逐个给**、⚠️ **`Ueff = U − J` ⇒ 跨 `U`/`J` 比总能无意义**、加 U 机理（Slater 积分/屏蔽/`Edc`）→ `workflows.md` 第四十节、`errors.md` §七 |
| 带你解读 DFT+U 计算，如何加 U（迈高科技 / MatCloud+） | `articles/20261001-带你解读DFT_U计算_如何加U.md`（原文 <https://zhuanlan.zhihu.com/p/502440652>） | ⭐ **`U` 的典型取值范围**（过渡族金属 `≈3.0 eV`、多在 `2~4`；稀土氧化物 `4~7 eV`；`J` 比 `U` 小一个量级）、**DFT+U 的思想框架**（轨道分成两个子体系 / 能量-占据数关系）、**带隙问题实例**（Si/GaAs 偏小；⚠️ **Ge/InN 被算成金属**）、⚠️ **原文 La/S 示例的参数顺序写反（应为 `LDAUL = 3 -1`）**、两个评论问答（不加 U 的场合 / 优化阶段要不要加 U）→ `workflows.md` §40.6–40.8、`errors.md` §七 |
| 铁电参考文献（原文所引） | <https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.117.097601> | *Ferroelectricity and Phase Transitions in Monolayer Group-IV Monochalcogenides*, PRL 117 (2016) |
| 并行参数测算参考（中科大超算） | <https://scc.ustc.edu.cn/zlsc/jsrj/201810/W020181016364157753668.pdf> | 张文帅老师的 VASP 并行测算结果，可作为选参数的对照 |
| 找初始结构的数据库合集 | Materials Project <https://materialsproject.org/>；AFLOW <http://aflowlib.org/>；**COD**（晶体学开放数据库）<http://www.crystallography.net/cod/>；**Topological Quantum Chemistry** <https://topologicalquantumchemistry.org/>；**Materiae**（中科院物理所）<http://materiae.iphy.ac.cn/> | 原文（POSCAR 教程）推荐的五个来源；MP 与 AFLOW 在本库另有条目（AFLOW 还能提供**标准基矢原胞**，见 §4.11） |
| 晶胞变换（手动转换矩阵）教程 | <https://yyyu200.github.io/DFTbook/blogs/2019/04/07/TransCell/> | 单胞 ↔ 标准原胞的矩阵变换推导（原文附录 2 引用） |
| 弹性模量各向异性三维图示 | <http://jerkwin.github.io/2014/04/17/材料弹性模量各向异性的三维图示方法/> | 弹性矩阵 → 各向异性曲面的作图与理论（原文附录 3 引用） |

---

## 七、收录自查（新增脚本/工具时）

- [ ] 速查表（第一节）加了一行：名称 / 类型 / 一句话功能 / 输入→输出 / 依赖 / 指向正文条目
- [ ] 正文条目写全：**功能 → 输入输出 → 依赖 → 头部参数或命令 → 关键注意点（坑） → 来源链接 → 对应 `workflows.md` 章节**
- [ ] 若来自某篇文章，在「来源」里写明 `articles/<文件名>` 可回溯
- [ ] 若这是某个自带脚本的替代/前身，在第五节或对应 `scripts/README.md` 表格里注明关系（planned / 已落地）
- [ ] 涉及第三方代码时保留原作者署名与仓库链接（尊重来源，也便于日后核对版本）

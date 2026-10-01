# 参考脚本库（`reference/`）

本目录存放**从文章里收集到的脚本**，定位是"**查参考**"，不是"拿来就跑"：

- **原样收集**：内容尽量保持文章原貌，并注明原作者/来源链接；网页代码块**经常丢失换行与缩进**，
  这类脚本只能读逻辑，不能直接执行。
- **不做验证**：本目录的脚本**没有** `--selftest`、**不保证可运行**。
  需要能跑的工具，请看 `scripts/` 下的**自带脚本**（`parse/`、`post/` 等，带自检）。
- **不与 `tools.md` 重复**：某个脚本的**功能说明**登记在 `references/tools.md`（外部脚本/程序速查）；
  本目录只负责放**源码文本**，并指向对应条目。

## 目录约定

- 文件名与原文一致（`idealdeform.sh`、`chgdiff.pl`、`vtotav.f`、`xvg.py`…）；
- 每个脚本文件**头部加注释**：来源文章（`articles/<文件名>`）、原文链接、用途、依赖，
  以及**抓取质量说明**（是否丢缩进、是否与原网页一致）；
- 收录后在下面的索引表里**加一行**。

## 索引

| 脚本 | 语言 / 用途 | 来源文章 | 状态 |
| --- | --- | --- | --- |
| `snap_dataset.py` | Python：多帧 `vasprun.xml` → FitSNAP 数据集 JSON | `articles/20261001-vasprun_xml_to_json_file_天帝君豪的个人博客.md` | **已收录**（原网页丢换行） |
| `optics_extract_awk.sh` | awk：从 `vasprun.xml` 抽介电函数实部/虚部 → `REAL.in`/`IMAG.in` | `articles/20261001-vasp计算光学性质教程.md` | **已收录**（VASPKIT 1.0+ 已不需要此步） |
| `optical_plot_pdf.py` | Python：把 VASPKIT 输出的 ABSORPTION.dat / REFRACTIVE.dat / REFLECTIVITY.dat / EXTINCTION.dat 画成四联图 PDF（Si 的 GW-BSE 例子） | `20261001-VASP_vaspkit_光学性质_2.md` | **已收录**（⚠️ 原文粘连，本库重排、未运行验证） |
| `graphene_absorption_plot.py` | Python：读 ABSORPTION_2D.dat（能量 + xx + yy 三列）画二维材料的光吸收谱（纵轴 %） | `20261001-VASP_vaspkit_光学性质_2.md` | **已收录**（⚠️ 原文粘连，本库重排、未运行验证） |
| `graphene_optical_conductivity_plot.py` | Python：读 REAL_/IMAG_OPTICAL_CONDUCTIVITY_2D.dat 画二维材料光学电导率（纵轴 sigma_2D/sigma_0） | `20261001-VASP_vaspkit_光学性质_2.md` | **已收录**（⚠️ 原文粘连，本库重排、未运行验证） |
| `grep_dump.sh` | 把 LAMMPS 的 dump.positions/dump.forces 转成 TDEP 需要的 infile.positions/forces/stat | `20261001-TDEP计算高温声子谱_天帝君豪的个人博客.md` | **已收录**（⚠️ 原文粘连，本库重排、未运行验证） |
| `grep_dump2.sh` | 同上，改用 gawk/tail 处理并排除第一帧 | `20261001-TDEP计算高温声子谱_天帝君豪的个人博客.md` | **已收录**（⚠️ 原文粘连，本库重排、未运行验证） |
| `lineshape_sqe_plot.py` | 读 TDEP 的 outfile.sqe.hdf5 画声子线型/动态结构因子 S(q,E) 热图 | `20261001-TDEP计算高温声子谱_天帝君豪的个人博客.md` | **已收录**（⚠️ 原文粘连，本库重排、未运行验证） |
| `vasp_Ueff-1.0.wsy` | sh：线性响应法求自洽 Hubbard U 的交互式驱动（0 生成输入 / 1 DFT / 2 +U 的 NSCF+SCF / 3 提取 Ueff） | `20261001-基于Shell_VASP实现自动计算DFT_U中的U值_附源代码.md` | **已收录**（⚠️⚠️ 原导出丢全部换行，**未重排、不可直接运行**；可运行版见 <https://github.com/Code-WSY/Code-WSY>） |
| `ising_mc_tc.py` | Python（numpy+matplotlib）：二维 Ising 模型的 Metropolis 蒙特卡洛，由热容/磁化率峰值定相变温度 | `articles/20261001-VASP如何计算居里温度_-_知乎.md` | **已收录**（原网页压成单行且丢空格，**不能直接运行**） |
| `force_conv.sh` | bash+gnuplot：汇总每个离子步的能量与**非固定原子**的最大受力，并在终端画 ASCII 曲线 | `articles/20261001-VASP结构优化计算中查看能量和力收敛情况.md` | **已收录**（原网页压成单行；依赖 gnuplot） |
| `stm_2dscan.py`（`STM-2DScan.py`） | Python：CHGCAR/PARCHG → STM 二维图（恒高 / **恒流** / 切面） | `articles/20261001-用vasp的输出文件PARCHG模拟STM图像的python代码.md` | **已收录**（原网页把脚本压成单行；作者 @叠加态，GPL） |
| `outcar_bands.sh` / `outcar_kpath.sh` / `outcar_homo_lumo.sh` | bash：从 `OUTCAR` 提本征值（逐带）/ k 路径（两种单位）/ HOMO-LUMO | `articles/20261001-提取OUTCAR中的能带数据.md`（**用户粘贴正文**，原作者 郭麒麟） | **已收录**（未运行验证；固定列宽等坑见文件头） |
| `cellconv_read_poscar.py` / `cellconv_reposcar.py` / `cellconv_run.py` | Python：用 **spglib** 在原胞 ↔ 惯用胞之间转换（`standardize_cell`） | `articles/20261001-晶胞转换_天帝君豪的个人博客.md` | **已收录**（原网页压成单行；`read_poscar.py` 对多元素体系有已知限制，见文件头） |
| `kpoint_encut_test.sh` | bash：自动扫 k 点间距与 ENCUT 做收敛性测试 | `articles/20261001-自动进行K点和ENCUT测试bash脚本.md` | **已收录**（网页带行号且丢空格，已做最小修复并在文件头列明） |
| `chgdiff.pl` | Perl：两个 `CHGCAR` 相减做差分 | `articles/20260930-差分电荷密度和平面平均差分电荷密度计算教程.md` | **已收录**（原网页丢换行） |
| `vtotav.f` | Fortran：沿 X/Y/Z 平面平均（改版读 `CHGCAR`） | 同上 | **已收录**（原网页丢换行；头注释用 `C` 固定格式写法） |
| `crecip.py` | Python：实空间基矢 → 倒格矢 | `articles/20260930-VASP计算二维材料的载流子迁移率.md` | **已收录**（原网页丢换行；python2 风格） |
| `xvg.py` | Python：画 GROMACS 的 `.xvg` | `articles/20260930-用强大的GROMACS分析工具分析VASP的动力学结果.md` | **已收录**（原网页带行号，已剥除；缩进仍丢） |
| `idealdeform.sh` | bash：准静态拉伸/剪切的应变序列 | `articles/20260930-计算应力应变曲线脚本idealdeform_sh使用指南.md` | **无法收录**（原文只给参数说明，未给源码；功能见 `tools.md` 三.1） |
| `vaspeqstress.sh` | bash：迭代施加任意外压 | `articles/20260930-vasp定压计算脚本vaspeqstress_sh使用教程.md` | **无法收录**（原文只给参数说明，未给源码；功能见 `tools.md` 三.2） |
| `mobility.sh` | bash：二维迁移率批量应变目录 | `articles/20260930-VASP计算二维材料的载流子迁移率.md` | **已收录**（配套作业脚本见 `mobility.pbs`；两者均丢换行） |
| `vasp_py_pandas.py` / `vasp_py_numpy.py` | Python：从 `OUTCAR` 提取任意量并出图（两条实现路线） | `articles/20261001-VASP_Python_数据挖掘_1.md`、`…_2.md` | **已收录**（两文代码块均丢换行） |
| `elastic_3d.py` / `elastic_2d.py` | Python：弹性矩阵 → 各向异性 `E`/`ν` 图 | `articles/20261001-VASP计算材料的弹性矩阵和杨氏模量.md` | **已收录**（原网页丢缩进） |
| `stm_crop.py` / `stm_gif.py` | Python：裁白边 / 合成 STM 动态图 | `articles/20261001-VASP_vaspkit_STM_模拟.md` | **已收录**（原文压成单行） |
| `extract_disp.py` / `extract_force.py` | Python：ALAMODE 从 MD 提取位移/力 | `articles/20261001-alamode_scph计算高温声子谱_天帝君豪的个人博客.md` | **无法收录**（原文只给文件名，未给源码；已登记在 `tools.md` 四.7） |

## 新增参考脚本清单

- [ ] 文件头写明来源（文章文件名 + 原文链接）与抓取质量说明
- [ ] 在本文索引表加一行（脚本 / 语言用途 / 来源文章 / 状态）
- [ ] 若已有对应的自带脚本或 `tools.md` 条目，注明关系

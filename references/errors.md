# VASP 报错诊断参考

本文件用于「VASP 报错诊断」任务：用户粘贴 VASP 的报错信息 / 输出日志片段，据此定位错误发生的位置、原因，并给出可执行的解决方案。

**快速检索**：若下方目录和条目没有直接命中，先运行
`python scripts/search_kb.py "<报错关键词>"`——它会检索本文件、`workflows.md` 和 `articles/` 用户文章知识库，返回相关片段，缩小定位范围。

## 目录

1. [诊断流程](#诊断流程按此顺序执行)
2. [一、读入与初始化阶段](#一读入与初始化阶段)：1.1 INCAR / 1.2 POSCAR / 1.3 KPOINTS / 1.4 POTCAR / 1.5 复用旧文件
3. [二、SCF（电子自洽）阶段](#二scf电子自洽阶段)：2.1 不收敛 / 2.2 NBANDS / 2.3 非埃尔米特 / 2.4 NaN
4. [三、离子步阶段](#三离子步阶段)：3.1 不收敛 / 3.2 线搜索 / 3.3 虚频
5. [四、运行环境与编译](#四运行环境与编译)：MPI / 段错误 / 内存 / Intel 环境变量 / makefile.include / FFTW / BLAS-LAPACK / 动态库 / 固定轴优化
6. [五、ALAMODE 相关](#五alamode-相关声子--热输运)：声子 / 热输运
7. [六、LOBSTER / COHP 相关](#六lobster--cohp-相关成键分析后处理)：无输出 / 元素 / 毛刺
8. [七、高频注意事项](#七高频注意事项防患)
9. [八、社区错误集精选](#八社区错误集精选外部来源)：SGRCON / PRICEL / NMAX_DEG / INCAR 长行截断 / HSE NaN 等

**相关文件**：定位到「要用某个脚本 / 工具」时，去 `references/tools.md` 查功能与入口——第三方脚本（`chgdiff.pl`、`vtotav.f`、`idealdeform.sh`、`vaspeqstress.sh`、`VASP2GRO`、`MEPSearcher`…）、外部程序（VASPKIT / VESTA / GROMACS）与自带 `scripts/` 都在那里登记。

---

## 诊断流程（按此顺序执行）

1. **确认 VASP 版本与运行方式**：`VASP 5.x / 6.x`、`vasp_gam/vasp_std`、是否 MPI（`mpirun -np N vasp_std`）。同一条报错在不同版本/编译选项下含义可能不同。
2. **定位报错发生在哪个阶段**：从 `OUTCAR` / `stdout` 末尾的报错和它之前最近完成的模块判断——
   - 读入与初始化阶段（读 INCAR / POSCAR / KPOINTS / POTCAR）
   - SCF（电子自洽）阶段
   - 离子步（力、晶胞）阶段
   - 后处理 / 属性计算阶段
   - MPI 调度与编译阶段

   **源码级阶段地图**（VASP 主程序 STEP 注释，用来判断「报错停在哪一段」）：
   读入 `POSCAR`/`POTCAR`/`INCAR`/`KPOINTS` → 对称性初始化（STEP 17）→ FFT 网格与数组/波函数分配（20–29）→ 读 `WAVECAR`（30）→ 初始电荷密度（38）→ Ewald 能量/力/应力（39）→ **主循环（42）**：
   电子步最小化（45，`NELM`/`EDIFF`）→ 占据数与 `NBANDS` 检查（46）→ 离子移动（47）→ 力与应力（48）→ 弛豫算法（54，`IBRION`）→ 写 `CONTCAR`/`CHG`（64–66）→ `WAVPRE` 波函数预测（68）→ 实空间投影与 Gram-Schmidt（72–73）→ 更新 `WAVECAR`（75）。
   主循环之后：写 `CHGCAR`（80）→ 本征值（81）→ 光学矩阵元（83）→ ELF（86–87）→ STM（88）→ 总 DOS（89）。
   报错落在哪一段，就先查那一段的输入与参数（来源：`articles/20261001-VASP的计算流程.md`）。
3. **区分致命错误与警告**：`Error` / `Fatal error` / `Segmentation fault` 为致命；`WARNING` / `... exceeded ...` 若伴随计算继续则先评估影响，不要一律当致命处理。
4. **用关键词匹配下方分类**：取报错中稳定、可搜索的关键片段（例如 `RMM-DIIS`、`NBANDS`、`Sub-Space-Matrix`）定位到具体条目。
5. **给出方案时带上验证**：说明改哪个文件哪个参数、为什么，并提示改完重跑后如何确认（如检查是否还出现同一条报错、看 OUTCAR 是否推进到下一阶段）。

> 使用原则：把下面当作**查表 + 推理**的参考，不要机械复读。如果用户给的报错在表中没有直接命中，按「阶段定位 → 成因分类 → 排查」的通用路径给出结构化方案。

---

## 一、读入与初始化阶段

### 1.1 INCAR 读取/解析错误

- **典型报错片段**：`Error reading item 'XXX' from file INCAR`、`Could not read file INCAR`、`Fatal error: no INCAR file`。
- **成因**：
  - 参数名拼写错误或该 VASP 版本不支持（如把 `PREC` 写成 `PREE`）。
  - 参数取值类型/取值非法（如给整数参数填了字符串、`ENCUT=0`、`NELM=0`）。
  - 文件编码（UTF-8 BOM / CRLF / 不可见字符）或括号、引号残留。
  - INCAR 文件缺失、路径不对。
  - **行首用了两个 Tab**：VASP 会**直接忽略该参数**（一个 Tab 无碍，双 Tab 后再加空格也无效）——这是「某参数怎么改都不生效」「ENCUT 扫描结果完全一样」的经典来源（VASP 5.3/5.4 实测）。
  - **同一参数在 INCAR 里写了多次**：VASP 只取**第一次**出现的值，后面的被忽略（长 INCAR 极易重复）。
- **定位**：报错会直接点出 `XXX` 是哪个标签；`OUTCAR` 顶部会列出被读取的 INCAR 内容。
  - 没有任何报错、但参数像没生效时：先查双 Tab，再查同名参数是否重复（VASP 只认第一个）。
- **方案**：
  - 用 `grep -n "XXX" INCAR` 找到该行，对照官方标签拼写修正；类型错误改取值。
  - 去掉 BOM/不可见字符：`sed -i '1s/^\xEF\xBB\xBF//' INCAR`，统一换行为 `\n`。
  - 确认工作目录下确实存在 INCAR 且文件名大小写正确。

### 1.2 POSCAR 结构错误

- **典型报错片段**：`Error reading item 'POSCAR'`、`Fatal error: LATTYP: Could not determine Bravais lattice`、`Fatal error: Cell volume <= 0`、`Fatal error: symmetry equivalent atoms`。
- **成因**：
  - POSCAR 第 1 行注释、第 2 行比例系数、晶胞矩阵、原子数、坐标行数不一致。
  - 直接坐标系（`Direct`）下坐标不在 `[0,1)` 或越界（会提示 check）。
  - 晶胞矩阵线性相关 / 体积 ≤0（比例系数写错、行缺失）。
  - 对称性问题：选择性动力学（`Selective dynamics`）与对称设置冲突、自旋磁矩破坏了对称性导致 `symmetry equivalent atoms`。
- **定位**：从 `stdout`/`OUTCAR` 看是哪一行读取出错；用 `python -m pymatgen.cli...` 或直接看 POSCAR 行列数核对。
- **方案**：
  - 用 pymatgen/ASE 读一次验证：`python -c "from pymatgen.core import Structure; s=Structure.from_file('POSCAR'); print(s)"`，读不出即格式问题。
  - 坐标系超出 [0,1) 时用 `--wrap` 或 `ase` 的 `wrap` 修正；晶胞矩阵问题重新生成 POSCAR。
  - `symmetry equivalent atoms`：检查是否开启 `ISYM=-1` 或自旋设置（`ISPIN`/`MAGMOM`/`MAGMOM` 对称破坏），必要时设 `ISYM=0`，或调整原子占位/位置。

### 1.3 KPOINTS 错误

- **典型报错片段**：`Error reading KPOINTS`、`Fatal error: unable to allocate ...`（网格过大）、band 路径下 `error in KPOINTS`。
- **成因**：格式（模式行、行数）不对；Monkhorst-Pack 网格过大导致内存不足；band 模式沿高对称路径的分数坐标/端点错误。
- **方案**：
  - 自洽用 `Automatic` + 整数网格；band 用 `Line-mode`，端点分数坐标用 pymatgen `HighSymmKpath` 自动生成，避免手写出错。
  - 网格过大报内存：降低 k 密度或换并行策略。

### 1.4 POTCAR 不匹配

- **典型报错片段**：`POTCAR does not match POSCAR`、`POTCAR: ... element order ...`、`Fatal error: PAW_PBE ... not found`、`LATTYP: ...`。
- **成因**：
  - POTCAR 中元素顺序/数量与 POSCAR 不一致（含重复元素、原子顺序不同）。
  - 伪势文件缺失、路径没配置 `POTCAR` 或 `$VASP_POTCAR`。
  - 用了与 `VASP` 版本不匹配的 POTCAR 目录（如 5.4 与 6.x 的 PAW_PBE 略有差异）。
  - **选错了同一元素的 POTCAR 变体**：同名元素常有多个版本（如 `Bi` 与 `Bi_d`），**价电子数不同**，算出来的结果自然不同——而且**不报错**（静默错误）。
- **定位**：比较 POSCAR 元素列表与 `grep "VRHFIN" POTCAR` 得到的元素列表。
- **查价电子数**：POTCAR **第二行的数字**就是该赝势的价电子数，用它来核对变体对不对——例如文章里 Bi 用 `5d10 6s2 6p3`，即 10+2+3 = **15 个价电子**，所以应选价电子数为 15 的那个（`Bi_d` 而不是 `Bi`）。带 `_d`（或 `_pv` 等）后缀通常表示把 d 电子纳入价电子；**带 `GW` 的一律忽略**（那是给 GW 方法用的）。
- **完整的选择知识**：赝势目录 ↔ 泛函对应表与基本权衡见 `references/onboarding.md` §3.2；**按元素/按计算类型的官方选势建议**（含「含短键二聚体用 `_h`」「杂化泛函禁用软势」「f 区 `_2`/`_3` 势」等）见 `references/potcar.md`。
- **也可以从 `OUTCAR` 反查**（跑完之后想确认实际用了什么）：`grep TIT OUTCAR`（有哪些元素）、`grep ZVAL OUTCAR`（价电子数）、`grep ENMAX OUTCAR`（赝势建议截断能）。
- **方案**：
  - 按 POSCAR 元素顺序重排并拼接 POTCAR；确保每种元素恰好一个头。
  - 脚本 `scripts/gen_inputs.py` 的 `--potcar` 参数可自动拼接并校验。
- **手动构建 POTCAR 就是按序拼接**：新建文件后，按 **POSCAR 里元素的顺序**依次把各元素的 POTCAR 内容粘贴进去（多元素就一个个往下贴）；Linux 下等价于 `cat A B C > POTCAR`。**顺序必须与 POSCAR 完全一致**——顺序反了，VASP 相当于把两种元素对调，后面的计算全是错的。
- 也可以用 **VASPKIT**：`1 102` 生成 `KPOINTS` 时会**按预设自动完成 POTCAR**；`1 104` 可手动指定；`1 103` 单独生成 POTCAR（见 `references/tools.md` 四.1）。
- 关于泛函：`PAW` 比超软（US）更精确但更慢，工程上常用 `PAW_PBE`；**PBE 与 PW91 没有本质区别**，看到 `GGA` 直接用 PBE 即可。

### 1.5 复用旧文件（CHGCAR / WAVECAR）出错

- **典型报错片段**：`charge density could not be read from file CHGCAR`、`WAVECAR ... inconsistent`、`Fatal error: reading CHGCAR`。
- **成因**：`ICHARG=11`/`ISTART=1` 复用了与当前结构/参数不匹配的 `CHGCAR`/`WAVECAR`（原子数、晶胞、`NBANDS`、自旋设置不同）；或文件损坏/版本不兼容。
- **方案**：核对复用的旧文件是否来自「同一结构、同一超胞、同自旋设置」的 scf；不一致就删掉 `CHGCAR`/`WAVECAR` 重新自洽；必要时先做一次 `LCHARG=.TRUE.` 的干净 scf。
- **续算时卡在 `charge-density read from file:` 之后不动**：多半是 `CHGCAR` 没写完（例如撞 walltime 被截断），VASP 会一直等缺失的数据直到超时——删掉 `CHGCAR` 重跑，或 `touch CHGCAR` 放一个空文件。
- **计算正常跑着突然 `application called MPI_Abort(MPI_COMM_WORLD, 1)` 且无其它信息**：社区经验是先删 `CHGCAR` 与 `WAVECAR` 重跑。

---

## 二、SCF（电子自洽）阶段

### 2.1 电子步不收敛 / SCF 震荡

- **典型报错片段**：`RMM-DIIS: did not converge, bisect, step`、`NELM exceeded`、电子步震荡、`dav: did not find a lowest eigenvalue`。
- **成因**：
  - 电荷混合参数不当（金属体系、磁性体系常见）、初猜不好、`NELM` 太小、`NBANDS` 不足、`ISMEAR` 不适合体系。
  - 磁性体系初始 `MAGMOM` 设置不合理导致震荡。
- **方案**：
  - 增大 `NELM`（如 60–200）；降低混合：`AMIX=0.1`、`BMIX=0.0001`（含 `AMIX_MAG/BMIX_MAG` 对磁性），必要时 `IMIX=4`（Kerker）或加 `MIXPRE`。
  - 用更稳定的 `ALGO=Normal`（而非 Fast）或调 `ALGO` 尝试 `All`/`Damped`。
  - 提高 `NBANDS`（加 10–20%）；检查 `ISMEAR`：金属用 `ISMEAR=1`（`SIGMA=0.1–0.2`），绝缘体用 `0`；**金属做结构弛豫或任何带力的计算时不要用 `ISMEAR=-5`**（四面体法只适合静态能量、DOS 这类不带力的计算）。
  - 对磁性体系先做非自旋或粗收敛得到好初猜，再恢复 `ISPIN=2`。
  - **`LMAXMIX` 别忘**：`+U`、`ICHARG=11`、以及含 d/f 电子的体系要设 `LMAXMIX=4`（d 区）或 `LMAXMIX=6`（f 区），否则电荷混合难收敛。
  - **`BMIX` 不要写 0**（某些版本会直接崩），最小写 `0.0001`；结构优化/MD 过程中**某一步突然不收敛**时加 `MAXMIX=50`。
  - **先粗后精**：先用大 `SIGMA`（如 0.2）粗收敛，再读 `CHGCAR`/`WAVECAR` 用小 `SIGMA` 精算；或先用 Γ 单 k 点（1×1×1）收敛，再读 `CHGCAR` 用密 k 网格。
  - 换算法与基组：`ALGO=Conjugate`；用更小/更大 `ENCUT` 做预收敛；换更 soft 的赝势。
  - 官方教程的兜底顺序：`ALGO=N` → `ICHARG=12`（不更新电荷的非自洽）→ `ICHARG=2` + `AMIX=0.1 BMIX=0.01` → `BMIX=3.0 AMIX=0.01` → 仍不行按 bug 报。

- **`ALGO`（电子迭代算法）怎么选**（社区整理，含 `IALGO` 对应与各自的坑）：

| `ALGO` | `IALGO` | 特点与用法 |
| --- | --- | --- |
| **`Normal`**（默认） | `38` | **稳定性最好**（手册原话：RMM-DIIS 在少数情况下会失败，而 `IALGO=38` 至今未在任何测试体系失败过）；出问题时**先试降低 `NSIM`**；小体系首选 |
| `Very_Fast` | `48` | 单步电子步耗时**少得多**（大体系、小内存带宽尤甚）；**只建议用于"容易收敛"的大体系**；可靠性较差。两个常见坑：① **MD/弛豫时未占据带优化可能失败 → 加 `WEIMIN = 0`**；② **轨道初始化不合理时可能收敛不了 → 增加 `NBANDS`，仍不行就换 `Fast`**；③ 不收敛时**降低 `AMIX`、增加 `BMIX`** |
| **`Fast`** | 38→48 | **先用 `IALGO=38` 走几步拿到合理初始电荷，再切 `IALGO=48`**（结构优化时，第一步离子步之后**每个离子步都先做一步 38**）；**相当可靠**，相同电子步数下比 `Normal` 快 |
| `Damped` | `53` | 面向**小带隙体系和金属**（这类体系常需要更大 `NBANDS`）；**配 `LDIAG=.TRUE.`** 能有效求基态；`LDIAG=.FALSE.` 收敛更快但**可靠性显著下降**；⚠️ **`TIME` 极其关键**（见下） |
| `All` | `58` | 建议用于**绝缘体**；非自旋极化时，**在"能带数 = 电子数的一半"时稳定性最佳**（有时甚至优于 `Fast`） |

- ⭐ **`TIME` 的优化方法**（`Damped`/`All` 用）：`TIME` 太小 → 收敛显著变慢；太大 → 不收敛。
  **做法：从小的 `TIME` 开始，每次乘 `1.2` 逐步增大，直到计算发散，然后取"仍能稳定收敛的最大 `TIME`"
  用于所有同类计算**（可用脚本批量测；这条与 HSE 里 `TIME=0.4` 的用法同源）。
- **选择算法时要权衡的三件事**：① **单步耗时 vs 迭代步数**（`Normal` 步数少但单步慢；`Fast` 单步快但复杂体系可能收敛困难）；
  ② **基态是金属还是半导体**（决定 `Damped` 还是 `All`，也影响 `AMIX`）；③ **是否有磁性**（复杂磁性体系优先保稳定）。
  对耗时敏感时，确定金属/半导体后可考虑 **`Damped` + `TIME` + `LDIAG`** 或 **`All` + `TIME`**。

- **磁性体系的 MIXING 实战**（同一作者的系统总结，也是 `errors.md` §2.6 那段 AMIX 经验的出处）：

  - **推荐"线性混合"**：**`BMIX = 0.0001` + `BMIX_MAG = 0.0001`**（适合 **slab、磁性体系、绝缘体/分子团簇**），
    能明显改善磁性体系的自洽收敛；⚠️ **一旦用线性混合，`AMIX` 就成了关键参数**；
  - **`AMIX` 的量级**：**磁性金属 ≈ `0.02`；磁性半导体 ≈ `0.2`**（在 `ALGO=Normal` 基础上）；
  - ⚠️⚠️ **`AMIX` 过大的两个后果**：**要么不收敛，要么"收敛到更高的状态"**——能量与总磁矩都与正确态差很多；
    **对设了层间反铁磁耦合的体系，还可能根本拿不到目标磁构型**；
  - ⚠️⚠️ **不写 MIXING 时的默认值是 `AMIX = 0.4`（`BMIX = 1.0`）——对不少磁性金属过大**，
    这是"什么都没改却收敛到错误磁态"的常见根源；
  - 📌 **加大 `NBANDS`/加密 k 点救不了混合参数问题**：实测在 `NBANDS` 与 k-spacing 足够大之后，
    再增大对收敛性提升不大，**`AMIX` 不对就依然不收敛或收敛错误**；
  - **`AMIX` 怎么定**：手册法（`AMIX_opt = AMIX_current × Γ`，Γ 取 `OUTCAR` 的 `average eigenvalue`，
    做到 Γ=1）**在实测的磁性金属上"很难得到合适的值"**——**作者因此更推荐直接扫描 `AMIX`**
    （例如 `0.02 → 0.2`、步长 `0.02`），并**同时盯住 `OSZICAR` 的总磁矩**确认收敛到了目标磁态；
  - **`IMIX` 的补充**：**`IMIX=4`（默认）**，`WC>0` 时走 **Pulay's scheme**、`WC=0` 时走 **Broyden 2nd**
    （默认 `WC>0`；**不建议改 `WC`**；`OUTCAR` 里默认显示的是 "modified Broyden-mixing scheme"，
    社区认为它实际就是 Pulay）；**`IMIX=1`（Kerker）平时少用**，但**论坛管理员建议"HSE06 + `ALGO=Normal`"时用 `IMIX=1`**。

### 2.2 NBANDS 不足

- **典型报错片段**：`TOO FEW BANDS for a reasonable calculation`、`NBANDS too small`、`Warning: number of electrons ...`。
- **成因**：默认 `NBANDS` 不足以容纳所有电子+空带。
- **方案**：显式增大 `NBANDS`（如按默认的 1.2–1.5 倍），或用 `NELECT` 校正价电子数错误。

### 2.3 非埃尔米特 / 数值警告

- **典型报错片段**：`Sub-Space-Matrix is not hermitian in DAV`（多见于磁性/自旋轨道或混合较激进时）。
- **成因**：常与电荷/自旋混合不当、`AMIX` 过大、磁性体系 SCF 初期不稳定、或 `NBANDS` 设置相关；也见诸某些数值条件较差的体系。
- **方案**：
  - 降低混合参数（`AMIX`/`BMIX`/`AMIX_MAG`），用 `IMIX=4` 或 `MIXPRE`。
  - 提高 `NELM` 并允许更多步数收敛；检查 `ISMEAR`。
  - 若伴随磁性，检查 `MAGMOM` 初猜合理性。
  - 该警告若只是偶尔出现且最终收敛，可先观察是否影响最终结果；频繁出现则按上述调参。
  - **若在「新」计算一开始就反复出现、且怎么改 INCAR 都没用**：看 `NBANDS ÷ 核数` 是否过小（经验上 < 5 就容易触发）——**减少 MPI 核数**（如 28 核节点只用 14 核），或**增大 `KPAR`**让单个 k 点由更少的核处理，通常能直接稳住。
  - 若同时出现 `Error FEXCP: supplied Exchange-correletion table is too small` 或 `BRMIX: very serious problems, the old and the new charge density differ`，优先按上一条（核数 / `KPAR`）处理。

### 2.4 NaN / 数值发散

- **典型报错片段**：能量/力出现 `NaN`、`nan`。
- **成因**：结构严重不合理、`ENCUT`/`PREC` 过低、混合发散、伪势不匹配、晶胞/原子重叠。
- **方案**：先用合理 `PREC` 和默认 `ENCUT`；检查结构是否有重叠原子；检查 POTCAR 是否匹配；重跑自洽看初值是否正常。

### 2.5 自旋 / 磁矩 / SOC 设置不一致

- **典型报错片段**：`MAGMOM` 个数与原子数不符、`LSORBIT` 需要 `LNONCOLLINEAR`/`SAXIS`、`ISPIN` 相关对称报错、`magmom` 相关 `symmetry equivalent atoms`。
- **成因**：`MAGMOM` 给出的磁矩数≠原子总数；开 `LSORBIT` 未配 `LNONCOLLINEAR` 与 `SAXIS`；自旋磁矩破坏了体系对称性而 `ISYM` 仍开。
- **方案**：`MAGMOM` 逐原子给全（可用 `scripts/gen_inputs.py -w mag --magmom "Fe:5,Mn:4"` 生成）；SOC 设 `LNONCOLLINEAR=.TRUE.`+`LSORBIT=.TRUE.`+`SAXIS`；对称相关报错设 `ISYM=0` 或调整磁构型。

### 2.6 LAPACK：ZPOTRF / ZHEGV 失败（EDDRMM）

- **典型报错片段**：`LAPACK: Routine ZPOTRF failed! 1 1 1`、`WARNING in EDDRMM: call to ZHEGV failed, returncode = 3 2 ...`（`returncode` 末尾 1→99 循环，即每步触发）。
  - 换个实例：`returncode = 7 1 8` 也是同一个错——**通俗地说就是电子步能量发散、怎么算都收不住**（原作者的原话）。
- **含义**：数值发散/崩溃——VASP 对非正定或病态矩阵做 Cholesky 分解（`ZPOTRF`）或广义本征求解（`ZHEGV`）失败；也常是 RMM-DIIS 电子最小化失败（`ALGO=Fast` 用 RMM-DIIS）。
- **成因**：SCF 不稳定/电荷混合发散；输入不一致或初值不当（旧 `WAVECAR`/`CHGCAR`、`MAGMOM` 初猜差）；并行/内存设置不当（`KPAR*NCORE` 分配、`NCORE` 过大）；精度不够；POTCAR 混用；k 网格过疏。
- **方案（按序）**：
  1. 删 `WAVECAR`/`CHGCAR`，`ISTART=0`、`ICHARG=2`；SOC/DFPT 前先收敛普通 SCF。
  2. **`ALGO=Normal`**（仍不稳→`All`；顽固→`Damped` + `TIME=0.3–0.6`）——直指 RMM-DIIS 失败。
  3. `PREC=Accurate`、`ENCUT≥max(POTCAR)×1.2–1.3`、`ADDGRID=.TRUE.`；金属/大体系 `LREAL=.FALSE.`。
  4. 混合：`AMIX=0.2 BMIX=0.0001 AMIX_MAG=0.2 BMIX_MAG=0.0001` 起；金属难收敛 `AMIX(_MAG)=0.05–0.1`；sloshing 加强 `BMIX(_MAG)=0.001`。
  5. 展宽：金属 `ISMEAR=1 SIGMA=0.2`（稳定后 0.1），绝缘体 `ISMEAR=0 SIGMA=0.05`。
  6. 设合理 `MAGMOM`；对称问题 `ISYM=0`（SOC/偏心常见）。
  7. 并行：`KPAR*NCORE≤总核数` 且整除；`NCORE` 过大降到 4–8；可用 Γ 单 k 点诊断。
  8. `NBANDS` +10–20%。
  9. POTCAR 同一套（勿 PBE+LDA 混用）；k 网格勿过疏，可 `KSPACING≈0.2–0.3`。
  10. SOC 专项：先无 SOC 收敛，再开 `LSORBIT`（必要时 `LNONCOLLINEAR`），保持 `ISYM=0`/`LREAL=.FALSE.`、`NBANDS` 略高。
  11. **把几何步长降下来**（针对「上一步几何变坏导致发散」这条成因的具体数值经验）：`POTIM` 默认 `0.5` → 先试 **`0.1`**，仍不行再降到 **`0.05`**（代价是明显变慢）；同时把 `IBRION` 换成 `2`（CG）。多方反馈这类 `returncode` 报错**多半是 POSCAR / 初猜几何不合理**（“position unreasonable guess”）；如果结构取自实验数据、不方便改，就只能在 `ALGO`、`POTIM` 与混合参数上想办法（原作者当时正是这种情况）。
      - **后续补充（同一作者的第二篇笔记）**：`POTIM` 可以一路降到 **`0.005`**，但**只对小体系管用**——原子一多照样报错；这时把 **`ALGO` 换成 `F`（Fast）**能压住报错，**代价是慢得离谱**（作者跑了一个半月），中途 VASP 还会提示 **「请选择更小的 EDIFF 或者拷贝 CONTCAR」**。
      - **两阶段做法（更省时间）**：先用 `ALGO=F` **少跑几步**（`NELM`/`NSW` 都取小，几十即可，别像作者那样取 160/200），把得到的 **`CONTCAR` 丢进 `ALGO=N`（Normal）里继续算**——作者的猜测是 `Normal` 从初始构型出发「离最终结果太远、走不过去」，先用 `Fast` 跑到附近再用 `Normal` 就不报错。
      - **别顺手把收敛判据设太严**：作者用的 `EDIFF=1E-6`、`EDIFFG=-0.001` 他后来自己也怀疑过严。注意方向——**放松 = 增大 `EDIFF`（如 `1E-4`）并增大 `|EDIFFG|`（如 `-0.01` ~ `-0.05`）**；原文在「往大还是往小」上说反过一次，以这里的写法为准。
- **附**：可用 custodian / aflow 自动处理此类常见报错（详见 `articles/20260930-lapack-zpotrf-zhegv-failed.md`）。
- **EDDRMM/ZHEGV 的四类成因（社区归纳）**：
  1. **RMM-DIIS 对该体系不稳** → `ALGO=Normal`（分块 Davidson）或 `ALGO=Fast`（5 步 Davidson + RMM-DIIS）；
  2. **几何不合理**：报错出现在**第一个离子步**就去查 `OUTCAR` 里的初始几何；若是**上一步弛豫**产生了不合理几何（对比 `XDATCAR` 的输入/输出几何），换 `IBRION` 并把 `POTIM` 调小于默认；
  3. **LAPACK 安装不当** → 改用它自带的 `vasp.4.lib/lapack_double.o`；
  4. 换了 Davidson 仍报错：某些架构（如 SGI）的 LAPACK 例行程序有问题，可注释掉 `davidson.F`、`subrot.F`、`wavpre_noio.F` 里的 `#define USE_ZHEEVX` 后**重新编译**，绕开 `ZHEGV`。

---

- **磁性解法（社区实例，针对 `Error EDDDAV: Call to ZHEGV failed. Returncode = 7 1 8`）**：

  - **先看诊断量**：**`grep "average eigenvalue" OUTCAR`**——PBE 计算会给出这个"平均本征值" Γ，
    手册认为 **Γ = 1 时电荷密度混合最优**（下面的公式用它）；
  - **首选手段：调 `AMIX`（线性混合系数）**，而不是一上来就改 `ALGO`/`NBANDS`：
    - **金属体系 `AMIX` 要小**（常用 `0.02`）；**半导体 `AMIX ≈ 0.2`** 多数情况能快速收敛；
    - ⚠️⚠️ **磁性金属体系里 `AMIX` 过大会"收敛到更高的磁态"**——看着收敛了，
      其实是**能量更高的错误磁态**（用 `AMIX=0.02` 才能拿到能量更低、磁矩正确的那一个）。
      这属于**静默错误**：**务必用 `OUTCAR` 的磁矩确认磁态**（见 `onboarding.md` §9.3 的磁态检查）；
    - **手册公式**：`AMIX_opt = AMIX_current × Γ`（Γ 取上一步的 `average eigenvalue`），迭代到 Γ = 1；
      **但社区更推荐直接扫描 `AMIX`**（例如 `0.02 → 0.2`、步长 `0.02`）——**对磁性金属，手册那套公式
      有时会给出相当糟糕的结果**（两种做法并列，建议都试一遍）；
    - 一个可用的**磁性混合参数组合**（报错时的起点）：
      **`AMIX=0.02`、`BMIX=0.0001`、`AMIX_MAG=0.8`、`BMIX_MAG=0.0001`**。
      社区实测：把 `AMIX` 从 `0.2` 改成 `0.02` 后就能算通；再按 `AMIX_opt = 0.02 × 1.5 = 0.03`
      （作者把 Γ 取小到 `1.5`）调整，**电子步降到 63 步收敛**。
  - **同一报错的另一条成因（非磁体系也会遇到）**：**`SYMPREC` 的设置**可能导致该报错——
    把 `SYMPREC` 去掉后计算即可继续（与 §8.2 的 `SYMPREC` 条目互查：它影响对称性判断）。
  - **来源**：`articles/20261001-VASP_Error_EDDDAV_Call_to_ZHEGV_failed_的磁性解决方案.md`
    （原文另引用了 <http://bbs.keinsci.com/thread-12444-1-5.html> 的讨论帖）。

## 三、离子步阶段

### 3.1 离子步不收敛

- **典型报错片段**：`NSW exceeded`、离子步数用尽、`EDIFFG` 未达到。
- **成因**：`NSW` 太小、初始结构远离平衡、力收敛标准 `EDIFFG` 设置过于严苛（注意：正值是能量判据、负值是力判据）。
- **方案**：增大 `NSW`（如 100–300）；先低精度粗优化再高精度；检查 `EDIFF`/`EDIFFG` 合理性；用 `IBRION=2`（CG）配合理 `POTIM`，或 `IBRION=3`（Damped MD）处理难收敛的势能面。
- **结构优化不收敛的进阶清单（社区经验，按现象选）**：
  - **力在接近收敛处震荡**：多半是电子步精度不够 → `EDIFF=1E-6`（必要时 `1E-7`）；也可试 `IBRION=1`。
  - **初始结构不好、前几步就崩**：`IBRION=2` 配 `POTIM=0.2` 或 `0.1`；在**极小点附近震荡**时进一步降到 `0.05`。
  - **体系大、收敛慢**（力与能量趋势都向下）：把 `NSW` 提到 `500`（**不建议超过 500**）；超大体系可试 `IBRION=3`（阻尼 MD）。
  - **高对称陷阱**：先用 `ISYM=0` 优化——初猜若是高对称结构，优化过程中高对称往往一直保持，而真实极小点并没有那么高对称，于是难收敛、**且即便收敛也带虚频**。
  - ⚠️ **有固定原子时，别拿「OUTCAR 里的最大受力」判断收敛**：`EDIFFG` **只约束非固定原子**，用 `Selective dynamics` 固定住的原子（`F F F`）受力**不受该阈值限制**——所以判据满足时，最大受力仍可能大于 `|EDIFFG|`。**必须把固定原子排除掉再看**：用本库参考脚本 `scripts/reference/force_conv.sh`（会读 `CONTCAR` 的 `T`/`F` 自动排除固定原子），VTST 版也可用 `vef.pl`（见 `references/tools.md` §4.13）。
  - **收敛判据参考值**：几何优化 `EDIFFG=-0.02`、过渡态 `-0.03`；大体系有人用 `-0.05`，**不建议再松**。
    - **适可而止**：若最大受力已很小却始终达不到判据，**画「总能 vs 离子步」看曲线是否走平**——走平就说明到了方法/软件的极限，不必无限加大 `NSW`。参考判据：**总能波动 ≈ `0.1 meV` 已算收敛得足够好**（尤其 >100 原子的体系）；**受力标准没必要卡 `0.01 eV/Å`，大体系 `0.02~0.05 eV/Å` 即可**。
  - **HSE 做结构优化又慢又难收敛**：💡 **先用 PBE 预优化，再用 HSE 拿 `CONTCAR` 收尾**——能显著减少 HSE 的离子步数（来源：PWmat 文档的结构优化建议，见 `articles/20261001-计算大牛教你优化结构.md`）。
  - 提高积分格点精度 `PREC=Accurate`；用 `cgrad` 一类工具直接看受力走势（<https://github.com/Ionizing/usefultools-for-vasp>）。

### 3.2 线搜索 / 括号错误

- **典型报错片段**：`ZBRENT: fatal error in bracketing`、`BRENT error`。
- **成因**：`IBRION=1`（RMM-DIIS 离子优化）或线搜索在势能面异常处无法成括号，常伴结构/力计算数值问题。
- **方案**：改用 `IBRION=2`；减小 `POTIM`；检查是否伴随 NaN 或对称性问题；先做几何粗优化。
- **一组实测可用的参数组合**（社区记录，按需取用）：`EDIFF=1e-7`；`EDIFFG=-1e-3`；`SYMPREC=1e-6`；`IBRION=1`（该记录中能量最低）；`POTIM=0.05`（或 0.1）；**加大 `ENCUT` 虽有效但不推荐**（应先做收敛性测试）、**减小 KPOINTS 也不建议**。

### 3.3 虚频 / 声子计算相关（非致命但需处理）

- ⚠️ **声子流程里两条最容易踩的「设置型」报错/错算**（见 `workflows.md` §38.9）：
  1. **有限位移法的单点计算把 `ISIF` 设成了 `0`** ⇒ **根本不算力**（H-F 力拿不到），声子流程直接崩；
     正确做法：`NSW = 0` 但 **`ISIF` 保持能算力的值**（如 `ISIF = 2`）；
  2. **`IBRION = 8` 时留着并行参数**（`NPAR`/`NCORE`/`KPAR`）⇒ **容易报错**；
     稳妥做法是先关掉这些并行参数再跑 Hessian 步。


- **现象**：声子谱/`phonon` 输出出现虚频（负频率），提示 `phonon mode negative`。
- **成因**：结构未充分优化、位移设置不当、数值噪声、或体系确实处于亚稳态。
- **方案**：先确保几何优化收敛到足够精度（力判据更严，如 `EDIFFG=-1E-3`），再生成位移；用更对称/更大的超胞；ALAMODE 拟合时检查正则化参数。


### 3.4 OUTCAR 里没有力 / 力恒为零

- **不是报错，但很常见的困惑**：VASP 主程序 STEP 48（FORCES+STRESS）在若干情形下**直接跳过力的计算**——
  `OEP` 方法（`EXXOEP ≠ 0`）、老算法 `IALGO=1–4`、从文件读入势（源码中的 `INICHG == 4`），
  以及使用内部本征值求解器时。
- **方案**：先确认这是不是正常情况（`IBRION=-1` 的纯静态本来就没有离子受力）；若确实需要力，回到默认
  `ALGO`/`IALGO=38`，并确保 `ISIF ≥ 2`、没有误用上述算法标签。
- 另注：STEP 46 会做「占据数 / 是否够带」检查——`NBANDS` 相关报错就出现在这一步（见 §2.2）。
- **另有两类「力恒为零」不是算法问题，而是结构/约束造成的**（很容易误判）：
  - **固定原子**：`Selective dynamics` 里标了 `F F F` 的原子，受力会被置零——如果体系里只有固定原子在「该动的地方」，看起来就是「力一直是 0、优化不动」；
  - **对称性造成的方向性零力**：例如把过渡金属（TM）掺进**纯平面二维材料**时，**若 TM 与材料共面，它在垂直平面方向的受力恒为 0**（即使 `ISYM=0`）——弛豫后**仍然是纯平面**；**只要在初始结构里把 TM 稍微挪出平面**，弛豫后就会出现起伏、**能量明显更低**。
    同理，**往体系里掺间隙原子 / 做元素替换时，建议手动挪几个关键原子，让初始结构尽量只有 `P1` 对称性**，避开势能面上的特殊点（详见 `workflows.md` 第一节的分步优化块）。
- 来源：`articles/20261001-VASP的计算流程.md`；固定原子与对称性两条另见 `articles/20261001-VASP结构优化计算中查看能量和力收敛情况.md`、`articles/20261001-聊一聊结构优化.md`

---

## 四、运行环境与编译

- **典型报错片段**：`mpirun: command not found`、`libmpi_...: cannot open shared object`、`Segmentation fault`、`vasp_std: command not found`、`out of memory` / `OOM`、`Killed`。
- **成因**：MPI 环境未加载（`module load`）、动态库路径缺失、二进制与 CPU/编译不匹配、作业脚本资源限制（内存/栈/核数不足触发段错误）。
- **方案**：
  - 先确认 `which mpirun` / `which vasp_std`，用 `module load` 加载 MPI 与 VASP 环境。
  - `Segmentation fault` / `Killed`：查是否内存不足（`OOM`）、栈空间（`ulimit -s`）、或伪势/二进制损坏；用 `mpirun` 单进程重跑定位。
  - 资源类：检查 `PBS/Slurm` 脚本申请的核数与内存是否足够（`NELECT`/k 网格大时尤其）；k 点或能带很多但核数过多也会降低效率甚至内存不足，可用 `NPAR`/`KPAR` 调并行策略。
- **本地编译全流程**（Linux 基础 → Intel 工具集 → FFTW → `makefile.include` → `make all`）见知识库文章 `articles/20260930-VASP_给真_小白看的VASP本地编译自学指南_Ver_2_1.md`；下面是编译期最常见的六类问题。
- **按 VASP 版本整理的编译教程汇编**（约 60 条：4.4.5 / 5.2.0–5.4.4 / 6.1.0–6.4.0，含 Intel oneAPI、GPU、VTST、Wannier90、WSL/Windows、Docker、HDF5 专题）：`articles/20261001-VASP_编译相关链接集锦.md`。

### 4.1 Intel 编译器 / MKL 环境变量没生效

- **典型报错片段**：`ifort: command not found`、`icc: command not found`、`cannot find -lmkl_intel_lp64`、`MKLROOT` 为空、`mkl.h: No such file or directory`。
- **成因**：Intel 工具集的环境脚本没有被 source；只写进 `~/.bashrc` 但当前 shell（尤其是 `mpirun`/作业脚本拉起的非交互 shell）没有重载；手写 `export PATH=/opt/intel/bin:$PATH` 与 `compilervars.sh` 互相覆盖。
- **方案**：在 `~/.bashrc` 末尾加 `source /opt/intel/bin/compilervars.sh intel64` 与 `source /opt/intel/mkl/bin/mklvars.sh intel64`（路径按实际安装改），再 `source ~/.bashrc`；**不要**再手写 `PATH`/`LD_LIBRARY_PATH`（脚本里已含，重复添加才是常见故障源）。验证四连：`icc -v`、`ifort -v`、`which ifort`、`echo $MKLROOT`。
- **注意**：`~/.profile` 只在登录时执行一次，`~/.bashrc` 每次新开 shell 都读，`/etc/bashrc` 对所有用户生效——作业脚本里往往一个都不读，所以环境要么写进作业脚本，要么用 `module load`。

### 4.2 makefile.include：选哪个模板、能不能不改

- **典型报错片段**：`make: *** No rule to make target 'makefile.include'`、链接期 `undefined reference to 'dgemm_'`、找不到 `libmkl_*`。
- **成因**：没有从 `arch/` 取模板；取了与编译器/MPI 不匹配的模板（`linux_gnu` vs `linux_intel`、串行 vs MPI）。
- **方案**：`cp arch/makefile.include.linux_intel .` 再 `mv makefile.include.linux_intel makefile.include`（另有 `makefile.include.linux_intel_serial`、`linux_gnu`、`linux_pgi`）。图快可以**完全不改**直接 `make all`：模板默认用 `ifort`，并到 `MKLROOT` 找库、走动态链接。要改就重点核对 `MKLROOT`/`MKL_PATH` 与 `OBJECTS`/`INCS` 里的库路径。

### 4.3 FFTW：用 MKL 自带接口还是自编译

- **典型报错片段**：`undefined reference to 'fftw_...'`、`libfftw3_mpi.a: No such file or directory`。
- **成因**：模板 `OBJECTS` 里写的是自编译 FFTW 的路径（如 `/opt/fftw/lib/libfftw3_mpi.a`），而机器上其实用 MKL 自带的 FFTW3 接口——后者需要先生成 `libfftw3.mpi.a`。
- **方案**：二选一，**不要混用**——(a) 用 MKL 接口：在 `$MKLROOT/interfaces/fftw3xf` 下执行 `make libintel64` 生成 `libfftw3.mpi.a`，再把 `OBJECTS` 指到它；(b) 自编译 FFTW3（打开 MPI），把 `OBJECTS`/`INCS` 指到自己的 `/opt/fftw`。

### 4.4 BLAS / LAPACK / ScaLAPACK / BLACS：从缺失符号判断缺哪一层库

- **典型报错片段**：`undefined reference to 'dgemm_'`（BLAS）、`'zhegv_'`（LAPACK）、`'pdsyevd_'`（ScaLAPACK）。
- **说明**：BLAS 是向量/矩阵基础运算接口，LAPACK 在其上做分解/求逆/特征值，ScaLAPACK 是并行版，BLACS 是它的通信层。MKL 对应写法：`-lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lpthread`（BLAS/LAPACK），ScaLAPACK/BLACS 用 `libmkl_scalapack_lp64.a` 与 `libmkl_blacs_*`。
- **方案**：按报错里缺的符号名回溯到对应变量（`BLAS`/`LAPACK`/`SCALAPACK`/`BLACS`）补齐；`mkl_sequential` 与 `mkl_intel_thread` 不要同时链接，用线程层时补 `-liomp5`。

### 4.5 编译通过但运行时报缺库

- **典型报错片段**：`error while loading shared libraries: libmkl_intel_lp64.so: cannot open shared object file`；换一个节点就报同样的错。
- **成因**：Intel 模板默认动态链接，而运行环境（作业脚本）的 `LD_LIBRARY_PATH` 里没有 MKL/Intel 库目录——交互式 shell 里有、作业脚本里没有。
- **方案**：作业脚本里同样 source `compilervars.sh`/`mklvars.sh`（或显式设置 `LD_LIBRARY_PATH`）；或改静态链接；用 `ldd vasp_std` 查到底缺哪个 `.so`。

### 4.6 编译前的基础依赖（Ubuntu 为例）

- **典型报错片段**：`g++: command not found`、`bits/stdc++.h: No such file or directory`、32 位相关头文件/库缺失。
- **方案**：`apt-get update` 后安装 `build-essential`、`g++`、`gcc`、`libc6-dev-i386`、`gcc-multilib`、`g++-multilib`（需要 32 位兼容时）；部分老教程还会要求 `libstdc++5` 与 `openjdk-8-jre`。

### 4.7 固定轴优化：`constr_cell_relax.F`

- **需求**：只想弛豫部分晶格方向（二维材料常固定 c 轴；单轴加载时固定加载方向）。
- **方案**：使用刘锦程分享的 `constr_cell_relax.F` **重新编译 VASP**，然后配一个 `OPTCELL` 文件控制哪些方向可变——**非正交体系同样适用**。例如固定 Z 轴时 `OPTCELL` 写三行：
  ```text
  110
  110
  000
  ```
- 注：不改源码时，VASP 自带的 `ISIF`/`OPTCELL` 组合也能覆盖多数场景（见 `references/workflows.md` 第十三、十四、十六节）。
- ⚠️ **`OPTCELL` 文件里 `0` 和 `1` 之间不能有空格**（写成 `011` 这类连排）。
- ⚠️ **把 `OPTCELL` 上三角矩阵元设为 0 可以阻止弛豫中晶胞转动，但这一做法有风险**：
  以 `F_ay` 置零为例——`a` 晶格在 x 方向的增量本来是 `F_ax·L_ax + F_ay·L_bx`，置零后变成 `F_ax·L_ax`：
  **若 `F_ax > 0` 而原本 `F_ay < 0`，置零前后该项的正负号可能翻转，`a` 晶格会朝相反方向变化**。
  （参考刘锦程的博文：<http://blog.wangruixing.cn/2019/05/05/constr/>）
- ⚠️ **前提**：**`OPTCELL` 必须配合修改过的 `constr_cell_relax.F` 并重新编译 VASP 才生效**；**没有重新编译的 VASP 不需要（也无法）准备这个文件**（见 `workflows.md` §36.9）。
  📌 同一篇博文的另一个域名：<https://blog.shishiruqi.com//2019/05/05/constr/>（王瑞星 blog 迁移后的地址）。


---

## 五、ALAMODE 相关（声子 / 热输运）

- **典型报错片段**：`[create_phonon_config] ...`、拟合报 `energy must be scalar`、`cannot fit harmonic`、`displacement not consistent`。
- **成因与定位**：
  - 能量文件解析错误 / 列不对：检查 `f`（力）与 `energy` 数据的列序、单位（eV/Å vs eV）。
  - 位移与结构不匹配：检查 `POSCAR` 顺序、超胞与 `displacements` 是否对应。
  - 拟合矩阵奇异：位移构型不足、正则化参数（`lreg_scale`）需调整。
- **方案**：
  - 核对 ALAMODE 的 `infile`（`harmonic`/`anharmonic`）各参数与数据文件路径。
  - 用 ALAMODE 自带工具重新生成位移并核对能量文件列数。
  - 拟合时先检查 `lreg_scale`/正则化，必要时增大位移超胞或多构型。
  - 三声子/四声子散射速率与热导率计算（`ph_conductivity`）报错多与前三阶/四阶力常数拟合质量有关，先回到拟合环节排查。

---

## 六、LOBSTER / COHP 相关（成键分析后处理）

- **lobster 不报错但无 COHP/ICOHP 输出**：几乎都是 **`NBANDS` 太少**。方案：加大 `NBANDS` 重跑 VASP（`LWAVE=.TRUE.`）再重算。
- **COHPCAR.lobster 只有正值/无负值部分**：多为元素名、键长范围或轨道（basisfunctions）设置问题。方案：核对 `lobsterin` 的 `cohpGenerator` 元素/键长、`basisfunctions` 是否按 POTCAR 价电子轨道填写、元素名/原子编号是否写对。
- **COHP 图像毛刺多**：k 点不够密，或插值/画图点太少。方案：加密 VASP 的 k 网格，或调整画图插值密度。
- **涉及元素名的报错**：检查 `lobsterin` 中元素名/原子编号拼写。
- **原子对数量与预期不符**：`cohpGenerator` 指定键长范围产生的原子对必须与结构实际的键长分布一致，多了/少了都会改变 COHP/ICOHP 值（用 `scripts/gen_lobsterin.py --list-bonds` 核对）。
- **原理提醒**：COHP 成键为负、反键为正；文献常画 `-COHP`。详见 `articles/20260930-vasp-lobster-cohp-bonding.md`。

---

## 七、高频注意事项（防患）

- 磁性 + 声子：有限位移法要在**磁构型下**位移，且确保力收敛判据严格，否则声子谱虚频。
- 热电/输运前：先保证 `scf` 收敛、能量/力噪声可控，再跑 `BoltzTraP2` / 输运系数，否则 ZT/Seebeck 结果不可信。
- 每次改参数后，用 `grep` 确认 OUTCAR 推进到对应阶段，不要只看是否退出。
- **二维材料的介电常数 / 光学性质不能直接套用 3D 定义**（**静默错误**：程序不报错，数值却没有意义）：把 3D 的静态介电常数与光学性质定义直接搬到 2D 材料上，得到的**不是 well-defined 的物理量**——国内相当多已发表工作都没有处理真空层效应。方案：按 2D 体系定义（考虑真空层）处理，或使用已支持二维光学性质的 `VASPKIT`（1.10.beta3 起）；原理见 *Nano Lett.* DOI 10.1021/acs.nanolett.9b02982 与 *New J. Phys.* DOI 10.1088/1367-2630/16/10/105007。
- **想「调整费米能级位置」不必改计算**：做能带 / DOS 对齐时，把能量值**整体加减一个常数**即可（本质就是换参考零点）；影响物理的是相对位置，不是绝对值。
- **原胞的「基矢形式」会静默地改变结果**：算**弹性常数**（以及介电、压电）前必须先确认原胞是**标准基矢形式**（standard primitive cell）——**AFLOW / VASPKIT（`6 602`）给的是标准原胞**，而 **VESTA / Materials Studio / Materials Project 给的通常不是**。用非标准原胞算出的弹性矩阵会出现本不该有的非对角项、三个方向 `C11` 还不一致，**但不会报错**。详见 `workflows.md` §18.0。

---

- ⚠️ **DFT+U 的三处静默陷阱**（都不报错，但结果是错的——见 `workflows.md` §三十）：
  1. **`LDAUL` / `LDAUU` / `LDAUJ` 是按 POSCAR 元素顺序一一对应的数组**——顺序写错（或漏掉某个元素的
     占位 `-1` / `0`）就会把 U 加到错误的元素上；
  2. **`LMAXMIX` 没跟着轨道放大**：加 U 时它必须大于轨道角量子数，**d → `4`、f → `6`**（默认 `2`）；
  3. **U/J 值没有出处**：U 值应能追溯到文献，或用实验带隙等性质校准（`U_eff` 与带隙是相互约束的）。
- ⚠️ **同一个 INCAR 里同一个标签写两次**（如 `PREC` 先 `Normal` 后 `Accurate`）：**建议清理成一个**，
  不要依赖"后出现者生效"这类不确定行为（社区文章里出现过这种写法）。

- ⚠️ **用 `I_CONSTRAINED_M`（约束磁矩）时的两个静默陷阱**（见 `workflows.md` §三十四）：
  1. **总能要减掉惩罚项**：`OUTCAR` 里的能量**已经包含**约束的能量惩罚 `E_p`
     （在 **`OSZICAR` 末尾**读取），**实际 DFT 总能 = `OUTCAR` 能量 − `E_p`**——
     做能量差比较时忘了减，会得到系统性偏差；
  2. **`MAGMOM` 与 `M_CONSTR` 要写成完全一致**（一个是初值、一个是目标），
     否则很可能拿不到想要的磁构型（作者实践经验）。
     另注：`I_CONSTRAINED_M=1` **不区分同一直线上的正反方向**，要区分符号请用 `=4`（需 VASP ≥ 6.4.0）。

- ⚠️ **金属不要用 `LOPTICS` 这套"介电函数"路线**：VASP 算介电函数**只考虑带间直接跃迁**，
  **只适用于半导体/绝缘体**；金属的主导贡献是**带内（Drude）**，不在其中
  （详见 `workflows.md` §36.10）。

- ⚠️ **`LDAUTYPE = 2` 时不要拿"不同 `U`/`J` 的总能量"互相比较**：此时起作用的是 **`Ueff = U − J`**，
  总能量同时依赖 `U` 与 `J`——**跨 `U`/`J` 比较总能没有意义**（要么固定 `Ueff`，要么只比较同一套参数下的
  相对能量）。详见 `workflows.md` §40.3。

- ⚠️ **`LDAUL`/`LDAUU`/`LDAUJ` 的顺序必须与 `POSCAR` 的元素顺序逐一对齐**——**写反不会报错**：
  例如 `POSCAR` 顺序是 `La S`、只想给 `La` 的 `f` 加 U，却写成 `LDAUL = -1 3`
  （正确应为 **`LDAUL = 3 -1`**、`LDAUU = 5.5 0`、`LDAUJ = 0.5 0`），
  结果是 **U 实质上没加到该加的元素上**，而计算照常跑完、照常收敛。
  ⇒ **每次改完 `LDAU*` 都回头对一遍 `POSCAR` 元素顺序**（见 `workflows.md` §40.8，那里有一个真实案例）。

## 八、社区错误集精选（外部来源）

> 本节条目整理自外部社区错误集 `articles/20261001-VASP_errors.md`（原页 <https://dannyvanpoucke.be/vasp-errors-en>），
> 按**原始报错字符串**存放，属于社区经验而非官方结论。其它外部错误库：`error.wiki/VASP`（本次抓取返回 403）、
> 腾讯文档错误集（需 JS/登录，未收录）。

### 8.1 `VERY BAD NEWS! internal error in subroutine SGRCON`（Found some non-integer element in rotation matrix）

- **成因**：对称性判定问题。
- **方案**：增大 `SYMPREC`；更保险（也更贵一些）的做法是 `ISYM=0` 直接关掉对称性。
- **社区记录的可用值**：**`SYMPREC=0.001`**（默认 `1e-5` 对某些胞过严），加到 INCAR 里即可解决。

### 8.2 `VERY BAD NEWS! internal error in subroutine PRICEL`（number of cells and number of vectors did not agree）

- **成因**：同样是对称性——高对称的原子位置让对称算法无法把晶胞识别为原胞。
- **方案**：把某个高对称原子**稍微移开**以破缺对称；或 `SYMPREC=1.0E-8`（默认 1E-5）；或 `ISYM=0`（作者认为这条最可能奏效）。

### 8.3 `internal error in SET_INDPW_FULL: insufficient memory`

- **成因**：往往**不是真的缺内存**，而是 Bravais 矩阵第 5 位带来的对称破缺；HSE06 计算时也可能是 `NPAR` 太小。
- **方案**：把 `SYMPREC` **调小**到 `1e-4`；HSE 时令 `NPAR × KPAR = 总核数`，或干脆 `NPAR=1`（反而更快）。

### 8.4 `Internal error in SETUP_DEG_CLUSTERS: NB_TOT exceeds NMAX_DEG`（声子 IBRION=7/8）

- **成因**：超出硬编码数组上限（`subrot_cluster.F` 中 `NMAX_DEG=48`）。
- **方案**：改源码把 `NMAX_DEG` 调大（如 256）后 `make veryclean && make all` 重编译；但可能只是把上限推高（107 → 320 也见过）。换**原胞**常能根治（作者用 fcc Al 的 conventional cell 改 primitive cell 后解决）。

### 8.5 `The distance between some ions is very small ... I HOPE YOU KNOW, WHAT YOU ARE DOING`

- **成因**：原子过近 / 重叠。
- **方案**：查 `OUTCAR` 的近邻表；用 VESTA 可视化 POSCAR 找"肇事原子"；**同时核对 POTCAR 与 POSCAR 的元素是否一致**——VASP 只按 POTCAR 计算，两者不一致时**不报警**（把 C 配成 Pt 就是这样来的）。

### 8.6 slab 电子难收敛（augmentation 项在离子步之间剧烈变化）

- **方案**：先试 `AMIX`/`BMIX`/`AMIX_MAG`/`BMIX_MAG`、`ALGO=All`、`ISMEAR`/`SIGMA`；**若 slab 位于晶胞中心（而非关于 z=0 对称）且开了偶极修正（`LDIPOL=.TRUE.` + `IDIPOL=3`），把偶极修正关掉反而能稳定下来**。

### 8.7 `WARNING: CNORMN: search vector ill defined`

- **方案**：删掉 `WAVECAR`（或换一份来源不同的波函数）；也有"存在重叠原子"的说法；作者实测 `ALGO=All` 直接解决。

### 8.8 `ISMEAR=-2` + HSE 崩成 NaN（`Fatal error in PMPI_Bcast` / `PZSTEIN parameter number # had an illegal value`）

- **方案**：改算法标签——`ALGO=D`（`IALGO=53`）+ `LSUBROT=.TRUE.` 只能部分缓解（仍会吐 NaN）；**`IALGO=38` 或默认的 `ALGO=N` 可以顺利跑完**。

### 8.9 HSE 激发态计算的 `BUG card`

- **方案**：把 `ALGO` 从 `Damped` 改成 `Conjugate` 或 `All`（代价：慢约 3 倍，1000 原子 Γ 点实测）。

### 8.10 INCAR「长行」被截断（> 255 字符）

- **成因**：Fortran 记录长度限制，`MAGMOM`/`FERWE`/`FERDO` 这类长列表容易超。
- **方案**：先用压缩写法 `400*0.0`（省掉大量重复值）；仍不够时在 vasp-lib 的 `drdatab.F`（`RDATAB` 子程序）里 `#define LONGCHAR` 后重编译（上限约 32K）。

### 8.11 并行效率与核数设置（避免"核越多越慢"）

- `NBANDS ÷ 8` 是一个不错的**核数起点**。
- **先查两个数**：`grep irre OUTCAR`（不可约 k 点数，`KPAR` 的上界）、`grep NBANDS OUTCAR`（能带数）。
- **约束**：`KPAR ≤ 不可约 k 点数`；`NPAR` 要能整除 `NBANDS`；`NCORE × NPAR = 总核数`（故 `NPAR` 与 `NCORE` 只设其一）。
- **三条经验规则并存且会冲突**（`NPAR ≈ √NBANDS`、`NCORE` 取 `4~√核数`、核数起点 `NBANDS÷8`）——详见 `references/performance.md` §4.1，**以实测为准**。
- **按体系规模的经验**（小体系 `KPAR` 尽量大 + `NPAR=1`；中体系 `KPAR` 高 `NPAR` 低、`KPAR=节点数` 最佳；**增大 `KPAR` 优于增大 `NPAR`**；偷懒就 `NCORE=8` 且总核数为 8 的倍数）见 `references/performance.md` §4.2；VASP 6 的 hybrid MPI/OpenMP（`NCORE` 被 `OMP_NUM_THREADS` 取代、内部强制 `NCORE=1`）见 §4.3。
- 有多个 k 点时：`KPAR` 取「节点数」与「k 点数」中**较小的那个**，再把上一步得到的核数翻倍。
- 试跑后检查 `NGZ`：应当是**偶数**且**大于 3 × 每节点核数**；否则调整基组大小或每节点核数。
- 与 §2.3 相互印证：`NBANDS ÷ 核数` 过小（经验 < 5）容易触发 `Sub-Space-Matrix is not hermitian`。
- **`NCORE` 的经验取值**：`NCORE` = 一个轨道用几个核，`NPAR = 总核数 / NCORE`；经验范围 **`4` ~ `√(总核数)`**（常见 `NPAR = 4/6/8` 或 `NCORE = 12`）。⚠️ **`GW`/RPA 计算必须用默认 `NCORE=1`**（会明确提示）。
- **想从原理上决定「该用多少核/怎么取舍」**：见 `references/performance.md`——时间标度律（∝ `ENCUT³`、∝ `NELECT³`）、`LREAL`/`ALGO`/`NPAR`/`KPAR` 的取舍，以及「同时跑多个小作业优于先后跑一个大作业」的排队策略。

### 8.12 密勒-布拉菲指数（四指数切面）

- 六方/三方晶系的 `(hkil)` 四个指数**并不独立**：`i = -(h + k)`（例如 Ru 的 `(0001)` 面）。
- 写表面模型或 `KPOINTS`/`POSCAR` 注释时别把 `i` 当独立自由度。

### 8.13 关于"网上流传的 INCAR 片段"

- 社区问答类清单（如本文来源）给出的参数组合**大多针对特定体系**，直接照搬常常无效甚至更糟。
- 建议按「**现象 → 成因 → 单变量调整 → 复跑验证**」的次序动手：一次只改一类参数，并记录改前改后的收敛曲线。

### 8.14 vaspkit 差分电荷：`Different NGX, NGY and NGZ are adopted`

- **报错原文**：`Error: Different NGX, NGY and NGZ are adopted in between ./scf/CHGCAR and ./B/CHGCAR`
- **成因**：要相减的几份 `CHGCAR` **FFT 网格不一致**。各体系分别自洽时，VASP 会自动选 `NGX/NGY/NGZ`——
  换了 POSCAR（元素数/原子数变了）、换了核数或并行方式，网格就可能变，**即使 INCAR 参数看起来完全一样**。
- **定位**：在各自目录里 `grep NGX OUTCAR`，把三组数值摆在一起比。
- **解决**：把**同一套** `NGX/NGY/NGZ` 显式写进每个体系的 `INCAR` 后重算（通常取 AB 那组最大的值）。
  详细流程见 `workflows.md` 第十五节路线 B。


### 8.15 `No initial positions read in`（选择性动力学写错）

- **成因**：用了 `Selective dynamics` 但格式不完整——要么 `Selective dynamics` 那一行没加，
  要么**原子坐标后的 `T T T` / `F F F` 标志没有给每个原子都补齐**。
- **方案**：POSCAR 顺序必须是：… → 元素行 → 原子数行 → **`Selective dynamics`** → `Direct`（或 `Cartesian`）
  → **每一行坐标末尾都带 3 个 `T`/`F`**（要固定的写 `F F F`，不能只写一部分原子）。
- 相关：`workflows.md` 第一节（只想弛豫晶格、固定原子）。

### 8.16 `The number of bands is not sufficient to hold all electrons`（配 `ICHARG>10`）

- **报错原文**（节选）：`I found NBANDS = 180 NELECT = 12` +
  `ERROR: charge density could not be read from file CHGCAR for ICHARG>10`
- **成因**：`NBANDS` 看着很大（180 对 12 个电子绰绰有余）却仍报"能带不够"，问题出在 INCAR 里
  **限制了能量窗口（`Emin`/`Emax`）**，被选中的态不足以容纳全部电子；这个组合与
  "读 `CHGCAR` 做非自洽（`ICHARG=11/12`）"互相冲突。
- **方案**：**去掉 `Emin`/`Emax`** 后重跑（报错本身也提示：若要只算选定态，应改用 `EFERMI` / `EREF`）。
- ⚠️ 社区反馈：也有人注释掉 `Emin`/`Emax` 后仍报同样错误（原帖未给出后续答案）；
  这种情况下优先确认 `ICHARG` 与 `CHGCAR` 的配套关系、以及 `NBANDS` 是否真的够。

### 8.17 NEB：`FOR ELEMENT n ... ATOMS IN FILE 1 IS: x` / `ATOMS IN FILE 2 IS: y`

- **成因**：NEB 的**初态与末态结构对不上**——原子顺序或某元素的原子数不一致
  （例：file 1 里某元素 1 个原子，file 2 里 2 个）。
- **方案**：把初末态的原子**一一对应**（同元素、同顺序、同数目）；两端都要与各自的 `POSCAR`/`CONTCAR` 自洽。

### 8.18 `Warning from LATTYP: Monoclinic adjustement (A1->A3, A2->A1, A3->A2)`

- **报错原文**（节选）：`Warning from LATTYP: Got some problem with cell dimensions! ... LATTYP: Found a simple monoclinic cell.`
- **成因**：给的晶胞**太大或不是原始晶胞**，VASP 在识别单斜格子时自行重排基矢并给出警告。
- **方案**：**改用原始晶胞（primitive cell）**；必要时在 INCAR 里加 **`ISYM=-1`**（关掉对称性）让它照原样算。

### 8.19 `For optimal performance we recommend to set NCORE= 4 - approx SQRT(number of cores)`

- **性质**：这是**性能提示，不是错误**（很多人会当成报错贴出来）。
- **含义**：`NCORE` 决定"几个核共同处理一个轨道"，`NPAR = 总核数 / NCORE`；默认 `NCORE=1`
  在现代多核机器上可能**极其低效**。经验取 **`4` ~ `√(总核数)`**，如 `NPAR = 4/6/8` 或 `NCORE = 12`；
  社区记录里设 **`NCORE=8`** 后提示消失。
- ⚠️ `GW`/RPA 必须沿用默认值（HF 支持 `NCORE` 但测试不充分）。
- 💡 **如果它出现在 `OUTCAR` 开头、而计算正常结束了，可以直接忽略**——无论计算成功与否它都会打印（见 `references/onboarding.md` §9.1 第 2 部分）。

### 8.20 k 点网格与对称性不匹配（HF 类计算会提示收敛慢）

- **报错原文**：`Your generating k-point grid is not commensurate to the symmetry of the lattice ...`
  或 `HNFORM: k-point generating vectors and reciprocal lattice are incommensurate.`
- **成因/适用**：k 网格与晶格对称性不匹配（HF/杂化泛函尤其会提示"k 点收敛慢"）。
- **方案**：① 用**自动 k 点生成**；② **把网格移到 Γ 中心**——KPOINTS 里从 Monkhorst-Pack 改成 **Gamma**。
- **背景（为什么 Γ 与 MP 不一样）**：两者只在某一方向为**偶数**时不同——**Gamma 一定含 Γ 点**，
  **MP 只有三个方向都取奇数时才含 Γ**；含不含 Γ 会影响不可约 k 点数与精度，所以用 MP 时通常取奇数。
  （另见 `workflows.md` 第十五节路线 B 关于 MP/Gamma 的说明。）
  ⚠️ **但「该不该含 Γ」社区里有两种相反的经验，取决于体系与用途**：
  - **不采 Γ 派**：Γ 点对称性最高、能带常在 Γ 处取极值，所以它**权重低、代表性差**——
    对**立方、正交**等格子，有人主张用 **MP 偶数**（不刻意取 Γ）；
  - **采 Γ 派**：**六方格子是例外**——用 MP 偶数会让撒点的对称性低于实空间格子，
    **不可约 k 点会变成 Gamma 法的约 3 倍（计算时间也约 3 倍）**，所以六方用 **Gamma** 更省；
    另有社区反馈：**有时候不含 Γ 点会直接报错**（杂化/HF 类尤其如此）。
    （本库**第三个来源**（公众号《VASP学习交流》的 KPOINTS 教程）也持同样看法：六方若用 M 点，「M 平移之后网格的对称性和晶胞的对称性会出现不匹配，从而**导致计算出错**」。）
  - **实践判据**：先看**不可约 k 点数**（`grep irre OUTCAR`）与耗时，再用收敛性测试定**密度**（`workflows.md` §二十八）；密度档位可直接参考 VASPKIT 的 KP-resolved 值（Low `0.08~0.05` / Medium `0.04~0.03` / Fine `0.02~0.01`）。
  - 💡 **想用显式 k 点列表**：VASP 自动生成 k 点时会把简约化后的不可约 k 点写进 **`IBZKPT`**，可以直接把里面的数据拷进 `KPOINTS` 使用（见 `references/onboarding.md` §九）。

### 8.21 能量凭空差 10+ eV（不是报错，但结果明显不对）

- **症状**：算同一个体系的总能，与他人/别的设置相差 **10 eV 以上**。
- **排查顺序**：
  1. **有没有考虑范德华力**——层状/吸附体系差异很大（社区记录用 `LVDW=.TRUE.`）；
  2. **`POTCAR` 的元素顺序是否与 `POSCAR` 一致**——顺序反了等于换了元素，差个十几 eV 很正常（见 §1.4）。

### 8.22 NEB：`WARNING: BASIS VECTORS ARE NOT THE SAME`

- **报错原文**（节选）：`BASIS ELEMENT 0 0 ... IS IN FILE 1: 5.26490755750692 / IS IN FILE 2: 5.26349913998309`
  `I HOPE YOU KNOW WHAT YOU ARE DOING`
- **含义**：NEB 的初末态**晶胞基矢不一致**（示例里差约 1.4×10⁻³ Å），VASP 无法把它们当成同一格子处理。
- **方案**：让初末态**共用完全相同的晶胞**（把一端的晶胞块复制到另一端，或两端用同一 `POSCAR` 模板分别弛豫到
  同一格子），并保证原子顺序一致。
- 说明：此条来自原帖评论区提问（**原文未给出答案**），这里按 VASP 输出的含义整理，采纳前请自行核对。

### 8.23 `Spin polarized Harris functional dynamics is a good joke ...`

- **含义**：这条提示通常意味着你**把静态计算当 MD 跑了**——社区记录的原因是**忘记设 `NSW=0`**。
- **方案**：静态/单点计算务必 `NSW=0`（配 `IBRION=-1`）；确实是 MD 时才保留 `NSW>0` 并给出 `POTIM`/`TEBEG`。


### 8.24 非自洽步改了 `ENCUT`/`EDIFF` → `CHGCAR` 维数不同 / `WAVECAR` cutoff 不同 / 力不正确

- **典型现象**（做能带、DOS 等非自洽计算时最常见）：
  - `WARNING: dimensions on CHGCAR file are different`（**`CHGCAR` 维数不同**）；
  - 读 `WAVECAR` 时报 **cutoff 不同**；
  - 以及 **"力不正确"** 一类的警告。
- **成因**：把非自洽步的 INCAR 改动了——**`ENCUT`（以及 `EDIFF` 等）与上一步自洽计算不一致**。
  `ENCUT` 一变，**FFT 网格（`NGX/NGY/NGZ`）就跟着变**，上一步写出的 `CHGCAR` 维数自然对不上
  （机理与 §8.14 相同；`WAVECAR` 也带着自己的 cutoff）。
- **方案**：
  1. **非自洽步除"该改的开关"外，其余参数与自洽步保持一致**——通常只加
     **`ICHARG=11`**（固定电荷密度）与 **`LORBIT=10`/`11`**（投影），
     并设 **`LWAVE=FALSE`**（这一步不需要再写波函数）；
  2. 若确实需要改 `ENCUT`：那就**从头重跑自洽**（或干脆用统一 `ENCUT` 重做整个流程），
     **不要**拿旧 `CHGCAR` 直接接着算；
  3. 用 `grep NGX OUTCAR` 对比两步的 FFT 网格，可快速确认是不是这个问题（见 §8.14）。
- **适用场景**：能带 / DOS 的"自洽 + 非自洽"两步法、HSE 的 `hse-scf` → `band`（见 `workflows.md` §29.4）。
- **来源**：`articles/20261001-VASP计算能带结构_HSE杂化泛函.md`（作者记录的真实报错与解法）。



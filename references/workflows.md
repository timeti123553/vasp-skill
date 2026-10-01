# VASP 计算流程生成参考

本文件用于「VASP 计算流程生成」任务：用户表述想算的性质（如"算能带""算磁性""算声子谱""算热导率/热电 ZT"），据此输出一套**基于 VASP 的完整计算流程**：先做什么后做什么、每步的关键 INCAR/KPOINTS/POTCAR 设置、提交与验证方式，并可调用 `scripts/gen_inputs.py` 自动生成输入文件。

## 流程选择（先判断）

| 用户要算的性质 | 主流程 | 依赖前置 |
|---|---|---|
| 结构/几何 | 结构优化 `opt` | 无 |
| 总能量、能带、态密度 | 优化 → `scf` → `band`/`dos` | 先优化 |
| 磁性（自旋、非共线、SOC） | 优化(含磁构型) → `mag` scf → 属性 | 磁构型初猜 |
| 声子谱 / 晶格动力学 | 高精度优化 → 有限位移（phonopy 或 ALAMODE）| 力收敛足够 |
| 晶格热导率 / 三声子四声子 | 声子超胞位移 → 拟合 → 散射速率 | 前三/四阶力常数 |
| 热电性质（Seebeck / 电导 / ZT） | scf → 输运（BoltzTraP2 等）| 电子结构 |
| 成键强度分析（COHP / COOP / ICOHP） | 优化 → scf(写WAVECAR) → LOBSTER | 收敛后的波函数 |
| 理想拉伸 / 剪切（应力应变曲线、理想强度） | 准静态施加应变序列（`ISIF=4` + `OPTCELL`）→ 逐步优化 | 优化好的晶胞 + 分数坐标 POSCAR |
| 施加任意外压（非静水压、多轴应力） | 迭代调晶格：读 `OUTCAR` 应力 → 胡克定律更新应变 → 逼近目标 | `ISIF=2` + 正交胞 |
| 二维势能面（PES / GSFE）与 MEP | 批量静态计算取能量 → `PES.data` → string 法找 MEP | 每个点同口径的单点能 |
| AIMD 轨迹分析（RDF / RMSD / 速度自相关 VACF） | 跑完 AIMD → 转 GROMACS 轨迹 → `gmx` 分析 | 有 `OUTCAR`/`XDATCAR` |
| 差分电荷密度 / 平面平均差分（成键电荷转移） | AB、A、B 三次同格子自洽 → `CHGCAR` 相减 → 平面平均 | 同 cell/`NGX-NGY-NGZ`/k 点，A、B 沿用 AB 的原子位置 |
| 载流子迁移率（二维，形变势法） | 优化 → scf → band → ±2% 应变序列（含泊松效应） → 拟合 `m*`/`E₁`/`C₂D` → μ | 方形超胞 + 真空能级 |
| 二维材料介电常数 / 光学性质 | ⚠️ **不能把 3D 定义直接套到 2D**：需按 2D 定义处理真空层（`VASPKIT` ≥ 1.10.beta3 可处理二维光学） | 足够厚的真空层 + 2D 公式 |
| 弹性常数 / 杨氏模量 / 泊松比 | 充分弛豫 → `IBRION=6`、`ISIF=3`、`NFREE=4`、`NSW=1` → 提取弹性矩阵 → 求柔度矩阵 → 各向异性 `E`/`ν` | 弛豫好的结构；2D 需固定 c 轴 |
| STM 模拟（恒高 / 恒流） | 自洽（留 `CHGCAR`/`WAVECAR`）→ `LPARD`/`NBMOD`/`EINT` 生成 `PARCHG` → `vaspkit 325` 或 **`STM-2DScan.py`** 出图 | 已收敛的 `WAVECAR`；恒流要额外搜高度 |
| 从 OUTCAR 提取任意量并出图 | `re` 正则抓取 → `pandas` 整理 → 画图 + 存 CSV（脚本化后命令行直接跑） | 有 `OUTCAR`；本机 python + pandas |
| 机器学习势数据集（FitSNAP 等） | 跑 AIMD/多构型 → 从 `vasprun.xml` 逐步提取「能量/晶格/位置/受力/应力」→ 写成带单位声明的 JSON | 多帧 `vasprun.xml` + 元素列表 |
| 高温声子谱（非谐显著） | MD 取构型 → `alm` 提力常数（LASSO 四阶）→ `anphon` 跑 SCPH → 各温度声子谱 | ALAMODE + MD 轨迹 |
| 波恩有效电荷 / 极化（铁电、LO-TO 劈裂） | 优化 → 静态 scf → `LEPSILON=.TRUE.`（DFPT，一次算完）或 `LCALCPOL` + 手动位移拟合 | 收敛好的 scf；`P = Z*·u` |
| 吸附能 / 掺杂能 | 分别算「吸附物/掺杂原子」「干净表面」「复合体系」→ 能量相减 | **同一格子 + 同一套参数** |
| 离子迁移能垒（扩散势垒） | 路径等距插点粗算 → NEB / CI-NEB 精算 | 稳定的初末态 |
| Wannier90 紧束缚模型（TB / 能带插值 / 拓扑） | 常规 scf → 能带分析找 E_F 附近轨道 → Wannierization（`wannier90.win` + `LWANNIER90=TRUE`） | 带 `LWANNIER90` 接口的 VASP + wannier90 |
| AIMD 热稳定性验证（某温度下结构稳不稳） | 优化 → Γ 点大胞 NVT/NPT 跑 ≥10 ps → 看能量时间序列有无漂移 + 看轨迹结构 | 扩胞 ≥100 原子；Andersen 热浴 |
| 有效质量（电子 / 空穴） | 优化 → scf → 能带取带边 → 带边附近 E-k 二次拟合（或 VASPKIT 911/912/913） | 带边附近的加密 k 点 |
| 收敛性测试（k 点 / ENCUT） | 固定 ENCUT 扫 k 间距 → 固定 k 间距扫 ENCUT → 画 E–参数曲线取走平处 | `POTCAR` + `POSCAR`；建议用脚本批量跑 |
| 杂化泛函能带（HSE06） | PBE 优化 → （可选 HSE 优化）→ **251 生成混合 KPOINTS** → 先用 PBE 存好 `WAVECAR` → 改 HSE 参数再算一次 → **252 提能带** | 原胞 + PBE 的 `WAVECAR`；计算量约几十倍于 PBE |
| 高通量筛选 | 批量 opt/scf + 属性 | pymatgen 工作流 |

> 通用原则：**先几何优化，再静态自洽，最后算属性**。属性计算必须建立在收敛良好的自洽电荷密度/波函数之上。对力敏感的（声子、输运）要更严的收敛判据。

---

## 一、结构几何优化（workflow=`opt`）

- **目的**：得到局域能量极小的原子位置/晶胞。
- **关键 INCAR**：
  - `PREC=Accurate`（或 `Normal` 起步）
  - `IBRION=2`（CG）或 `1`（RMM-DIIS）；`NSW=200` 左右
  - `ISIF`：只动原子 `2`；动原子+晶胞 `3`（需谨慎，先原子后晶胞分两轮更稳）
  - `EDIFF=1E-6`，`EDIFFG=-1E-2`（力判据，负值）粗，`-1E-3` 精
  - `ISMEAR`：金属 `1`（`SIGMA=0.1`~`0.2`），绝缘体 `0`；`NELM=60`+
  - 磁性体系加 `ISPIN=2`、`MAGMOM`
- **KPOINTS**：`Automatic` 网格，密度按体系（绝缘体/金属），粗→细两轮。
- **验证**：`grep "reached required accuracy" OUTCAR`；看 `OSZICAR` 离子步能量/力随步收敛；确认没有明显虚频前兆（对声子流程）。
- ⚠️ **`EDIFFG` 的力判据只约束「非固定原子」**：用 `Selective dynamics` 固定住的原子（坐标后写 `F F F`）**不受这个阈值限制**——所以**只要体系里有固定原子，即使判据已满足，`OUTCAR` 里的「原子最大受力」仍可能大于 `|EDIFFG|`**。**检查力收敛时必须把固定原子排除掉**，否则会误判。
  - 想看**每个离子步的最大受力（已排除固定原子）**：用本库参考脚本 `scripts/reference/force_conv.sh`（作者 @叠加态/lipai，需系统里有 `gnuplot`，它用 `set term dumb` 直接在终端画曲线）；如果是 **VTST 版**（能算 NEB 的那版）也可以用官方脚本 **`vef.pl`**（见 `references/tools.md` §4.13）。
  - 手工查看的位置：`OUTCAR` 里每个离子步的 **`POSITION` … `drift`** 区块（`grep -A ... 'POSITION' OUTCAR`），或用 `vi` 搜 `?TOTAL-FORCE`。
- **弛豫要「在一个离子步内收敛」**：弛豫过程中晶格与基组会变化，若最后一步原子仍在明显移动，得到的能量/力与最终结构并不自洽。第一次通常做不到，**把 `CONTCAR` 复制成 `POSCAR` 再弛豫一轮**，反复直到「一跑就收敛」（`grep "reached required accuracy" OUTCAR` 且只走了 1 个离子步）。
  ⚠️ **金属做结构弛豫（或任何涉及力的计算）不要用 `ISMEAR=-5`**（四面体法），用 `ISMEAR=0`（或 `1`）；`-5` 只适合静态能量、DOS 这类不带力的计算。
- **想要畸变相（铁电、姜-泰勒等）必须手动破缺对称**：VASP **不会**把原子从高对称位置自发推离——先用 `ISIF=3` 优化出晶格常数（此时原子仍停在对称位），再把目标原子沿要畸变的方向挪一点点（例：Ba `0 0 0` → `0 0 0.01`），然后改 `ISIF=2` 只弛豫原子；**位移量会影响最终落点**（原文的说法：「你不推它一下，它自己懒得动弹」），必要时加大 `NSW` 多优化几轮，最后用 `CONTCAR` 里归一化后的位移比对照文献。
  这条与 `errors.md` §3.1 的「高对称陷阱」是同一件事的两面：那边是**不想要**畸变却被高对称卡住，这边是**想要**畸变就必须先破缺。
- **只想弛豫晶格、固定原子位置**：在 POSCAR 晶格常数三行之后加一行 `Selective dynamics`，再接 `Direct`，然后**给每个原子坐标后面加 `F F F`**（三个方向都固定），配 `IBRION=2` + `ISIF=3` 即可。比整胞冻结更细；另一种思路是 `errors.md` §4.7 的 `constr_cell_relax.F` + `OPTCELL`。
#### 分步优化（粗 → 精）：新搭结构 / 带缺陷的大体系强烈建议这么做

> 场景：**手动搭的新结构、缺陷（间隙原子/空位）、元素替换、表面吸附物**——这些初始结构常离"合理结构"很远。
> 做法是**先用低精度参数把它快速推到合理位置，再用高精度收尾**；原文指出对构建了缺陷的大体系**能省一半以上机时**。

**Step 1（粗优化）**：

```
PREC   = M
ISPIN  = 1          # 还不确定有无磁性时先关掉
EDIFF  = 1E-04      # 体系小 / 离合理结构近 → 1E-05
EDIFFG = -0.05      # 小体系 -0.03；很大的体系 -0.08
LREAL  = Auto       # >20 原子用 Auto；<20 用 .FALSE.
NSW    = 200        # 跑满 200 步仍不收敛也没关系——"拿到较合理结构"这个目的已达到
IBRION = 2
ISIF   = 3          # 有时用 2 也不错
ISMEAR = 0 ; SIGMA = 0.1
ISYM   = 0          # 还不知道合理对称性，先关掉
# k-spacing ≈ 0.03 ~ 0.04 Å⁻¹
```

**Step 2（精优化）**：

```
PREC   = N
ISPIN  = 2          # 确认无磁性可用 1
EDIFF  = 1E-06
EDIFFG = -0.01
LREAL  = Auto / .FALSE.
NSW    = 200
IBRION = 2
ISIF   = 3
ISMEAR = 0 ; SIGMA = 0.1
ISYM   = 2          # 把 step1 的结构导回建模软件，按 0.05~0.1 Å 精度找对称性并加上
# k-spacing ≈ 0.02 ~ 0.025 Å⁻¹
# POTIM 一般不调；多次不收敛就调小并配 IBRION=1
```

- **step1 之后先判断是金属还是半导体**，再定展宽：**半导体 `ISMEAR=-5`**；**金属 `ISMEAR=1, SIGMA=0.1`**
  （或继续用 `ISMEAR=0`，但按 `EENTRO` 调 `SIGMA`，**尽量让 `EENTRO/atom` 落在 1~2 meV**）。
  - ⭐ **怎么「快速判断金属还是半导体」（社区经验，出处见下）**：第一步粗优化时用 **`ISMEAR=0` + `SIGMA=0.1`**，
    算完看 `OUTCAR` **最后一个 `EENTRO`**，用 **`EENTRO / 原子数`** 判断：
    - **> `1 meV` → 金属**；
    - **< `0.1 meV` → 半导体**（这个值极小，比如 `1e-6` 量级时，**带隙一般较大**）；
    - 落在 `0.1 ~ 1 meV` 之间：**原文作者也「没有具体测试过，不确定」**（按金属/半导体两头取保守设置）。
  - **原理**：金属在 `ISMEAR=0`（高斯展宽）下费米面处出现**分数占据** → `EENTRO ≠ 0`；带隙足够大时
    `SIGMA=0.1` 还不足以造成分数占据 → `EENTRO = 0`（**`SIGMA` 若大到离谱，`EENTRO` 也会不为 0，但那种计算本身有问题**）。
  - ⚠️ **适用边界**（作者自己声明的）：这是**个人经验**，大部分情况正确、**不保证所有体系**；
    **若弛豫过程中晶格变化很大**，平面波截断球已严重变形、自洽收敛到的状态本身误差大，此时判断不可靠——
    **解决办法：拿弛豫后的结构再做一次弛豫**，然后再用这个方法判断。

- ⚠️ **收尾判据（原文习惯）**：比较 `POSCAR` 与 `CONTCAR` 的晶格常数，**差值 > 1% 就再用 `CONTCAR` 优化一轮**——
  优化过程中平面波基组对 `CONTCAR` 的描述可能已有偏差，哪怕 step2 显示"收敛"。

**对称性经验（与 `errors.md` §3.1「高对称陷阱」同源）**：

- 加**合理**对称性会**加快**收敛（不可约 k 点变少、原子只在对称允许的方向移动）；加**不合理**对称性会出问题；
- **弛豫过程中对称性可以升高，但不会降低**；
- ⭐ **实例**：往纯平面二维材料里掺过渡金属（TM）时，**若 TM 与材料共面，TM 在垂直方向的受力恒为 0**
  （即使 `ISYM=0`）→ 弛豫后**仍是纯平面**；**只要把 TM 稍微挪出平面**，弛豫后就出现起伏、**能量明显更低**；
- **掺间隙原子 / 做元素替换时，建议手动挪几个关键原子，让初始结构尽量只有 `P1` 对称性**，
  避开势能面上的特殊点——往往能得到更低的能量；
- 对称性判错还会影响电子结构：石墨烯若被当成 `C2h`（而不是 `D6h`），`a ≠ b`、夹角偏离 120°，
  **高对称 K 点会偏移**，与 K 点有关的量就带误差。
- **`MAGMOM` 与磁态点群**：**只有绝对值和分布影响磁态对称性，正负号不影响**——例：CrI₃ 的
  `MAGMOM = 6*0 2*3` 与 `6*0 3 -3` 都是 `D3d`，而 `6*0 3 3.5` 变成 `D3`。

- **`ISIF` 的分步用法**：复杂体系可先 `ISIF=2`（只动原子）快速弛豫，再 `ISIF=3`（连晶格）；
  二维材料（真空足够）常用 `ISIF=3` 并**固定 c 方向**（改 `constr_cell_relax.F`，见 `errors.md` §4.7）。
- **`POTIM`**：极度不合理的结构第一步可**加大到 ~0.2** 让它快些移动；**在极小值附近来回振荡不收敛时调小并配 `IBRION=1`**。
- **出处**：公众号《学术之友》文章《聊一聊结构优化》
  （`articles/20261001-聊一聊结构优化.md`，作者署名「中科大无缺」）。

#### 几条通用经验（出自 PWmat 官方文档的「结构优化建议」，VASP 同样适用）

> 出处：田洪镇《计算大牛教你优化结构》（PWmat 的推广文）。**参数名是 PWmat 的**，下面同时给出 VASP 的对应手段。

- **SCF 不收敛就别硬让离子动**：一边电子步不收敛、一边让离子跑，**结构很可能直接跑散**；
  先确认电子步收敛（VASP：看 `OSZICAR` 的 `dE` 与 `rms(c)`），不行就杀掉重来。
- **SCF 正常但离子步不收敛**时，可以依次试：
  - **金属 / 费米面附近态多**的体系：**加大展宽**（PWmat 从 `0.025` → `0.1~0.15`）→ **VASP：加大 `SIGMA`**；
  - **绝缘体**：**加大电荷混合**（PWmat 的 `imax` 由 `1.0` → `1.05~1.08`）→ **VASP：调 `AMIX`/`BMIX`**；
    ⚠️ 但**大金属体系强行加大混合可能让 SCF 更不稳、结构乱掉**（与 `references/incar.md` 的混合参数条目一致）；
  - **提高「展开电荷密度那一步」的截断能**（PWmat：`Ecut2 = 4·Ecut`）能让**总能与受力随离子步的曲线更平滑、
    明显利于收敛** → **VASP 的对应手段是 `PREC=Accurate` 与 `ADDGRID=.TRUE.`**（它们控制的正是 FFT 网格/密度展开）。
- **大体系尽量别做晶格优化**：`ENCUT` 不够大时**优化出来的晶格并不准**，可能要反复优化；
  **没有必要时别开 `ISIF=3`**（或只优化一次晶格，之后固定晶格只优化原子位置）；确实要优化就把 `ENCUT` 给足。
- **先想清楚是不是所有原子都要优化**：表面 / 吸附模型可以**固定基体下层（例如固定下面两层），
  只优化上面两层 + 吸附物**——既省机时，也更贴近「半无限晶体」的实际物理。
- **HSE 慎做结构优化**：一般只用于小体系或「规范的大体系」（如体相里带一个点缺陷）；
  💡 **先用 PBE 预优化、再用 HSE 收尾**，能显著减少 HSE 的离子步数（VASP 里就是 PBE 跑一遍 `opt` 再拿 `CONTCAR` 开 HSE）。
- **懂得适可而止**：若最大受力已经很小却总也达不到判据，**画「总能 vs 离子步」图**——曲线走平就说明到了方法/软件的极限，
  可以停：**总能波动 ≈ `0.1 meV` 就算收敛得足够好（尤其 >100 原子的体系）**；原文也明确
  **受力标准没必要卡 `0.01 eV/Å`，大体系 `0.02~0.05 eV/Å` 即可**（与 `errors.md` §3.1 的参考值一致）。

- ⭐ **"迭代弛豫"到一个离子步内收敛**（社区做法，本人文章）：
  **弛豫计算应尽量保证"整个弛豫在一个离子步内算完"**——因为弛豫过程中**晶格大小与平面波基组可能会变**，
  一步算完的结果更精确（基组与结构自洽）。首次弛豫往往做不到一步收敛，**做法是：把 `CONTCAR` 复制成 `POSCAR`
  再弛豫一次，如此反复，直到它在一个离子步内收敛**（`OUTCAR`/`OSZICAR` 里只有 1~2 个离子步）。
  这与"分步优化"（§一上方的粗→精）是两种不同的加速/提精思路，**可以结合使用**。
- ⚠️ **金属体系的弛豫不要用 `ISMEAR=-5`**，应取 `ISMEAR ≥ 0`（`0`/`1`/`2`）；`-5` 适用于静态/DOS 这类取能量的步骤
  （第二来源印证，见 `errors.md` §2.1）。

- 生成命令：`python scripts/gen_inputs.py -s POSCAR -w opt`

---

## 二、静态自洽（workflow=`scf`）

- **目的**：在固定结构上自洽收敛出电荷密度 `CHGCAR`/波函数，供能带、态密度、输运复用。
- **关键 INCAR**：
  - `IBRION=-1`（不做离子步）、`NSW=0`
  - `ISMEAR=-5`（四面体法）适合绝缘体/半导体态密度；金属仍可用 `1`
  - `NELM` 足够；`LCHARG=.TRUE.` 写 CHGCAR；`LWAVE=.TRUE.`
  - 磁性：`ISPIN=2` + `MAGMOM`
- **KPOINTS**：比优化更密的网格（能带/态密度质量依赖 k 点）。
- **验证**：电子步收敛到 `EDIFF`；`OUTCAR` 末尾能量稳定。
- 生成命令：`python scripts/gen_inputs.py -s POSCAR -w scf`

---

## 三、能带（workflow=`band`）

- **目的**：沿高对称 k 路径给出色散关系。
- **步骤**：`opt` → `scf`（最好同一 `CHGCAR`/`WAVECAR`）→ `band`。
- **关键 INCAR**：
  - `IBRION=-1`、`NSW=0`、`ISMEAR=0`（半导体）或 `-5`
  - `ICHARG=11`（读 CHGCAR，不做自洽）、`LORBIT=11`
  - 沿用 scf 的 `PREC`/`ENCUT`/`ISPIN`/`MAGMOM`
- **KPOINTS**：`Line-mode` 高对称路径。用 pymatgen `HighSymmKpath` 自动生成，避免手写分数坐标出错。
- **验证**：`vasprun.xml` 能读出每条带；检查带隙/带宽与文献一致。
- 生成命令：`python scripts/gen_inputs.py -s POSCAR -w band`

### 能带图的另一种出法：VASPKIT 出数据 + Origin（手工设 K 点刻度）

> 出自本人文章 `articles/20261001-VASP_vaspkit_Origin_画能带图.md`（案例：**二维 MnPS₃，铁磁半导体**）。
> 不想写脚本、习惯 Origin 的同学走这条。

**流程**：

1. 弛豫（同 §一；二维材料照样 `ISIF=3` 并把真空方向留足）；
2. **能带步**：把 `INCAR`、`CONTCAR`、`POTCAR`、**`CHGCAR`** 与提交脚本拷进新目录 → `cp CONTCAR POSCAR`；
   ⚠️ **务必把 INCAR 里的 `NSW` 改成 `0`**；
3. ⭐ **最省事且无歧义的参数组合**：**`ISTART = 0`（不读 `WAVECAR`）+ `ICHARG = 11`（读 `CHGCAR` 并固定）**
   ——这样只需拷 `CHGCAR` 一个"上一步产物"，不必纠结要不要带 `WAVECAR`；
4. **K 点路径**：`vaspkit → 3 → 302`（**二维**）/ `303`（**三维**）→ 生成 `KPATH.in` → **复制为 `KPOINTS`**；
5. 提交计算 → **`vaspkit → 21 → 211`** → 得到 **`BAND.dat`**；
6. 💡 **带隙直接查 `BAND_GAP` 文件**（示例：MnPS₃ 总带隙 **0.6491 eV**），不必自己去数两条线的最小间距。

**用 Origin 画能带（8 步，重点是第 7 步）**：

1. 把 `BAND.dat` 拖进 Origin；
2. 绘图 → **折线图**；
3. 设定 X、Y 轴对应的列，确定；
4. 点 **Y 轴 → 刻度**：改**起始值**与**主刻度值**；
5. Y 轴标题改 **`E(eV)`**、**线宽设为 2**；**自旋极化时两条线分别注释为 `up` / `down`**；
6. 打开**静态/能带目录里的 `KLABELS`**——里面是各高对称点在横轴上的位置；
7. **把 X 轴取值范围设为**（按自己的 `KLABELS`）**如 `0.000 ~ 1.523`**；再把**主刻度类型改为「按自定义位置」**，
   在下面**输入各个 K 点的位置**；然后在**刻度线标签 → 显示 → 类型 → 刻度索引字符串**里，
   **按 `KLABELS` 的顺序把高对称点符号（Γ、X、M…）填进去**，确定；
8. 出图（这就是"横轴带高对称点标注"的能带图）。

**与其它两条路线的关系**：脚本化出图见 §二十（从 `OUTCAR` 直接抓）与 §29.5（`vaspkit 252` 自动画 `band.png`）；
本节是**纯手工 GUI 路线**，好处是样式完全可控。

**案例里的磁性设置**（可当模板）：**MnPS₃** 是铁磁半导体，**Mn 的预期磁矩 ≈ 4.8 μ_B → `MAGMOM` 初始值直接写 `5`**
（`MAGMOM = 2*5 2*0 6*0`）——**"写一个接近真实磁矩的值"比随便写 `1` 收敛更快**；
`SYMPREC` 也顺手设成了 `1E-4`（默认 `1E-5`）。

### 能带与 DOS 的 Python 包路线（`vaspvis` / `pymatgen`）

> 出自本人文章 `articles/20261001-画能带_Band_和态密度_DOS_图--Python包.md`（案例 UO₂）。
> 两个包都能**独立画能带、画 DOS，也能把两张图画在一起**。**选哪个先看这条差别**：

| 包 | **画图前目录里必须有什么** | 特点 |
| --- | --- | --- |
| **`vaspvis`** | **`EIGENVAL`、`PROCAR`、`KPOINTS`、`POSCAR`、`INCAR`**（五个都要） | 接口极简，一行一个图；**能带 + DOS 联合图很方便** |
| **`pymatgen`** | **只要 `vasprun.xml`** | 与 `gen_inputs.py` 同源；`BSDOSPlotter` 可做联合图 |

- 安装：`pip install vaspvis` / `pip install pymatgen`（建议 anaconda 环境）；
- 文档：`vaspvis` <https://vaspvis.readthedocs.io/en/latest/index.html>（GitHub: <https://github.com/DerekDardzinski/vaspvis>）；
  `pymatgen` <https://pymatgen.org/index.html>（GitHub: <https://github.com/materialsproject/pymatgen>）；
- ⚠️⚠️ **希腊字母（Γ）的坑**：若想让能带图横轴显示 `Γ` 等高对称点希腊字母，
  **必须把 `KPOINTS` 里的 `GAMMA` 全部同时改成 `\Gamma`**——**只改一部分的话，一个都不会显示**（两个包都一样）。

**`vaspvis` 速查**（`from vaspvis import standard`）：

| 调用 | 用途 |
| --- | --- |
| `standard.band_plain(folder=..., figsize=(5.5,3), save=True)` | 总能带图（`save=True` → `band_plain.png`） |
| `standard.band_plain_spin_polarized(folder=..., figsize=(6,3))` | 自旋向上/向下分开显示 |
| `standard.band_elements(folder=..., elements=['U','O'], figsize=(6,3), save=True)` | 按元素投影的能带 |
| `standard.dos_orbitals_spin_polarized(folder=..., orbitals=[0,1,2,3,4,5,6,7,8], energyaxis='x')` | 各轨道 + 总 DOS |
| `standard.dos_elements_spin_polarized(folder=..., elements=['U','O'], energyaxis='x')` | 按元素的 DOS |
| `standard.dos_atom_orbitals_spin_polarized(folder=..., atom_orbital_dict={0:[1,3], 1:[1,7]}, energyaxis='x', total=False)` | **指定原子 + 指定轨道**（`{原子序号: [轨道序号]}`） |
| `standard.band_dos_plain_spin_polarized(band_folder=..., dos_folder=..., save=True)` | **能带 + DOS 画一起** |
| `standard.band_dos_orbitals_spin_polarized(band_folder=..., dos_folder=..., orbitals=[0,1,...,8], save=True)` | 能带 + 轨道分辨 DOS 一起 |

> 💡 最后一个**会出两张图**：**颜色对应"轨道"这个维度、自旋又是另一个维度**，只能分成上下自旋两张画。

**`pymatgen` 速查**：

```python
from pymatgen.io.vasp import Vasprun
from pymatgen.electronic_structure.plotter import DosPlotter, BSDOSPlotter
from pymatgen.electronic_structure.core import OrbitalType
import matplotlib.pyplot as plt

v = Vasprun('./vasprun.xml')

# ① spd 投影 DOS
DosPlotter().add_dos_dict(v.complete_dos.get_spd_dos())
# ② 元素投影 DOS： v.complete_dos.get_element_dos()
# ③ 元素 + 轨道：   v.complete_dos.get_element_spd_dos('U')[OrbitalType.f]

plotter = DosPlotter()
plotter.add_dos_dict(v.complete_dos.get_element_dos())
plotter.get_plot(xlim=[-10, 5], ylim=[-25, 25])
plt.savefig('dos_element.png')
```

**能带 + DOS 联合图（`BSDOSPlotter`）**：

```python
bs_data  = Vasprun("./vasprun.xml", parse_projected_eigen=True).get_band_structure(line_mode=True)
dos_data = Vasprun("./vasprun.xml").complete_dos

fig = BSDOSPlotter(bs_projection=None, dos_projection=None,
                   vb_energy_range=5, fixed_cb_energy=5, fig_size=(16, 12))
fig.get_plot(bs=bs_data, dos=dos_data)
plt.savefig('banddos_fig.png')
# 按元素投影：BSDOSPlotter(bs_projection="elements", dos_projection="elements", fig_size=(16,12))
```

- `parse_projected_eigen=True` 是画联合图/投影图时**读 `vasprun.xml` 的必需项**；
- `vb_energy_range` / `fixed_cb_energy` 分别控制价带、导带在图上各留多少能量范围。

### `vaspkit` 取能带/DOS 数据的档位与几个细节（含三条高频疑问）

> 出自一篇社区教程 `articles/20261001-VASP_vaspkit计算能带结构_态密度.md`
> （VASP + vaspkit + OriginLab，三步：`scf/` → `band/` → `dos/`）。

**`vaspkit` 的档位**：

| 命令 | 产物 | 说明 |
| --- | --- | --- |
| `vaspkit → 21 → 211` | **`BAND.dat`** | 普通能带数据（可直接进 Origin） |
| `vaspkit → 21 → 212/213/214/215/216` | 投影能带数据 | **想要"按元素/轨道投影"的能带就选这几档** |
| `vaspkit → 11 → 111` | `TDOS.dat`（部分版本写作 `tdos.dat`） | 总 DOS |
| `vaspkit → 11 → 114 / 115` | `PDOS_SUM.dat` / `PDOS_USER.dat` | 分波 / 自定义轨道组合（见 §4.2） |

**`KPATH.in` 生成后可以（也应该）看一眼**——它的结构是：第一行注释里带**"高对称点之间的采点数量"**，
下面是 `Line-Mode`、`Reciprocal`，再逐行是高对称点坐标 + 符号（`GAMMA`/`M`/`K`…）。**采点数可以自己调大**
（教程示例用了 `60`），符号想显示成希腊字母要**全部**改成 `\Gamma`（见上一小节的坑）。

**几个容易忽略的细节**：

- **`scf` 步就把 `LVTOT = .TRUE.` 打开**（写出 `LOCPOT`）：后面做**功函数 / 真空能级对齐 / 形变势**
  （见 §十六）时要用它，**此时不写、以后就得重算**；顺手把 `LELF = .FALSE.`（不需要 ELF 文件）写上也省 IO。
- **DOS 步的 KPOINTS 密度**：教程给的另一种经验是**取 scf 的 2 倍、一般落在 20~40 之间**
  （与 §4.2 说的"格点翻倍"同义，只是给了具体数字区间）。
- ⚠️ **`LCHARG` 在非自洽步可以设 `.FALSE.`**——能带/DOS 步不需要再写一遍 `CHGCAR`
  （有的教程注释里写着"确保是 TRUE"，那是从 `scf` 段复制过来的残留，容易误导）。

**三条高频疑问（评论区反复出现，本库已有答案）**：

1. **"`scf` 明明没输出 `WAVECAR`，为什么能带步要写 `ISTART=1`？"**
   —— **那个 `ISTART=1` 是无用且误导的**：目录里没有 `WAVECAR`，VASP 只会忽略它。
   **最简洁、无歧义的写法是 `ISTART = 0` + `ICHARG = 11`**（只读 `CHGCAR`），见本节的 Origin 路线一节。
2. **"`vaspkit` 导出的能带/DOS 数据，费米能级自动归零了吗？"**
   —— **是，已经默认归到 0**，不需要再手动减费米能级（§4.2 也确认过）。
3. **"`LCHARG` 到底该 `T` 还是 `F`？"**
   —— **非自洽的能带/DOS 步用 `F` 即可**（不再需要电荷密度文件）；写 `T` 只是多出一个大文件。

## 四、态密度（workflow=`dos`）

- **步骤**：`opt` → `scf`（密 k 点）→ `dos`。
- **关键 INCAR**：`ICHARG=11`、`LORBIT=11`、`ISMEAR=-5`（或 `0`）；高 k 密度；`NBANDS` 够容纳导带。
- **验证**：总态密度/分波态密度（PDOS）峰值、带隙与能带一致。
- 生成命令：`python scripts/gen_inputs.py -s POSCAR -w dos`

---

### 4.2 另一条路线：VASPKIT 出数据 + Origin 画图（含 PDOS）

> 出自本人文章 `articles/20261001-VASP_vaspkit_Origin_画态密度_DOS_图.md`（材料：**Ru** 金属，`P6₃/mmc`，
> 12 配位十四面体，6 个短键 2.67 Å + 6 个长键 2.73 Å）。适合不想写代码、习惯用 Origin 出图的同学。

**DOS 步怎么做**（与 §4.1 的差别）：

1. 把 `POTCAR`、`KPOINTS`、`CHGCAR`、`CONTCAR` 与提交脚本拷进 DOS 目录，`cp CONTCAR POSCAR`；
2. ⭐ **把 `KPOINTS` 里的格点数「翻倍」**——DOS 需要比自洽更密的 k 网格；
3. INCAR 模板（本篇）：

```
ISTART = 0 ; ISPIN = 1 ; LREAL = .FALSE. ; ENCUT = 400 ; PREC = Accurate
LWAVE  = .FALSE. ; LCHARG = .TRUE. ; ADDGRID = .TRUE.
NSW    = 0 ; IBRION = -1 ; ISIF = 3
ISMEAR = -5 ; SIGMA = 0.05 ; EDIFF = 1.0E-5
#DOS control
EMIN   = -10 ; EMAX = 30 ; NEDOS = 1001 ; LORBIT = 11
```

- **`ISMEAR=-5` 适用于所有体系的 DOS 计算**（而**金属的结构弛豫不能用 `-5`**，见 `errors.md` §2.1）；
- **`EMIN`/`EMAX` 只划定大致范围**——输出不会正好是 `-10 ~ 30`；
- **`NEDOS` 默认 `301`**，决定 DOS 横轴取多少个点（点少就加大，见 §4.1 的 CeMnNi₄ 用了 `1001`）；
- `ISIF=3` 在 `NSW=0` 时不会产生弛豫，只是顺带算应力张量——非必需，但无害。

**VASPKIT 取数据的三个命令**：

| 命令 | 产物 | 说明 |
| --- | --- | --- |
| `vaspkit → 11 → 111` | **`tdos.dat`** | 总 DOS |
| `vaspkit → 11 → 114 → <元素>` | **`PDOS_SUM.dat`** | 按元素/轨道的分波 DOS + 总 DOS；**`SELECTED_ATOMS_LIST`** 会列出实际选中的原子（也可直接输原子序号） |
| `vaspkit → 11 → 115 → <元素> → <轨道列表> → …` | **`PDOS_USER.dat`** | **自定义轨道组合**：例把全部 d 轨道加起来——`11 115 → Ru → dxy dyz dz2 dxz dx2 → Ru → dxy → …` |

**Origin 出图**：把 `PDOS_SUM.dat` 拖进 Origin → 选 x/y 数据作图 → 再调整四件事：
**① 改 x/y 轴标题；② 改 x 轴取值范围；③ 加上边框（含上边框）；④ 加粗线条**。

- 💡 **费米能级不用手动移**：`vaspkit` 生成的 `.dat` 放进 Origin，**费米能级默认已在 0 处**。

### 4.1 完整算例：CeMnNi₄（mp-5951）的三步与 pymatgen 出图

> 一篇完整实操（`articles/20261001-VASP_vaspkit_Python_画态密度_DOS_图.md`）：
> 材料取自 Materials Project（**mp-5951 = CeMnNi₄**，六角 Laves 衍生结构、立方 `F̄43m` 空间群），
> 目录按 **`opt/` → `scf/` → `scf/nonscf/`** 组织，最后用 **pymatgen 的 `DosPlotter`** 出图。
> **三步的 KPOINTS 用同一密度**：KPT-resolved `0.030` → Monkhorst-Pack **`5 5 5`**。

**三步 INCAR 的差异（最值得复用的一张表）**——其余参数三步完全相同：
`ENCUT=400`、`PREC=Normal`、`ADDGRID=.TRUE.`、`LREAL=.FALSE.`、`NPAR=4`、`ISPIN=2`、
`MAGMOM = 4*0.5 4*6 16*0.5`、`LORBIT=11`、`NELM=90`、`NELMIN=6`、`EDIFF=1E-06`。

| 参数 | `opt`（结构优化） | `scf`（静态自洽） | `nonscf`（DOS 非自洽） |
| --- | --- | --- | --- |
| `ISTART` | `0` | `0` | **`1`**（读入上一步的 `WAVECAR`） |
| `LWAVE` / `LCHARG` | `.FALSE.` / `.FALSE.` | **`.TRUE.` / `.TRUE.`**（要把两个文件留下来） | `.FALSE.` / `.FALSE.` |
| `ISMEAR` | `0` | **`-5`** | **`-5`** |
| `NSW` | `100` | **`0`** | **`0`** |
| `ICHARG` | — | —（注释掉留作备选） | **`11`**（固定电荷密度） |
| 额外 | `ISIF=2`、`IBRION=2`、`EDIFFG=-2E-02` | 同左 | **`EMIN=-10`、`EMAX=30`、`NEDOS=1001`** |

- **非自洽步要从自洽目录拷来两个文件：`WAVECAR` 和 `CHGCAR`**
  （⚠️ 原文两处都写成「把自洽计算目录下的 `WAVECAR` 复制到本目录下」，**第二处应为 `CHGCAR`**——本库已订正）。
- **DOS 曲线的点数由 `NEDOS` 决定**（觉得点太少就加大它）；`EMIN`/`EMAX` 控制能量窗口。
- ⭐ **强烈建议养成的习惯：把自己的 DOS 与文献对照**。该文就是拿 CeMnNi₄ 的结果与
  **Mazin, *Phys. Rev. B* **73**, 012415 (2006)（"CeMnNi₄: Impostor half metal"）** 的图比对后才下结论——
  「算完不知道对不对」正是新手最常见的问题（对照数据源见 `onboarding.md` §六）。

**pymatgen 出图配方（两段，可直接用）**：

```python
# ① 总 DOS + 按元素投影
from pymatgen.io.vasp import Vasprun
from pymatgen.electronic_structure.plotter import DosPlotter
import matplotlib.pyplot as plt

v = Vasprun('./scf/nonscf/vasprun.xml')
plotter = DosPlotter()
plotter.add_dos('Total DOS', v.tdos)
plotter.add_dos_dict(v.complete_dos.get_element_dos())
plotter.get_plot(xlim=[-4, 4], ylim=[-150, 350])
plt.savefig('dos_element.png')
```

```python
# ② 按「元素 + 轨道」投影（Ce-f、Ni-d、Mn-d）
from pymatgen.electronic_structure.core import OrbitalType
from pymatgen.electronic_structure.plotter import DosPlotter
from pymatgen.io.vasp.outputs import Vasprun
import matplotlib.pyplot as plt

r = Vasprun('./scf/nonscf/vasprun.xml', parse_potcar_file=False)  # 不去找 POTCAR
cdos = r.complete_dos
plotter = DosPlotter()
plotter.add_dos('Total DOS', r.tdos)
for el, orb, name in (('Ce', OrbitalType.f, 'Ce(f)'),
                      ('Ni', OrbitalType.d, 'Ni(d)'),
                      ('Mn', OrbitalType.d, 'Mn(d)')):
    plotter.add_dos(name, cdos.get_element_spd_dos(el)[orb])
plotter.get_plot(xlim=(-5, 2), ylim=(-150, 350))
plt.savefig('dos_spd.png')
```

- `Vasprun(...).complete_dos` 自带 `get_element_dos()` 与 `get_element_spd_dos('Ce')`
  ——**不需要自己解析 `DOSCAR` 的数字列**。
- 💡 只要「总 DOS + 投影」的图，上面两段就够；要更多样式再看 `scripts/README.md` 的 `scripts/plot/`。

**两个磁性相关提示**（原文注释里给的）：

- **`NUPDOWN`**：磁性材料若算出来「没有磁性」，可以设 `NUPDOWN = <体系总磁矩>`（原文注释里是 `19.6936`）；
  ⚠️ **算磁性材料基态时一般不用这个参数**——它只是把总磁矩强行固定住。
- **`LORBIT=11`** 打开后，**算完可在 `OUTCAR` 的 `magnetization (x)` 处查看每个原子的磁矩**
  （与 `references/onboarding.md` §9.2 的磁矩提示一致）。

## 五、磁性计算（workflow=`mag`）

- **目的**：自旋极化、磁矩、自旋轨道耦合（SOC）/非共线磁结构。
- **关键 INCAR**：
  - `ISPIN=2`、`MAGMOM=...`（按元素给出初猜，如 Fe 高自旋 `5`，Cu `1`）
  - 非共线：`LNONCOLLINEAR=.TRUE.` + `MAGMOM`（三维方向）；SOC 再加 `LSORBIT=.TRUE.` + `SAXIS`
  - `ISMEAR` 按金属/绝缘体；`NELM` 调大
  - 收敛难时调混合：`AMIX_MAG`/`BMIX_MAG` 减小、`IMIX=4`
- **注意事项**：磁构型初猜很关键，先做低精度粗收敛再提精度；`symmetry equivalent atoms` 报错时检查对称与磁矩设置。
- 生成命令：`python scripts/gen_inputs.py -s POSCAR -w mag --magmom "Fe:5"`

---

## 六、声子计算（有限位移法，phonopy / ALAMODE）

- **目的**：声子谱、声子态密度、晶格动力学。
- **步骤**：
  1. 高精度几何优化：`EDIFFG=-1E-3`（或更严 `-5E-4`），`EDIFF=1E-6`~`1E-7`，`PREC=Accurate`。力噪声直接决定声子质量。
  2. 建超胞并生成有限位移构型（phonopy：`phonopy --dim ...`；ALAMODE：`create_phonon_config`）。
  3. 对每个位移构型跑 VASP `scf`（`IBRION=-1`，可 `NSW=0`），只取力。
  4. 收集力/能量，拟合力常数，计算声子谱/态密度（phonopy 的 `band.conf` / ALAMODE `harmonic`）。
- **关键 INCAR**：`PREC=Accurate`、`EDIFF` 严格、`IBRION=-1`、`ISMEAR` 合适、位移体系关闭对称破坏项（`ISYM=0` 常配合 ALAMODE）。
- 📌 **phonopy 的完整实操、`phonopy -d` 产物如何区分、以及 VASP 自己算 Hessian 的 `IBRION=8` 路线**，见 **§三十八**（含 `band.conf` 写法、`PBAND.dat` 导出与**虚频判读经验**）。
- **验证**：声子谱无显著虚频（有则回优化）；力常数拟合残差小。
- 生成命令（位移构型的 VASP 输入）：`python scripts/gen_inputs.py -s <displaced_POSCAR> -w scf`

## 七、晶格热导率 / 三声子·四声子散射（ALAMODE）

- **目的**：`κ_lattice`，需要二/三/四阶力常数与散射速率。
- **步骤**：
  1. 高精度优化（同上，力判据严）。
  2. ALAMODE 生成二阶（harmonic）与三阶/四阶（anharmonic）位移构型。
  3. VASP 逐构型 `scf` 取力/能量。
  4. `fit_phonon`/`fit_alm`（或 `harmonic`/`anharmonic`）拟合力常数，注意正则化参数（`lreg_scale`）稳定拟合。
  5. 三声子散射（`ph_conductivity` 等）算各温度 `κ_lattice`；四声子（如含低频光学模/强非谐）需四阶项。
- **关键 INCAR**：同声子，`EDIFF` 更严（能量噪声直接影响三阶力常数）；`ISYM=0`；位移幅度与超胞尺寸合理。
- **验证**：不同 k 网格/位移幅度下 `κ_lattice` 收敛；对比实验/文献数量级。
- 生成命令（位移构型 VASP 输入）：`python scripts/gen_inputs.py -s <displaced_POSCAR> -w scf`

## 八、热电性质（Seebeck / 电导 / ZT）

- **目的**：电子输运系数，常与声子 `κ_lattice` 结合得 `ZT = S²σT/(κ_e + κ_lattice)`。
- **步骤**：
  1. `opt` → `scf`（固定结构）。
  2. 用 `BoltzTraP2`（或类似输运工具）读取 `vasprun.xml`/`PROCAR`，在若干掺杂浓度/温度下算 `S`、`σ`、`κ_e`。
  3. 电子热导率 `κ_e`（Wiedemann–Franz）与 `κ_lattice`（见第七节）合并得 `ZT`。
- **关键 INCAR**：`scf` 的 k 点要足够密且对称完整（输运系数对 k 网格/带结构敏感）；`LORBIT=11`；能带结构与实验一致是前提。
- **注意事项**：`ZT` 优化的核心是 `κ_lattice`（声子）与电学性能的解耦——先确认各自收敛再合成结论。
- 生成命令：`python scripts/gen_inputs.py -s POSCAR -w scf`

---

## 九、高通量筛选（可选，与 pymatgen 结合）

- **思路**：用 pymatgen `Structure`/`MPRelaxSet` 批量生成 `opt→scf→属性` 输入，逐结构跑、汇总能量/带隙/磁矩等。
- **脚本复用**：`scripts/gen_inputs.py` 支持单结构生成；批量场景可在外层循环调用，或按 `--workflow` 一次性产出。
- **注意事项**：统一 `PREC`/`ENCUT`/k 密度等口径，保证可比性；记录每结构的收敛状态。

---

## 十、成键强度分析：COHP / COOP / ICOHP（VASP + LOBSTER）

- **目的**：定量衡量成键强度，辅助判断结构稳定性与相变（如费米能级是否落在反键区）。详见 `articles/20260930-vasp-lobster-cohp-bonding.md`。
- **原理速记**：COOP 成键为正、反键为负；COHP **成键为负、反键为正**，故常画 `-COHP`（成键朝右）。COOP 与 -COHP 无直接等价关系。
- **步骤**：
  1. `opt` 结构优化。
  2. `scf` 单点（为 LOBSTER 写波函数）：`ISYM=-1 或 0`、`LORBIT=12`（别用 11）、`LWAVE=.TRUE.`、`NBANDS` 尽量大、`LREAL=.FALSE.`、`EDIFF=1e-8`、`ISMEAR=-5`（若用 0/1 则 lobsterin 加 `gaussianSmearingWidth`）。
  3. 生成 `lobsterin`：**按元素+键长**（`cohpGenerator from dmin to dmax type A type B`）而非逐原子对（LOBSTER 把显式原子对当非周期，会认错周期性距离）；`usebasisset pbeVaspFit2015`；`basisfunctions` 按 POTCAR 价电子轨道写（对结果影响大）。
  4. 运行 `lobster`（目录含 WAVECAR/CONTCAR/KPOINTS/OUTCAR/POTCAR/vasprun.xml + lobsterin）。
  5. 分析 `COHPCAR.lobster`：第 1 列能量（费米=0）、第 2/3 列平均 COHP/ICOHP，之后每两列一原子对；**特定原子对的 ICOHP 越负成键越强**（整体平均意义不大）。
- **脚本**：`python scripts/gen_lobsterin.py` 可 `--list-bonds` 统计键长、或按 `-e/-s/-z/-d/-m` 生成 lobsterin 并软链 VASP 文件。
- **易错**：lobster 无 COHP/ICOHP 输出多半是 `NBANDS` 太少；COHPCAR 只有正值或元素名报错 → 检查元素/键长/轨道设置；COHP 毛刺多 → k 点不够密。

---

## 十一、AIMD 轨迹后处理：借 GROMACS 分析动力学结果

- **目的**：AIMD 跑完后做动力学分析（RDF、RMSD、速度自相关函数 VACF 等）。VASP 自带的 AIMD 后处理较弱：`XDATCAR` 只有位置没有速度，而 `OUTCAR` 也只输出**最后一帧**的原子速度，因此速度相关性质必须额外处理。
- **思路**：把 VASP 轨迹转成 GROMACS 的 `.gro`（同时记录位置与速度），再借用 GROMACS 成熟的分析功能。转换工具用 `VASP2GRO`（源码 <https://github.com/tamaswells/VASP_script/tree/master/VASP2GRO>，提供 Linux / Windows 可执行文件）：自动读同目录 `OUTCAR`，输出含位置与速度的 gro 轨迹，并生成伪 `XDATCAR.top` 与 `XDATCAR.mdp`。
  - 速度用**向后差分**近似得到，因此**第 1 帧没有速度**；更精确的做法是由 `OUTCAR` 里的受力按牛顿定律积分求速度，`VASP2GRO` 未采用。
  - 已做周期性处理，避免跨边界的假速度。
  - ⚠️ 伪 `top`/`mdp` **不能真的用来跑 MD**，只服务于 GROMACS 的分析功能。
- **步骤**：
  1. 运行 `VASP2GRO`：`chmod u+x VASP2GRO.exe && ./VASP2GRO.exe`（自动读 `OUTCAR`）。
  2. 安装 GROMACS：Ubuntu `apt-get install gromacs`、CentOS `yum install gromacs`，或参考 Sob 的并行安装方法；用 `gmx`（并行版 `gmx_mpi`）验证。**并行安装时后续所有命令都要把 `gmx` 换成 `gmx_mpi`**。
  3. 转成二进制轨迹：`gmx trjconv -f XDATCAR.gro -o XDATCAR.trr`
  4. 打包输入：`gmx grompp -f XDATCAR.mdp -c XDATCAR.gro -p XDATCAR.top -o em.tpr`
  5. 建原子组：`gmx make_ndx -f XDATCAR.gro` → `a H` / `a O` 添加组，`3 | 4` 合并两组，`q` 保存 → `index.ndx`
  6. 速度自相关：`gmx velacc -f XDATCAR.trr -o vacf.xvg -n index.ndx`（按提示选组，例如 4 = O 原子组）
  7. 出图：`vacf.xvg` 可用 `xmgrace` / Origin，也可用 matplotlib 解析（xvg 由 `@ title/xaxis/yaxis` 注释行加数据行组成；该文章附带 `xvg.py` 示例）。
- **其它常见分析**（GROMACS 常规命令，供参考）：`gmx rdf` 径向分布函数、`gmx rms` 均方根偏差、`gmx msd` 均方位移。
- **易错与边界**：
  - 首帧无速度：算 VACF 时从第 2 帧起算，别把首帧的零速度当物理结果。
  - 轨迹长度与采样间隔决定可信度：扩散、RDF、VACF 对轨迹长度敏感，轨迹太短时结论不可靠。
  - 跨周期边界成键会让 RDF 峰位异常，建议先核对第一配位峰位置是否合理。
  - 记得 `gmx_mpi` 与 `gmx` 不要混用同一条流程里的命令。
- **来源文章**：`articles/20260930-用强大的GROMACS分析工具分析VASP的动力学结果.md`
- **脚本 / 工具**：`VASP2GRO`（`OUTCAR` → 带速度的 `.gro`）、`XDATCAR_toolkit.py`（轨迹转 PDB，无速度）、`xvg.py`（画 `.xvg`）的功能与用法见 `references/tools.md` 二.3–2.5、四.3。

---

## 十二、二维势能面（PES）与最小能量路径：string 法

- **目的**：扫完二维势能面（例如 γ-TiAl {111} 面的广义层错能 GSFE、催化吸附能面）后，**自动**找出最小能量路径（MEP），而不是像不少文献那样直接在图上手工描一条。
- **数据从哪来（VASP 侧）**：PES 由一系列**固定形变 / 位移的静态计算**给出——对每个 (x, y) 组合生成结构做单点能（`scf`），汇总成三列 `PES.data`（第 1 列 x、第 2 列 y、第 3 列势能）。这一步与体系强相关（层错能常用面内位移约束，吸附常用吸附位/高度），关键是**所有点用同一套 `ENCUT`/k 网格/赝势口径**，否则面形会被数值噪声污染。
- **工具**：`MEPSearcher`（Xin Chen，<https://github.com/chenxin199261/MEPSearcher>）——string 法的 Python3 实现，含 CG 算法（测试中略优于 SD）与 `draw.py` 快速查看收敛结果。
- **算法一句话**：string 法属 chain-of-states，与 NEB 同类——把一串很密的珠子放在 PES 上让它们自由向能谷跑，稳定后即为 MEP。演化时扣除**平行于串珠的切向力**，再用拉格朗日乘子施加约束（该实现用最简单的**珠子均匀化**）。原始文献：E, Ren, Vanden-Eijnden, *Phys. Rev. B* **66**, 052301 (2002)。
- **步骤**：
  1. 安装 ALGlib 库。
  2. 准备 `PES.data`（三列：x、y、势能）。
  3. 准备 `guess.data`：第 1 行是珠子个数（**30–40 为宜**），第 2 行起点 x y，第 3 行终点 x y。端点**不必精确**，只要不落到别的能谷即可——程序会按线性插值建一条初始路径。
  4. 在 `MEPSearcher.py` 里调参数：`h`（每步位移步长，默认可用）、`o`（`sd` 或 `cg`，默认 `sd`；收敛不理想就试 `cg`）。
  5. 把两个输入文件放到主目录后运行；程序**每 30 步**报一次消息，成功时给出收敛总步数（`diff` 是当前收敛差值）。
  6. 结果写入 `out.data`（格式与 `PES.data` 相同），用 `draw.py` 看图：**红线 = 初始路径，黑线 = MEP**。
- **优势与边界**：
  - string 法的初态/末态**不固定**，搭初猜比 NEB 省事——但这个优势**只在二维情形**成立；高维过渡态搜索仍用 NEB / dimer 等。
  - 该实现用三次样条插值，实测够用（未提供 B 样条）。
  - pymatgen 也集成了画 MEP 的功能（三维、带动画），需要三维展示时可考虑；精度上 string 法更严谨。
- **来源文章**：`articles/20260930-string法自动寻找二维势能面上的MEP.md`
- **脚本 / 工具**：`MEPSearcher`（string 法，`PES.data` + `guess.data` → `out.data`）、`draw.py`、ALGlib 依赖与参数（`h`/`o` 选 sd 或 cg）见 `references/tools.md` 三.4。

---

## 十三、理想拉伸 / 剪切：应力应变曲线（idealdeform.sh）

- **目的**：用 DFT 算理想拉伸 / 剪切曲线，取弹性模量、理想强度等。⚠️ **不要把 DFT 的理想应力应变曲线和宏观应力应变曲线混为一谈**——宏观曲线来自位错运动与塑性变形，与第一性原理结果不是同一个概念，写作与解释时必须说清楚用的是哪一种。
- **原理**：假设加载足够慢（准静态），按固定应变间隔施加**应变矩阵**，每一步只做晶胞 + 原子优化（`ISIF=4`），记录该步的应力。
- **两类应力应变**（换算只在颈缩初期之前成立）：
  - 工程：`ε_eng = (l - l₀)/l₀`、`σ_eng = F/A₀`；
  - 真实：由塑性变形不可压缩假设 `A₀l₀ = A·l` 得 `σ_true = σ_eng(1 + ε_eng)`、`ε_true = ln(1 + ε_eng)`。
  - 对**有表面**的体系一般不需要真实曲线，看工程曲线即可。
- **输入准备**：
  - 备好 VASP 四个输入文件；**`POSCAR` 必须用分数坐标**；
  - `INCAR` 用 `ISIF=4`，**不要用 3**（体积变化会让曲线失真）；
  - 用 `OPTCELL` **关闭变形方向的弛豫**；
  - `idealdeform.sh` 与输入文件放在同一目录。
- **脚本参数**（改脚本头部）：
  - `orientation`：`XX`/`YY`/`ZZ`（拉伸）或 `XY`/`XZ`/`YZ`（剪切）；
  - `initial`：初始应变；`step`：每步应变间隔；`num`：施加次数——示例 `initial=0, step=0.01, num=100` 表示从 0 开始每 0.01 拉一次、共 100 次、最终应变 1.000（100%）；
  - `mpiexec`：运行命令，按本机 MPI 环境填写。
- **运行与输出**：
  - 运行时打印进度；完成后默认用 gnuplot 画**工程**应力应变曲线（单位 GPa，**正号 = 拉应力**）；想换画法可把 `plot.sh` 复制到当前目录运行；
  - 数据文件：`engineeringstressstrain.all`（工程）、`truestressstrain.all`（真实）。
- **某一步不收敛**：脚本会停下——先在 `OUTCAR` 里查原因，修好后**从当前阶段继续**运算，不要从头重跑。
- **工具来源**：ponychen 的 Vasptools <https://github.com/ponychen123/Vasptools>。
- **来源文章**：`articles/20260930-计算应力应变曲线脚本idealdeform_sh使用指南.md`
- **脚本 / 工具**：`idealdeform.sh` 的头部参数（`orientation`/`initial`/`step`/`num`/`mpiexec`）、产物与坑见 `references/tools.md` 三.1。

---

## 十四、施加任意外压（非静水压）：vaspeqstress.sh

- **为什么需要**：VASP 自身只能施加**静水压**（`PSTRESS`），不能直接加任意外压张量。该脚本通过**迭代调整晶格**把体系逼到目标外压，适合研究单轴/剪切加载下的晶胞响应。
- **原理**（广义胡克定律迭代）：
  1. 从 `OUTCAR` 读当前外压矩阵；
  2. 与目标外压相减，得到下一步需施加的应力矩阵 `Mad`；
  3. 用广义胡克定律（杨氏模量 `E`、泊松比 `v`）把每个应力组元换成应变组元；
  4. 更新应变矩阵：`Mnew = (I + Mad * P) * Mold`（`I` 为单位矩阵，`P` 为阻尼系数，`Mold` 是当前 POSCAR 的应变矩阵）；
  5. 重复以上步骤，直到「当前外压 − 目标外压」小于收敛标准。
- **参数**（改脚本头部）：
  - `Setpress`：目标外压，六个分量依次为 `XX, YY, ZZ, XY, YZ, ZX`；**VASP 的外压正号 = 压应力，负号 = 拉应力**；
  - `presscirt`：应力差的收敛标准（`0.1` 够用，不要乱改）；
  - `E` / `v`：杨氏模量与泊松比（查文献/手册即可，**不必太精确**）；
  - `imax`：最大迭代步数（`100` 够；到 100 还没收敛就加大后再接着跑）；
  - `P`：阻尼系数，作用是防止外加应变加过头；
  - `mpiexe`：执行 VASP 的命令，按你的作业系统填写。
- **运行**：
  - `INCAR` 与普通优化相同，但**必须 `ISIF=2`**；
  - 每一步的 POSCAR 会另存为 `poscar.*`；`pressure.all` 里可以看每一步的外压与收敛情况；
  - 实测例子（bcc Ni）：施加静水压 34 次迭代收敛；改成目标外压 `(0.0 100 0.0 0.0 0.0 0.0)` 并放开原子弛豫、从上一状态继续，46 次迭代收敛。
- **Tips（都是踩过的坑）**：
  - **建议分两次做**：第一次固定原子只弛豫晶胞，收敛后再放开原子弛豫；
  - `E`、`v` 只是初值：实际材料是多晶，与 DFT 结果不严格对应，意思到位即可；
  - **VASP 对应力/压应力的计算是出了名的差**，解读这类结果要保守；
  - 脚本里已经带了 PBS 参数，需要就把行首的 `#` 去掉；
  - **尽量用正交胞**：VASP 的应力/压力基于笛卡尔坐标系，最好让三个基矢沿 `X/Y/Z`。
- **工具来源**：ponychen 的 `vaspeqstress.sh` / `vaspeqstress.py`（在他人 python2 版本基础上用 python3/bash 重写）。
- **来源文章**：`articles/20260930-vasp定压计算脚本vaspeqstress_sh使用教程.md`
- **脚本 / 工具**：`vaspeqstress.sh` / `.py` 的头部参数（`Setpress`/`presscirt`/`E`/`v`/`imax`/`P`/`mpiexe`）、版本关系与坑见 `references/tools.md` 三.2。

---

## 十五、电荷密度可视化：总电荷密度 / 差分电荷 / 平面平均

### 先分清要算的是哪一种「差分」

文献里的 *charge density difference* 至少指**三种不同的量**，图长得不一样是正常的：

1. **体系 − 各片段**（`AB − A − B`）：最常用，回答"相互作用后电子往哪儿流"。本节的路线 A / B 算的就是它。
2. **变形电荷密度（deformation charge density）**：体系的自洽密度 − **各原子自由状态的球对称密度**
   （`AB − 孤立原子`，注意不是各自弛豫后的片段）。
   - VASP 侧做法：用**同一个 `POSCAR`** 跑一次 **`ICHARG=12`**（非自洽、取原子密度叠加，
     密度在整轮电子迭代中保持不变）+ `LCHARG=.TRUE.` → 得到"球形原子叠加"的 `CHGCAR`，再与 AB 的自洽
     `CHGCAR` 相减。
   - ⚠️ `ICHARG=11/12` 时按元素设 `LMAXMIX`：s/p → `2`，d → `4`，f → `6`
     （VASP Wiki `ICHARG` 条目）。
3. **同一体系两个状态之差**：如"有外场/无外场"、"激发态/基态"的密度差。

⚠️ **片段必须与体系同几何**：A、B 的 `POSCAR` **直接从 AB 的结构里截取**，坐标一字不改，
**不要再单独做结构优化**——片段各自弛豫后坐标对不上，差分结果就没有意义了。

⚠️ **加了 U 或带磁性时，片段的 INCAR 不能"照抄 AB"**：`LDAU` 的 U 值与**元素种类及其出现顺序**一一对应，
片段里元素变了就必须同步改（否则 U 会加到错的元素上）；`ISPIN`/`MAGMOM` 同样要按片段重新设定。

⚠️ 用 VASPKIT 做差分（`31 314`）时，若三份 `CHGCAR` 的 **FFT 网格不一致**会直接报
`Different NGX, NGY and NGZ are adopted...`——把 `NGX/NGY/NGZ` 显式写进每个体系再重算，
见 `errors.md` §8.14。



- **两种「差分」不要混**：
  - **差分（形变）电荷密度**（deformation charge density）：成键后的电荷密度 − 各原子在**同位置**的孤立原子电荷密度之和，用来看成键过程中的电荷转移与极化方向；
  - **二次差分电荷密度**（difference charge density）：体系成分或几何构型改变后的电荷重新分布。
- **计算式**：`Δρ = ρ(AB) − ρ(A) − ρ(B)`。
- **三个硬性前提**（任一条不满足，图一定是错的）：
  1. AB、A、B 必须放在**相同大小的空间格子**里——同一 cell，并**显式统一 `NGX/NGY/NGZ`**（FFT 网格不同会让相减结果出现假条纹）；
  2. A、B 计算时原子位置**固定为它们在 AB 中的位置**，不要各自重新优化；
  3. `KPOINTS`、`ENCUT`、`PREC` 等口径与自洽计算一致。
- **INCAR 要点**（只做电子自洽）：`IBRION=-1`、`NSW=0`、`ISIF=2`、`ISMEAR=0 SIGMA=0.05`、`PREC=ACCURATE`、`LREAL=Auto`、`ISYM=0`，并**显式写出 `NGX/NGY/NGZ`**。
  - NGX/NGY/NGZ 从（优化或自洽的）`OUTCAR` 里取：`grep -A3 'NGX' OUTCAR`，可加一个 alias 方便反复查。
- **目录与文件组织**：`mkdir AB A B`；先在 AB 里做结构优化，`cp opt/CONTCAR POSCAR`；A、B 的 `POSCAR` 由 AB 的 POSCAR **删掉不属于自己的原子行**得到（**保持 cell 不变**）；各自 `POTCAR` 与自己的 POSCAR 相符；跑完得到三个 `CHGCAR`。
- **三维图（VESTA）**：打开 AB 的 `CHGCAR` → `Edit → Edit Data → Volumetric Data → Import` 选 A 的 CHGCAR → 勾选 `Subtract from current data` → OK；再对 B 重复一次；`Properties…` 调等值面。二维切面用 `Utilities → 2D Data Display`。
- **平面平均差分（沿某方向平均的曲线）**：
  - 先用 `chgdiff.pl` 做差：`chgdiff.pl <要减去的> <总电荷>`——即 **file2 = AB，file1 = A/B**；一次只减一个，所以 `chgdiff.pl A AB` 得 `ρAB−ρA`，再 `chgdiff.pl B <上一步结果>` 才得到 `Δρ`；
  - 再用改过的 `vtotav.f` 做平面平均：它原本处理 `LOCPOT`（算功函数），**必须改源码才能读 `CHGCAR`**；编译 `ifort -o vtotav.x vtotav.f`，运行时选方向（1=X、2=Y、3=Z）；
  - **画图注意**：横坐标是**所选方向的格点数**（不是 Å，需自己换算），纵坐标是**电荷密度 × cell 体积**，单位需自行转换；
  - 替代路线：用 `vtotav.x` 分别处理 AB/A/B 的 CHGCAR，再在 Origin/Excel 里做列相减，结果一致；或用 **vaspkit 的 Planar-Average CHG** 处理后手动相减。
- **方法论提醒**（原文引用朱全喜老师）：后处理不要张口就要现成脚本，先读懂它到底做了什么再动手，尤其这种「改别人脚本去读另一种文件」的做法，切忌刻舟求剑。
### 路线 B（推荐）：VASPKIT + VESTA + 建模软件，一条龙（免 Perl/Fortran）

- **适用**：不想碰路线 A 的 `chgdiff.pl` + 改版 `vtotav.f`（要装 Perl、改 Fortran、`ifort` 编译），
  改用 VASPKIT 与图形界面完成同样的**差分电荷 + 平面平均**。
- **建模（Materials Studio + VESTA）**：从 Materials Project 下 cif → MS 里
  `Build → Surfaces → Cleave Surface`（选 hkl 与层数）、`Build → Crystals → Build Vacuum Slab`（加真空层）、
  按需加吸附物 → `File → Export` 存 cif（**这几步必须按顺序**）→ VESTA `File → Export Data → VASP`
  转成 POSCAR。
  - ⚠️ **VESTA 里删原子不会写回文件**（视图里删掉了，保存出来还是原样）——要删原子请回建模软件里做完再导出。
- **固定底层原子**：`vaspkit 4 402` 生成 `POSCAR_FIX`，改名 `POSCAR`。老版只能按"从下往上第几层"选；
  **新版可以逐层或连续选任意层，并能指定方向**（如 `all`）。
- **其它输入文件也能交给 vaspkit**：`1 101`（INCAR，`LR` 系列）、`1 102`（KPOINTS，**会顺带生成 POTCAR**）、
  `1 103`（POTCAR）。
  - **K 点撒点方式**：`Monkhorst-Pack` 与 `Gamma` 两种；**各维取奇数时两者等价且都含 Γ；取偶数时 MP 不含 Γ，
    Gamma 会平移以采到 Γ**——一般选 Gamma 更稳妥。
    ⚠️ 不过「该不该含 Γ」在社区里有**相反经验**：立方/正交有主张用 **MP 偶数**（理由是 Γ 点对称性高、
    能带在此常取极值，代表性差），而**六方**用 MP 偶数会让不可约 k 点变成约 **3 倍**、故应选 Gamma——
    两派经验详见 `errors.md` §8.20。本行的「选 Gamma 稳妥」是**保守做法**，最终以**不可约 k 点数 + 收敛测试**为准。
  - **ENCUT 与 ENMAX**：先 `grep ENMAX POTCAR` 看各元素最大 `ENMAX`；不设 `ENCUT` 时 VASP 自动取 max(ENMAX)，
    但常规做法是取 **max(ENMAX) 的 1.2–1.3 倍**。
- **三次自洽**：AB 直接用弛豫后的 `CHGCAR`（结构弛豫时 `LCHARG=.TRUE.` 就会留下）；A、B 的 `POSCAR` 由 AB 的
  `CONTCAR` 经「VESTA → cif → 建模软件删原子 → cif → VESTA → POSCAR」得到。
  - **必须统一 `NGX/NGY/NGZ`**：在 AB 目录 `grep NGX OUTCAR` 查到网格（本例 `NGX=16, NGY=32, NGZ=90`），
    把同样的数值**显式写进 A、B 的 INCAR**；三次计算都要 `LCHARG=.TRUE.`。
- **差分与出图（vaspkit）**：
  1. `vaspkit 31 314`，按提示依次给出 **AB、A、B** 的 `CHGCAR` 路径（空格分隔）→ 生成 **`CHGDIFF.vasp`**；
  2. 拖进 VESTA 看三维等值面：**默认青色 = 电荷减小，黄色 = 电荷增加**；
  3. **二维切片**：先选中三个原子（例如吸附的 CO 加一个邻近原子）→
     `Utilities → 2D Data Display... → Slice... → Calculate the best plane for the selected atoms → OK`；
  4. **平面平均（沿某方向）**：把 `CHGDIFF.vasp` **改名为 `CHGCAR`**，再 `vaspkit 31 316` → 选读取形式 →
     选方向（`3` = z）→ 生成 **`PLANAR_AVERAGE.dat`** → 拖进 Origin 作图。
- **两条路线的关系**：路线 B 的 `31 314`/`31 316` 与路线 A 的 `chgdiff.pl`/`vtotav.f` **做的是同一件事**
  （差分 + 平面平均），B 免编译、更省事；A 的好处是逻辑透明、可自己改。

### 总电荷密度（`CHGCAR`）的查看与切片

- **数据从哪来**：结构弛豫时设 `LCHARG=.TRUE.`，算完直接得到 `CHGCAR`（**不需要**再做一次专门的自洽）。
- **三维等值面**：把 `CHGCAR` 拖进 VESTA 即可。
  - **原子球太大挡住电子云**时：`Objects → Properties → Atoms... → Radius and color`（或界面左下角的
    `Properties` 按钮）——左侧选元素、右侧改半径、下方选颜色，改小后 OK。离子晶体（如 NaCl）要把球缩小
    才看得清电荷往哪一侧转移。
- **二维电荷密度图（VESTA 有两条路径）**：
  1. `Edit → Lattice Planes... → Add lattice planes`，直接改 Miller 指数 `(hkl)`；或选中三个原子后点
     `Calculate the best plane for the selected atoms`；
  2. `Utilities → 2D Data Display... → Slice` → 手动选三个原子 → `Calculate the best plane for the selected atoms`
     → OK。
  - **画等高线**：`2D Data Display` 页面 `Contours` 栏勾 `Draw contour lines` 与 `Logarithmic`；
  - **转成「三维鸟瞰图」**：同页面 `General` 栏勾 `Bird's-eye view`。
- **两个常见疑问**：
  - **「我画出来的电荷密度和别人不一样」**：**先怀疑 POTCAR**——不同赝势的价电子数不同（例如同一元素
    7 个电子 vs 1 个电子的版本），电荷密度分布自然不同；这通常**不是 INCAR 参数的问题**。
  - **「图上最蓝的部分是负值？」**：原文观察到负值区域集中在**原子核位置**，据此**猜想**负值对应「正电荷（核）
    所在处」。⚠️ 但要注意：**总电荷密度 `CHGCAR` 本身应为非负**——若你确实看到负值，先确认自己画的是
    **差分**密度（`CHGDIFF.vasp`，差分为负很正常）还是总密度，再看 VESTA 的色标范围，别把色标读数当成物理值。
- **`CHGCAR` 文件长什么样**（自己写解析/后处理脚本时必备）：
  - 开头就是**该体系的 POSCAR 内容**（注释行 + 缩放系数 + 3 行晶格 + 元素行 + 原子数行 + `Direct` + 各原子坐标），共 **`8 + 原子数`** 行（原文的例子 NaCl 有 8 个原子 → 前 16 行；另一篇讲单个 O 原子的教程说「前九行 + 第 11 行是 `NGX/NGY/NGZ`」，`8 + 1 = 9` ✓ **两个独立来源一致**）；
  - 紧跟**一个空行**；
  - 再一行是三个方向的**格点密度 `NGXF NGYF NGZF`**；
  - 之后是 `NGXF × NGYF × NGZF` 个电荷密度数值（沿文件往下还会重复出现“坐标块 + 格点行”，这是 VASP 的书写习惯）；
  - ⚠️ `CHGCAR` 是**基于赝势的价电子**电荷密度（**不是全电子**），所以紧贴原子核处的数值没有物理意义；
  - **自旋极化体系**（`ISPIN=2`）的 `CHGCAR` **还包含自旋电子密度**（文件里多一段数据），解析与可视化都要留意。
- **从电荷密度图看键性**（体相 Si vs NaCl 的经典对比）：
  - **电荷集中在原子之间** → 共价键；**电荷偏向一侧原子** → 离子键；
  - 看**梯度**更直观：**共价键梯度不明显，离子键梯度明显**。
- **VESTA 二维切面的一个限制**：`Utilities → 2D Data Display → Slice` 出的切面图**能显示 colorbar，但显示不了原子**——要在图上标出原子，得改用 `Edit → Lattice Planes...` 那条路（或配合等值面方案）。

- **来源文章**：路线 A（`chgdiff.pl` + `vtotav.f` + VESTA）见 `articles/20260930-差分电荷密度和平面平均差分电荷密度计算教程.md`；路线 B（VASPKIT / VESTA / 建模软件）见 `articles/20261001-VASP_vaspkit_VESTA_Materials_Studio_差分电荷.md`。
总电荷密度与 VESTA 操作细节另见 `articles/20261001-VASP_vaspkit_VESTA_电荷密度分布.md`。
- **脚本 / 工具**：`chgdiff.pl`（`chgdiff.pl <要减去的> <总电荷>` → `CHGCAR_diff`）、改版 `vtotav.f`（`ifort` 编译、交互选方向、横轴为格点数）、VESTA 相减步骤与 VASPKIT 替代路线见 `references/tools.md` 二.1、二.2、四.1、四.2。

---

## 十六、二维材料载流子迁移率（形变势理论）

- **方法定位**：形变势理论（Bardeen & Shockley, *Phys. Rev.* **80**, 72 (1950)）不考虑电子-声子与电子-电子相互作用，结果与实验**量级吻合**；更严格的是含电声耦合的玻尔兹曼输运（QE + EPW + MLWF 插值），但**计算量极大**，且 EPW 对二维材料存在已知问题。二维体系通常先走形变势路线。
- **公式与各量定义**：
  - 二维迁移率：`μ₂D = 2 e ℏ² C₂D / (3 k_B T |m*|² E₁²)`
    ⚠️ 原文公式是**图片**，此处按形变势理论常用写法补出；**套用前请与原文/文献核对前缀系数与 `m*` 的定义**（有的文献用输运方向有效质量 `m*`，有的引入平均有效质量 `md = √(m*_x m*_y)`；三维形式的指数与前置系数都不同）。
  - `E₁ = ΔE/(Δl/l₀)`：沿输运方向 CBM（电子）或 VBM（空穴）**能量随应变的变化率**，即形变势常数；
  - `m* = ℏ²(∂²E/∂k²)⁻¹`：输运方向有效质量（由能带在 Γ 附近的二次拟合求出）；
  - `C₂D = (1/S₀)(∂²E/∂δ²)`：二维弹性模量，`E` 为体系总能量、`S₀` 为优化后的面积；
  - `T`、`k_B`、`e` 分别为温度、玻尔兹曼常数与元电荷。
  - **单位换算（原文专门强调）**：用 Hartree 原子单位制最省事——1 bohr = 0.5292 Å、1 Hartree = 27.21 eV、ℏ = 1。拟合有效质量前先把能量 **eV ÷ 27.21 换成 Hartree**；迁移率式里的 ℏ、`e`、`k_B` 也要统一到同一单位制，否则数值会差几个数量级。
- **建模技巧（六角 → 方形）**：二维 InSe 原胞是六角，直接施加单轴应变很别扭；用**根号建模**（√3 超胞一类）把原胞转成**方形超胞**再施加应变，操作效率高、计算量增加可接受。
- **四步计算**：
  1. **结构优化**：`ISIF=3`、`IBRION=2`、`NSW=200`、`EDIFF=1E-5`、`EDIFFG=-0.01`、`PREC=Accurate`、`ENCUT=500`、`GGA=PE`、`ISMEAR=0 SIGMA=0.05`、`LREAL=.FALSE.`、`NPAR=4`；**二维体系用 `OPTCELL` 冻结 c 方向**（如 `100/010/000`）；`POTCAR` 按 POSCAR 元素顺序 `cat` 拼接。
  2. **静态自洽**：`ISIF=2`、`NSW=0`、`IBRION=-1`，k 网格加密（示例 21×13×1）；**要取真空能级就加 `LVHAR=.TRUE.`**（得到 `LOCPOT`）。
  3. **能带**：line-mode 走方形胞高对称路径（示例 `Y–Γ–X–S–Y`），`ICHARG=11`（或 2）、`LORBIT=11`；用于取 Γ 附近色散拟合 `m*`。
  4. **应变序列**：对 x、y 方向分别施加 **−2% ~ +2%（步长 0.005）** 的应变；**必须考虑泊松效应**——对 x 施加应变时**固定 x 与 z、只优化 y**（`OPTCELL` = `000/010/000`），对 y 施加应变时反之（`100/000/000`）。
- **批量与目录组织**：`mobility/{IS, mobility-x, mobility-y}`；`IS` 里放优化输入与 `2_scf/`（内含 `band/`）；`mobility.sh` 用 `cp -r ../IS ./$i` 生成每个应变目录，再用
  `sed -i "3s/$x/$(echo "$x*$i"|bc)/g" $i/POSCAR` 改晶格常数（**x 方向改 POSCAR 第 3 行、y 方向改第 4 行**）；PBS 脚本把 `opt → scf → band` 串起来并沿途复制 `CONTCAR`/`WAVECAR`。
- **数据处理三步**：
  1. **求 E₁**：以**真空能级为参考（不是费米能级）**——读能带结果中未扣费米能的 VBM/CBM，减去真空能级；再以应变为横轴线性拟合，斜率即 E₁。
  2. **求 C₂D**：读每个应变下的体系**总能量**，对应变做二次拟合，代入 C₂D 公式并换算单位。
  3. **求 μ**：把 `m*`、`E₁`、`C₂D` 代入迁移率公式，注意单位换算。
- **有效质量实操细节**：高对称路径按均匀撒点求每个 k 点的路径长度（第一个点设为 0）；取 Γ 起点附近 **4–8 个点**，用 `y = a + b·x + c·x²` 拟合，`m* = 1/(2c)`（原文示例 `c = 2.69188` → `m* = 0.19 m₀`，与文献一致）。
- **参考与工具**：结果见 *J. Phys. Chem. C* **2019**, *123*, 12781；人大迁移率软件包 ReMoC <https://gitee.com/jigroupruc>；作者博客 <https://yh-phys.github.io>。
- **来源文章**：`articles/20260930-VASP计算二维材料的载流子迁移率.md`
- **脚本 / 工具**：`mobility.sh`（复制基准目录 + `sed` 改晶格常数）、配套 PBS 串联脚本、`crecip.py`（倒格矢换算）的功能与坑见 `references/tools.md` 三.3–3.4；迁移率公式与单位换算见本节。

---

## 通用输出模板（给用户的流程答复应包含）

1. **一句话流程**：`优化 → 静态自洽 → 具体性质`。
2. **每步关键参数表**：INCAR（`PREC/EDIFF/EDIFFG/IBRION/NSW/ISMEAR/ISPIN/MAGMOM` 等）、KPOINTS 类型与密度、POTCAR 元素。
3. **提交与验证**：`mpirun`/Slurm 命令、用 `grep`/`vasprun.xml` 检查收敛的关键点。
4. **脚本命令**：如需生成输入文件，给出 `python scripts/gen_inputs.py ...` 具体命令及产物说明。
5. **风险与边界**：磁性/声子/输运各自易出错点，以及收敛不好时先调什么。

---

## 十七、外部脚本与工具：功能速查（指向 `tools.md`）

第十一～十六节的流程会用到一批**外部脚本 / 程序**。它们的功能、输入输出、依赖与坑统一登记在 **`references/tools.md`**——**要「用某个脚本」「找有没有现成工具」时先看它**，别在这一节重复描述。

| 脚本 / 工具 | 功能一句话 | `tools.md` |
| --- | --- | --- |
| `idealdeform.sh` | 理想拉伸/剪切的准静态加载（第十三节） | 三.1 |
| `vaspeqstress.sh` / `.py` | 迭代施加任意外压张量（第十四节） | 三.2 |
| `mobility.sh` + PBS | 二维迁移率批量应变目录与作业串联（第十六节） | 三.3 |
| `crecip.py` | 实空间基矢 → 倒格矢换算（第十六节） | 三.4 |
| `MEPSearcher` | string 法在二维 PES 上自动找 MEP（第十二节） | 三.5 |
| `chgdiff.pl` | 两个 `CHGCAR` 相减做差分电荷（第十五节） | 二.1 |
| `vtotav.f`（改） | 沿 X/Y/Z 的平面平均曲线（第十五节） | 二.2 |
| `VASP2GRO` / `XDATCAR_toolkit.py` / `xvg.py` | AIMD 轨迹转 GROMACS（第十一节） | 二.3–2.5 |
| VASPKIT / VESTA / GROMACS | 外部程序（二维光学性质、等值面与切面、轨迹分析） | 四.1–4.3 |
| ELATE / JARVIS-DFT | 弹性张量可视化与验证数据源（第十八节） | 四.4–4.5 |

- **自带脚本**（`scripts/`）的功能与依赖见 `scripts/README.md`；参数细节以各脚本 `--help` 与 docstring 为准。
- **脚本编写约束**：`scripts/` 下的脚本必须支持 `--selftest`（内嵌合成样例 + 数值断言，退出码 0/1），解析类默认输出 CSV/JSON，依赖分 L0–L3 级——详见 `scripts/README.md` 第一节与第八节。

---


## 十八、弹性矩阵与各向异性杨氏模量 / 泊松比

### ⚠️ 18.0 先确认原胞是不是「标准基矢形式」（算弹性/介电/压电前的头等大事）

**结论：做弹性常数之前，务必确认你的原胞是「标准基矢形式」（standard primitive cell）的原胞。**

- **给标准原胞的工具**：**AFLOW**、**VASPKIT**（命令：`(echo 6; echo 602) | vaspkit`）、以及 **`spglib`**（Python 库：`standardize_cell(cell, symprec, to_primitive=False/True)`，见 `references/tools.md` §4.12）。
- **通常不给标准原胞的**：**VESTA**、**Materials Studio**、**Materials Project** 下载的结构。
- 换胞的矩阵变换方法（手动转换）见外部教程：
  <https://yyyu200.github.io/DFTbook/blogs/2019/04/07/TransCell/>。

**实测对比（Si，同一套 INCAR/KPOINTS，仅原胞形式不同）**：

| 原胞 | `C11` | `C12` | `C44` | 非对角项 |
| --- | --- | --- | --- | --- |
| **标准基矢原胞（AFLOW/VASPKIT）** | 153.416 | 60.373 | 72.566 | **0**（矩阵干净，符合立方 3 个独立常数） |
| **非标准原胞（Materials Project）** | 179.640 / 179.640 / 188.662 | 51.817 / 42.795 | 63.911 / 54.890 | **±12.759**（三个方向 `C11` 都不一致） |

- 单位 GPa；两组用的是同一套参数（`IBRION=6`、`NFREE=2`、`ISIF=3`、`NSW=1`、`PREC=High`、
  `ENCUT=700`（1.3–1.5× 默认，需做收敛测试）、`EDIFF=1E-6`）。
- **非标准原胞算出来的矩阵"看着像结果"，其实不符合晶体的对称性**（立方体系本应只有 3 个独立常数），
  **VASP 不会报错**——这是典型的**静默错误**。
- 补救：非标准原胞的结果**需要做矩阵变换**才能对应到标准形式。
- ⚠️ **不只弹性常数**：原文明确说 **介电、压电** 等性质同样会受原胞形式影响。

> 提取弹性矩阵用 `vaspkit 2 203`（输出 `CrystalClass` / `SpaceGroup` / `StiffnessTensor`）——
> **先看它报的晶系与独立常数个数对不对**，这本身就是一道廉价的"结果体检"。
> 出处：公众号《原胞转化方法以及标准原胞在计算中的重要性》（obaica／学术之友）
> （`articles/20261001-原胞转化方法以及标准原胞在计算中的重要性.md`）。



- **物理框架**：线弹性 `σ = C·ε`，逆关系 `ε = S·σ` 中的 `S = C⁻¹` 是**柔度矩阵**。因果要分清：
  `C` 描述「变形产生多大应力」，`S` 描述「施加应力产生多大变形」。
  - 独立常数个数：2D 材料 6 个（3×3）；3D 材料 21 个（6×6）。按晶系还会减少：三斜 21 / 单斜 15 /
    正交 9 / 三方 7 / 四方 5 / 六方 5 / 立方 3。
- **VASP 三步**：
  1. **充分弛豫**：3D 直接弛豫；**2D 要先建 slab 并在弛豫中固定 c 轴**（`ISIF=4` 体积不变，
     或改源码 `constr_cell_relax.F`，见 `errors.md` §4.7）。
  2. **算弹性常数**：`IBRION=6`、`ISIF=3`、`NFREE=4`（四阶插值）、`NSW=1`；为提速打开 `ISYM=2`。
  3. **提取**：`grep -A 9 "TOTAL ELASTIC" OUTCAR`（喂脚本时常用 `grep -A 8 ... | tail -6`）；
     **单位是 kBar**，`1 kBar = 0.1 GPa`。
- **⚠️ 两个最容易错的换算**：
  1. **下标顺序**：VASP 输出的 6×6 弹性矩阵**不按 Voigt 顺序**，必须重排后才能求逆与计算。
     置换规则（行、列同理）：索引 `≤ 2` 保持不变；`3, 4 → 索引+1`；`5 → 3`。
  2. **2D 单位**：VASP 给的是 3D 的 kBar，而 2D 要 N/m。实用写法
     **`C_2D = C_3D(kBar) × 0.01 × c_z(Å)`**（先 ×0.1 转 GPa 再乘 c 轴长度），结果为 N/m。
- **各向异性杨氏模量与泊松比**：
  - 3D：取单位矢量 `a = (sinθcosφ, sinθsinφ, cosθ)`，则
    `1/E(a) = Σ_{i,j,k,l=x,y,z} a_i a_j a_k a_l S_ijkl`；
    再取垂直于 `a` 的 `b`（需额外引入绕轴角 γ）得
    `ν(a,b) = −E(a) · Σ_{i,j,k,l} a_i a_j b_k b_l S_ijkl`。
  - `S` 要从 6×6 展开成 **3×3×3×3**（Voigt 规则）：`i=j 且 k=l → S_mn`；`i≠j 且 k≠l → S_mn/4`；其余 `→ S_mn/2`。
  - 2D：只在 xy 面内（展开成 2×2×2×2），且可直接用解析式：
    `1/E(φ) = S₁₁cos⁴φ + S₂₂sin⁴φ + (S₃₃+2S₁₂)cos²φsin²φ + 2S₁₃cos³φsinφ + 2S₂₃cosφsin³φ`
    `ν(φ) = −E(φ)·[(S₁₁+S₂₂−S₃₃)cos²φsin²φ + S₁₂(cos⁴φ+sin⁴φ) + (S₁₃−S₂₃)(cosφsin³φ − cos³φsinφ)]`
- **后处理与出图**：
  - 3D：读矩阵 → 重排 + 转 GPa → 求逆得 `S` → 展开成 4 维 → 球面采样（θ、φ 各约 500 点）→
    求 `E(a)` → `matplotlib` 的 `plot_surface` 画三维曲面。
  - 2D：单位换算后同样求逆 → 展开 2×2×2×2 → φ 采样（约 1000 点）→ **极坐标双子图**（左 `E(φ)`、右 `ν(φ)`）。
  - **交叉验证**：3D 结果可与 **ELATE** 对比；2D 可把文献里的弹性矩阵代入脚本复现（原文即用此法自检）。
- **参考数据源**：JARVIS-DFT（如 #7974 的 `FD-ELAST` 与配套 `OUTCAR`）适合做练手与验证。
- **工具与脚本**：见 `tools.md` 三.6（弹性矩阵后处理脚本）、四.4（ELATE）、四.5（JARVIS-DFT）；
  自带复刻版见 `scripts/README.md` 的 `post/elastic.py`（planned）。
- **来源文章**：`articles/20261001-VASP计算材料的弹性矩阵和杨氏模量.md`
  ⚠️ 该文代码块来自网页高亮组件，**抓取时空格/缩进会丢失**（如 `for m in range(6)` 变成 `for m inrange(6)`），
  **不要直接复制运行**，按逻辑重写。

---

## 十九、STM 模拟（VASP → `PARCHG` → 图）

- **两步思路**：① 先做**自洽**，必须留下 `CHGCAR` 与 `WAVECAR`；② 再做**STM 一步**——让 VASP 写出
  **带分解的部分电荷密度 `PARCHG`**，最后用 `vaspkit` 把它画成恒定高度 STM 图。
- **第一步（自洽）INCAR 要点**：`LWAVE=.TRUE.`（写 `WAVECAR`）、`LCHARG=.TRUE.`（写 `CHGCAR`）、
  `ADDGRID=.TRUE.`、`LORBIT=11`、`LREAL=.FALSE.`、`PREC=Normal`、`ISMEAR=0 SIGMA=0.05`、
  `NELM=60`、`NELMIN=6`、`EDIFF=1E-08`、`LVHAR=T`。
- **第二步（STM）**：把自洽的 `POSCAR`/`POTCAR`/`KPOINTS`/`CHGCAR`/`WAVECAR` 复制过来，在 INCAR 里**追加**：
  `LPARD=.TRUE.`、`LSEPK=.FALSE.`、`LSEPB=.FALSE.`、`NBMOD=-3`、`EINT=-0.1 0.1` → 跑完得到 **`PARCHG`**。
  - 参数含义（原文逐条解释过）：
    - `LPARD`：是否计算**部分（能带 / k 点分解）电荷密度**；**从 `WAVECAR` 读入的轨道必须是先前已收敛的**；
    - `LSEPK`：`=.TRUE.` 每个 k 点单独写 `PARCHG.*.nk`；`=.FALSE.` 合并成一个文件；
    - `LSEPB`：`=.TRUE.` 每个能带单独写 `PARCHG.nb.*`；`=.FALSE.` 合并为 `PARCHG.ALLB.*` 或 `PARCHG`；
    - `NBMOD`：用哪些带——`>0` 表示 `IBAND` 中的个数（**给了 `IBAND` 就不要再手设 `NBMOD`**）；`0` 所有带
      （含未占据）；`-1` 默认（总电荷密度）；**`-2` 用 `EINT` 指定能量范围**；**`-3` 同 `-2`，但能量是相对费米能
      给出的**（STM 常用：`NBMOD=-3` + `EINT=-0.1 0.1` 表示费米面附近 ±0.1 eV）；
    - `EINT`：配合 `NBMOD=-2/-3` 的能量范围。
- **第三步（出图，vaspkit）**：
  - **先打开自动绘图**：`vi ~/.vaspkit` 把 `AUTO_PLOT` 改成 `.TRUE.`——**不打开就不出图**；
  - **单张恒定高度图**：`vaspkit 325 1 0.5 8 8`——`325` 是 STM 功能；`1` = **恒定高度模式**；`0.5` = 高度；
    `8 8` = 沿 a、b 方向的重复单元数；
  - **多高度（做动态图用）**：`vaspkit 325 2 0.5 2 0.2 8 8`——给出高度范围与步长（示例产出
    `STM_0.50.jpg … STM_1.50.jpg`）；
  - **样式自定义**：第一次运行会生成 `PLOT.in`，可改 `colormap`（示例 `RdBu`）、`contour_levels`、
    `contour_limits`、`display_colorbar`、`display_level_value`、`display_contour`、`colorbar_shrink`、
    `colorbar_orientation`、`font_family`。
- **已知坑**：
  - `vaspkit` **不能直接设置输出图片的格式与长宽比**，图四周留白多——原作者用 PIL 写了裁白边脚本；
  - 多高度模式**在某个高度就截止**（原作者怀疑是程序问题），所以实际图片数可能少于预期；
  - 出图前务必确认 `~/.vaspkit` 的 `AUTO_PLOT=.TRUE.`，否则 `325` 跑完没有任何图片。
- **配套脚本（原文给出，逻辑可复用）**：① 遍历当前目录 `*.jpg`，按非白像素边界裁掉四周空白；
  ② 按文件名中的高度数字排序、在图上标红字、合成 `STM_animation.gif`（`duration=500 ms`）。
  自带复刻计划：`scripts/` 的 `post/stm_frames.py`（planned）。
- **来源文章**：`articles/20261001-VASP_vaspkit_STM_模拟.md`（该文代码块在抓取时空格丢失，不能直接复制运行）

---

### 恒高 vs 恒流，以及第三条路线（`STM-2DScan.py`）

上面走的是**恒定高度（constant-height）**模式。两种模式的差别与坑（社区经验）：

- **恒定高度**：在固定高度切一个 xy 面，**容易做**、结果稳定；
- **恒定电流（constant-current）**：要**搜索针尖高度**（使电流恒定），**各程序算法不同**；
  ⚠️ **对表面高度落差较大的体系（例如笼状团簇吸附在衬底上），恒流模拟结果可能不稳健、甚至不被支持**——
  这也是本节把恒高作为主路线的原因。
- 想同时要两种模式：**`STM-2DScan.py`**（GPL，原作者 @叠加态/lipai）：
  - **输入**：任意 CHGCAR 格式的体数据（`CHGCAR`、`PARCHG`，甚至 BSKAN 的 `CURRENT`）；
  - **三种模式**：① 恒高；② **恒流**；③ 直接从三维密度在给定高度切 xy 面
    （与恒高结果几乎一致，但更通用——也可以用来把 `CHGCAR`/`CURRENT` 画成二维图）；
  - 还可以**沿 a、b 方向复制原胞**，最后用 matplotlib 的 colormap 输出 `.png`；
  - 本库收集于 **`scripts/reference/stm_2dscan.py`**（原网页把脚本压成了单行，见文件头说明）。

> 参考实现思路：两种模式的工作方式与 ASE 的 `stm.scan` / `stm.scan2` 类似。

## 二十、OUTCAR 数据挖掘：用 `re` 抓取任意量并出图（pandas 路线 / numpy+matplotlib 路线）

- **什么时候用**：VASP 输出里有很多量**没有现成后处理程序**（例如每步的 CPU 时间 `LOOP+: cpu time`）。
  本节给的是**通用配方**；常见量（能量、力、磁矩、耗时、参数…）已经由 `scripts/parse/parse_outcar.py`
  覆盖，**先看自带脚本，不够再自己写**。
- **基本思路**：`re` 用正则把文本里的数值抓出来 → `pandas` 整理成表 → 画图并落盘 CSV。
- **最小配方**（把正则换成你要的量即可）：

  ```python
  import pandas as pd, re
  t = open("OUTCAR").read()
  match = re.findall(r"(LOOP\D: cpu time) (\d{2}\.\d{4})", t)   # 按需改正则
  df = pd.DataFrame(data=match)
  df1 = df[1].astype(float)          # ⚠️ 必须转成数值，否则画不出图
  a = df1.plot()
  fig = a.get_figure(); fig.savefig("1.png")
  df.columns = ["name", "LOOP+:cpu time"]
  df.to_csv("1.csv")
  ```

- **另一条路线（`numpy` + `matplotlib`）**：没装 pandas 时同样能做——`re` 抓数值 → 造 x 轴 → 画图 →
  `np.savetxt` 落盘：

  ```python
  import matplotlib.pyplot as plt, numpy as np, re
  t = open("OUTCAR").read()
  match = re.findall(r"(?<=cpu time )\d{2}\.\d{4}", t)   # 后行断言：只取数值本身
  a = len(match)
  x = np.linspace(1, a, a)                              # x 轴 = 步数
  y = [float(num) for num in match]
  plt.plot(x, y); plt.xlabel("step"); plt.ylabel("cpu time (s)")
  plt.savefig("1.png"); plt.show()
  np.savetxt("1.csv", y, delimiter=",", header="cpu time (s)", fmt="%s")
  ```

- **脚本化**：把上面存成一个可执行文件（第一行 shebang 写**本机 python 绝对路径**，例如
  `#!/public/home/XXX/miniconda3/bin/python3.9`），`chmod +x vasp-py`，然后在**含 `OUTCAR` 的目录**里
  `./vasp-py`，表格与图片就落在当前目录。
- **正则调试**：先用在线工具（如 regex101）验证模式，再写进脚本。两种写法返回的东西不一样：
  - 用**分组** `(LOOP\D: cpu time) (\d{2}\.\d{4})`：`re.findall` 返回**元组列表**，交给
    `pandas.DataFrame(match)` 正好按分组成列；但直接 `float(元组)` 会报错，要取 `match[i][1]`。
  - 用**后行断言** `(?<=cpu time )\d{2}\.\d{4}`：`re.findall` 直接返回**字符串列表**，可 `float()` 直接用，
    更适合 numpy/matplotlib 路线（少一层索引）。
- **常见疑问（补充说明）**：原作者给 `df1.plot(x="step", y="time")` 指定了轴名却不见显示——因为这里 `df1`
  是 **Series**，`x`/`y` 不会被当成它的"列名"来用。稳妥写法是直接命名坐标轴：

  ```python
  df1.plot(); plt.xlabel("step"); plt.ylabel("time")
  ```

- **实践提醒**：
  - 先 `grep <关键词> OUTCAR` 看目标行长什么样，再照着写正则（比凭空写可靠得多）；
  - 正则里数字用 `\d`、小数点用 `\.`，注意 OUTCAR 里负数/科学计数法（`-.12345E+02`）要单独处理；
  - 提取结果先 `print` 前几条核对，再交给 `pandas` 画图，避免"图出来了但数错了"。
- **自带脚本**：`scripts/parse/parse_outcar.py`（常见量的现成解析）；若要"按任意正则批量提取"，计划中的
  `scripts/` 的 `post/outcar_grep.py`（planned）就是本配方的产品化版本。
- **来源文章**：pandas 路线见 `articles/20261001-VASP_Python_数据挖掘_1.md`，numpy+matplotlib 路线与后行断言技巧见 `articles/20261001-VASP_Python_数据挖掘_2.md`（两文代码块在抓取时空格丢失，不能直接复制运行）

### 从 `OUTCAR` 提能带数据（纯 bash/awk 路线）

> 三个现成脚本：`scripts/reference/outcar_bands.sh`（本征值）、`outcar_kpath.sh`（k 路径）、
> `outcar_homo_lumo.sh`（HOMO/LUMO 与带隙）。来源是用户粘贴的一篇短文（原作者 郭麒麟）。

**1）先摸清三个锚点**

```bash
NBANDS=$(awk '/NBANDS/ {print $NF}' OUTCAR | tail -1)   # 能带数（注意取最后一行，见坑①）
NKPTS=$(awk  '/NKPTS/  {print $4}'  OUTCAR)             # 不可约 k 点数
grep -n "band No." OUTCAR | head                       # 本征值块的起始位置
```

**2）逐带导出本征值**（每个 k 点一行）

```bash
for i in $(seq 1 1 $NBANDS); do
  grep -A $NBANDS 'band No.' OUTCAR | grep "    $i    " | awk '{print $2}' > bands_$i.dat
done
```

**3）导出 k 路径——注意有两套单位**

```bash
NKPTS=$(awk '/NKPTS/ {print $4}' OUTCAR)
grep -A $NKPTS "k-points in reciprocal lattice and weights" OUTCAR   | awk '{print $1"  "$2"  "$3}' | tail -$NKPTS > kpath_1.dat    # 倒格矢（分数）坐标
grep -A $NKPTS "k-points in units of 2pi/SCALE and weight" OUTCAR   | awk '{print $1"  "$2"  "$3}' | tail -$NKPTS > kpath_2.dat    # 2π/SCALE 单位
```

> ⚠️ **这两套单位正是 `workflows.md` §二十七 里"有效质量横坐标该不该乘 `2π/a`"那场争议的根源**：
> 你手上是哪一套，决定了要不要再做 `2π/a` 的换算。**画能带图/拟合有效质量前，先明确自己是哪一套。**

**4）HOMO / LUMO（半导体由此得带隙）**

```bash
homo=$(awk '/NELECT/ {print $3/2}'   OUTCAR)   # 占据带里最高的那条
lumo=$(awk '/NELECT/ {print $3/2+1}' OUTCAR)   # 空带里最低的那条
nkpt=$(awk '/NKPTS/  {print $4}'    OUTCAR)
e1=$(grep "     $homo     " OUTCAR | head -$nkpt | sort -n -k 2 | tail -1 | awk '{print $2}')  # HOMO：该带在所有 k 点的最大值
e2=$(grep "     $lumo     " OUTCAR | head -$nkpt | sort -n -k 2 | head -1 | awk '{print $2}')  # LUMO：最小值
echo "HOMO band=$homo E=$e1"; echo "LUMO band=$lumo E=$e2"
# 带隙 ≈ e2 - e1
```

**四条坑（本库核对后补充，非原文内容）**：

1. **`NBANDS` 可能匹配到多行** → 变量会变成多行字符串、`seq` 直接失败；**加 `| tail -1`**。
2. **内层 `grep "    $i    "` 依赖固定列宽**：带序号到两位数、三位数时空格数就变了 →
   大体系（`NBANDS ≥ 10`）改用 `awk -v b=$i '$1==b {print $2}'` 更稳。
3. **`NELECT/2` 推带序号只适用于非自旋极化（`ISPIN=1`）**；`ISPIN=2` 要分自旋通道，带电体系（奇数电子）也不适用。
4. 原文的 `>>` 追加写法**重复运行会叠加内容**；首次导出用 `>`。

> 💡 若要**一步到位**：本库的 `scripts/parse/parse_outcar.py`（带 `--selftest`）已经能解析 `OUTCAR` 的
> 能量/TITEL 等信息；纯 bash 路线的优势是**不装任何 Python 库**、能在超算登录节点上直接跑。


---

## 二十一、机器学习势数据集：从 `vasprun.xml` 提取构型（FitSNAP 格式）

- **用途**：为 **FitSNAP**（SNAP 势）之类的机器学习势准备训练集——把 AIMD/多构型计算里**每一帧**的
  「能量 + 晶格 + 原子位置 + 受力 + 应力」抽出来，写成一份 JSON。
- **输入**：多帧 `vasprun.xml`（每帧含一个 `forces` 之类的结果块）+ 一个 POSCAR 结构的 `PPOSCAR`（用来取元素列表）。
- **数据来源与单位**（**必须与 JSON 里声明的单位一致，否则训练出来的势不可信**）：
  - 晶格：Å；位置：Å；能量：eV；受力：eV/Å；**应力：原文从 `vasprun.xml` 读出后 ×1000**
    （vasprun 里是 kBar，SNAP 要 bar）。
  - 元素列表：从 `PPOSCAR` 第 6 行（元素名）与第 7 行（各元素原子数）**展开成与原子一一对应的符号列表**。
- **原脚本的做法（行偏移法，可以借鉴但要知道它脆弱）**：
  1. 逐行扫 `vasprun.xml`，命中 ` <varray name="forces" >` 当锚点（**每帧一个**；可先
     `grep -c 'name="forces"' vasprun.xml` 数帧数）；
  2. 从锚点**向上**偏移取 3 行当晶格（`n - num_atom - 14 + i`，i = 0..2）；
     从锚点**向下**偏移取 3 行当应力（`n + num_atom + 3 + i`），并 ×1000；
  3. 锚点之后的 `num_atom` 行是各原子的位置与受力，每行取第 1–3 个数；
  4. `s_step` / `d_step` 控制**从第几帧开始、每隔几帧取一帧**；
  5. 按 SNAP 的字段约定组装并写 JSON。
- **SNAP JSON 的字段约定**（可照搬到其它 ML 势的数据准备）：
  `Label`、`LatticeStyle=angstrom`、`EnergyStyle=electronvolt`、`StressStyle=bar`、
  `AtomTypeStyle=chemicalsymbol`、`PositionsStyle`、`ForcesStyle=electronvoltperangstrom`。
- **坑（比脚本本身更重要）**：
  - **行偏移法非常脆弱**：它依赖 `vasprun.xml` 的节点顺序与行距（`-14`、`+3` 这类硬编码偏移），
    **换 VASP 版本、开/关某些输出（如 `LORBIT`、应力块）就会整体错位且不报错**——数据静默错误。
    更稳的做法是按标签解析：`xml.etree.ElementTree.iterparse` 逐节点取 `<varray name="...">`，
    或用 `pymatgen` 的 `Vasprun`（自带 `ionic_step_data`）。见下方"与自带脚本的关系"。
  - **锚点匹配是全等比较**（`text[n] == ' <varray name="forces" >\n'`）：行首空格数、属性顺序、
    自闭合写法一变就匹配不上 → 用 `'name="forces"' in line` 之类更宽容的判断。
  - **单位**：应力 ×1000 这一步是最容易漏的；位置/受力/能量的单位也必须在 JSON 里如实声明。
  - 原脚本是 python2 风格（`np.mat` 等），移植到 python3 要一并现代化。
- **与自带脚本的关系**：`scripts/parse/parse_vasprun.py`（planned）就是用 `iterparse` 做同一类提取的
  稳健版本；"按任意帧导出 ML 数据集"计划落在 `scripts/` 的 `post/snap_dataset.py`（planned）。
- **相关工具**：FitSNAP（SNAP 势训练）；若你的训练框架要的是 LAMMPS dump / extxyz，思路一样，
  只是输出格式不同（见 `tools.md` 四.6）。
- **来源文章**：`articles/20261001-vasprun_xml_to_json_file_天帝君豪的个人博客.md`（该文脚本在抓取时空格与换行丢失，不能直接复制运行）

---

## 二十二、高温声子：自洽声子理论（ALAMODE SCPH）

- **适用**：温度较高、**非谐效应显著**时，普通有限位移 / DFPT 声子谱会失效（虚频、频率随温度漂移）。
  **自洽声子理论（SCPH）** 通过迭代修正频率来处理非谐性，直接给出**不同温度下**的声子谱。
- **输入文件清单**（原文，`alamode-1.1.0`）：
  - `vasprun.xml`：MD 输出（构型与力的来源）；`PPOSCAR`：初始超胞；
  - `extract_disp.py` / `extract_force.py`：从 MD 轨迹里**挑结构**，分别导出**位移**与**受力**；
  - `Dfile`：两者按行合并——每行 `disp_x disp_y disp_z force_x force_y force_z`，共 N 行；
  - `alm.in`：提取力常数的输入；`anphono.in`：计算声子谱的输入。
- **步骤 1｜从 MD 造数据集**：`python extract_disp.py` → 按提示输入**起始步**与**间隔步**（例：共 1000 步、
  从第 1 步开始、每 5 步取一次）→ 得 `disp.dat`；`extract_force.py` 同样操作 → `force.dat`；
  再把两者**按行拼成 `Dfile`**。
- **步骤 2｜提取力常数**：`alm alm.in > alm.log` → 得到力常数文件（示例 `Nb.xml`）。
  - **四阶力常数用 `alm.in` + LASSO**：`&optimize` 里 `LMODEL=enet`、`CV=0`、
    `L1_RATIO` / `L1_ALPHA` / `CV_MINALPHA` / `CV_MAXALPHA` / `CV_NALPHA`、`STANDARDIZE=1`、`CONV_TOL=1e-9`；
  - **二阶力常数可用有限位移法**提取（官网手册）；
  - 其它关键字段：`&general PREFIX / MODE=optimize / NAT / NKD / KD`；
    `&interaction NORDER=5 / NBODY=2 3 3 2 2`；`&cutoff *-* None None 12.0 12.0 12.0`；
    `&position` 逐个原子给分数坐标。
  - ⚠️ **`&cell` 的晶格常数是 Bohr 单位**——原文明示"注意晶格常数单位的转换"，
    `1 Bohr = 0.529177208 Å`（换算表见 `references/constants.md`）。
- **步骤 3｜算 SCPH 声子谱**：`anphon anphono.in > anphono.log` → 得 `scph.scph_bands`
  （**含各温度的声子谱**）。
  - `&general`：`PREFIX`、`MODE=SCPH`、`FCSXML`（上一步的力常数文件）、`NKD`/`KD`、`MASS`；
    极性材料可选 `NONANALYTIC` / `BORNINFO`；
  - **温度扫描**：`TMIN` / `TMAX` / `DT`（示例 0 → 300、步长 100）；
  - `&scph`：`KMESH_SCPH`、`KMESH_INTERPOLATE`、`SELF_OFFDIAG`、`RESTART_SCPH`、`MIXALPHA`、
    `MAXITER`、`TOL_SCPH`；
  - `&cell`：**建议用原胞**（原文注明 "primitive cell is best"）；`&kpoint`：`KPMODE=1` 取声子谱，
    其后给出高对称路径点与插值点数。
- **与其它声子流程的关系**：`workflows.md` 第六节是**有限位移法**（phonopy / ALAMODE，谐近似）、
  第七节是**晶格热导率**；SCPH 是**处理非谐、拿高温声子谱**的第三条路线。
  同站另有 **TDEP** 路线（登记见 `tools.md` 与 `articles/`）。
- **来源文章**：`articles/20261001-alamode_scph计算高温声子谱_天帝君豪的个人博客.md`（两处输入文件在抓取时被压成多行块，字段仍可辨读）

---

## 二十三、波恩有效电荷（Born effective charge）与极化

- **它是什么**：`Z*` 描述「原子位移 → 宏观极化」的耦合强度，是**铁电性、LO-TO 劈裂、介电响应**的核心量。
  VASP **不会**直接输出"极化"，得到的是把位移与极化联系起来的**张量**；**极化由 `Z* · u` 乘出来**
  （与第一节"手动破缺对称"配套使用）。
- **两条路线**：
  1. **DFPT（现代推荐，一次算完）**：静态自洽时加 **`LEPSILON=.TRUE.`**（配 `IBRION=-1`、`NSW=0`、`ISIF=2`），
     VASP 用密度泛函微扰理论**同时给出介电张量与波恩有效电荷**（金属/极性体系的适用条件见官方手册）。
  2. **Berry 相 + 手动位移（本文路线，老手册的算法）**：
     ① 先静态 scf（`IBRION=-1`、`NSW=0`、**`LCHARG=.TRUE.`**）拿到 `CHG` / `CHGCAR` / `WAVECAR`；
     ② 把它们拷进新目录（连同 `INCAR`/`POSCAR`/`POTCAR`/`KPOINTS`，共 7 个输入文件）；
     ③ 新 INCAR 里加 **`LCALCPOL=.T.`**（必要时 `LBERRY=.T.`）、**`NPPSTR=2`**、**`DIPOL=0.25 0.25 0.25`**；
     ④ **手动给目标原子一个小位移**（要算谁的 `Z*` 就挪谁）；
     ⑤ 在 `OUTCAR` 里搜 **`Ionic dipole moment`**（旁边还有 `Electronic dipole moment`）；
     ⑥ `ΔP/Δu` 就是该原子的波恩有效电荷。
     - 想更可靠：**取几个不同大小的位移，把 P 对 u 拟合直线取斜率**（本质是有限差分）。
- **INCAR 参考**（本文给的静态 + 极化设置）：`EDIFF=1E-6`、`PREC=High`、`NELM=200`、`NELMIN=2`、`NSW=0`、
  `IBRION=-1`、`ISMEAR=0 SIGMA=0.05`、`ISIF=2`、`EDIFFG=-0.005`、`POTIM=0.2`、`LCHARG=.T.`、`NPAR=4`、
  `LREAL=Auto`，再加 `LCALCPOL=.T.` / `LBERRY=.T.` / `NPPSTR=2` / `DIPOL=0.25 0.25 0.25`。
- **`DIPOL` 的坑**：数值可以随意给，但**不要正好落在某个原子上**，更要保证**原子在计算过程中不会穿过它**
  （手册明确要求；穿过会出什么问题作者也没试过，别试）。
- **与其它章节的关系**：第一节讲"想要铁电畸变必须手动破缺对称"，本节讲"有了位移怎么把它变成极化/有效电荷"；
  声子的 **LO-TO 劈裂**与介电性质同样依赖 `Z*`（见第六节、`errors.md` §五）。
- **⚠️ 来源与可信度**：原文是作者自称的"个人笔记"，**明说不保证正确性**。本节按他的描述整理，
  正式使用前请对照官方手册的 `LEPSILON` / `LCALCPOL` / `DIPOL` 条目核对。
- **来源文章**：`articles/20261001-VASP计算的个人笔记_二.md`

---

## 二十四、吸附能 / 掺杂能 / 迁移能垒：起步算法

> 面向刚上手的人：这里只给**能立刻算起来的做法与公式**，参数细节按需回看第一、二节。

- **吸附能**：
  1. 分别优化并算能量：`E1` = 吸附物分子、`E2` = 干净表面、`E3` = 吸附后的体系；
  2. **`E_ads = E3 − E2 − E1`**，**越负越容易发生**；
  3. 比较不同构型（例如 N₂ 横躺 vs 竖立）就能判断最可能的吸附方式。
  - **三个体系必须同一格子、同一套参数**（`ENCUT`/k 点/赝势/展宽一致），否则相减没有意义。
- **掺杂能**：把"吸附物"换成"掺杂原子"，公式与之类似。
- **离子迁移能垒（扩散势垒）**：
  - **粗算（等距插点）**：在稳定位 A → 稳定位 B 的路径上**等距插若干点**，逐点单点算能量，
    **最高点能量 − 稳定点 A 的能量 = 能垒**；
  - **精算**：用 **NEB / CI-NEB**（VASP 内嵌，直接用即可，不必先懂原理）；
  - **另一条路：二聚体法（dimer）**——`IBRION=44`（改进的二聚体方法）可以**直接从初态出发找鞍点**，不需要像 NEB 那样先构造一条完整路径；路径不明确、或只想快速定位鞍点时很省事（<https://www.vasp.at/wiki/index.php/Improved_Dimer_Method>）。
  - 电池材料常问的"锂离子在正极中的迁移能垒"就是它。
- **孪晶晶界能**（顺带）：
  - 计算上能模拟的主要是**孪晶晶界**（两侧晶粒关于界面**对称**）：先切目标晶面（如 `111`），
    再把上半部分原子镜像拼上；
  - **晶界能 = (含晶界的晶胞能量 − 初始晶胞能量) / 2**——除以 2 是因为一个晶胞里有**两个**晶界；
  - 扫不同取向（`001`/`010`/`100`/`110`/`011`…），能量最低者最稳定。
- **入门导航**：这三类算例的"面向实验人员"讲解（含实验类比、四个输入文件、常用数据源）见
  `references/onboarding.md`。
- **来源文章**：`articles/20261001-材料科学实验人员_如何入门_第一性原理计算_计算材料学_VASP_从0到上手.md`（原文面向实验人员，示例为 MoO₃ 表面吸附 N₂、石墨烯上 Li 迁移、孪晶晶界）。

---

## 二十五、Wannier90 紧束缚模型（VASP 接口）

> 目标：把 DFT 波函数变成**最大局域化 Wannier 函数（MLWF）**，据此做能带插值、构造**紧束缚（TB）模型**、
> 算拓扑量与输运量。原文以 MoSi₂N₄（无 SOC / SOC）与 MnBi₂Te₄（铁磁/反铁磁）为例。

### 25.1 版本与安装（选错版本是最常见的坑）

| 选择 | 与 VASP 的接口 | 代价 |
| --- | --- | --- |
| **wannier90 1.2** | 开箱可用 | **做不了自旋向上/向下分别的能带**（即无 SOC 的铁磁/反铁磁体系） |
| **wannier90 2.1** | 是能与 VASP 结合的最新版，但**默认接口不好**，需打补丁 | 需用肖承诚的接口，且**只针对 VASP 5.4.4** |

- 2.1 的接口：`VASP2WAN90_v2_fix`（<https://github.com/Chengcheng-Xiao/VASP2WAN90_v2_fix>）。
- **wannier90 编译**：
  ```bash
  tar -zxvf wannier90-2.1.0.tar.gz
  cd wannier90-2.1.0/
  cp config/make.inc.ifort make.inc   # 用自己的编译器模板，检查 ifort / mpiifort
  make
  make lib                            # 得到 libwannier.a
  ```
- **VASP 打补丁并链接**：
  ```bash
  patch -p0 < mlwf.patch              # mlwf.patch 来自接口仓库
  # 在 makefile.include 中加入（注意路径）：
  #   CPP_OPTIONS += -DVASP2WANNIER90v2
  #   LLIBS += /path/to/wannier90_distro/libwannier.a
  make all
  ```

### 25.2 三步流程

1. **常规自洽（scf）**：拿到 `CHGCAR`/`WAVECAR`（`LWAVE=.TRUE.`、`LCHARG=.TRUE.`）。
2. **能带分析**：把 `CHGCAR` 拷到能带目录，加 **`ICHARG=11` + `LORBIT=11`** → 得到 `PROCAR`，
   用它画 **fatband**（再加上 PDOS），确认**费米面附近的轨道成分**。
3. **Wannierization**：写 `wannier90.win`，在 INCAR 里加 **`LWANNIER90=TRUE`**（其余 `KPOINTS`/`POTCAR`/`POSCAR`
   与自洽一致）→ VASP 跑完会**自动补全 `.win`**（结构、k 点等信息）并输出 Wannier 接口文件
   `wannier90.amn`、`wannier90.mmn`、`wannier90.eig`（原文把 `.amn` 写成 “`.amm`”，以标准文件名为准）
   → 再运行 `wannier90.x wannier90`（`.win` 名不是 `wannier90.win` 时，参数换成对应前缀，如 `wannier90.x name`）
   → 得到 `wannier90.chk`（restart 用）与 `wannier90_band.dat`（与 DFT 能带对比）。

⚠️ **INCAR 里不要用 `NPAR`**——原文明确说会出错。

### 25.3 `num_wann` / `num_bands` 怎么定（最容易算错的地方）

- **`num_bands` = INCAR 的 `NBANDS`**，并且必须 **≥ `num_wann`**。
- **`num_wann` = Σ（该元素在原胞中的原子数 × 投影轨道的电子数）**，其中 **s = 1、p = 3、d = 5**。
  例（MoSi₂N₄ 单层，投影 `Mo: d`、`Si: p`、`N: p`，原胞含 1 Mo、2 Si、4 N）：
  `num_wann = 1×5 + 2×3 + 4×3 = 23`。
- **SOC（`spinors=.true.`）时 `num_wann` 翻倍**（23 → 46），`num_bands` 同步加大且仍等于 `NBANDS`。

### 25.4 `wannier90.win` 的关键项

```
num_bands = 48          # = INCAR 的 NBANDS，且 >= num_wann
num_wann  = 23
dis_win_min  = -20.0    # 解纠缠窗口
dis_win_max  =  30.0
dis_froz_min = -11.50   # 冻结（Frozen）窗口
dis_froz_max =   4.0
num_iter    = 200       # 最大局域化迭代（dis_num_iter 是解纠缠那一步）
begin projections
Mo : d
Si : p
N  : p
end projections
bands_plot = true
begin kpoint_path
K -0.3333 0.6666 0.0   G 0.0 0.0 0.0
G  0.0 0.0 0.0         M 0.0 0.5 0.0
M  0.0 0.5 0.0         K -0.3333 0.6666 0.0
end kpoint_path
bands_num_points 101
bands_plot_format gnuplot xmgrace
```

- **能量窗口是相对"未做费米能修正"的能带**；**冻结窗口尽量包含整数条能带、且不包含没投影的轨道**；
  `dis_froz_min` 有时设小一点（多包含些能带）反而**收敛更快**。

### 25.5 影响投影质量的关键参数

- **`num_bands`**：要足够多，既覆盖你要研究的能带，也覆盖**投影子有成分的能带**。
- **投影轨道**：动手前**务必**做一次能带成分分析（fatband + PDOS），按费米面附近的实际成分选
  （例：Si 的 p 轨道在 M 点价带贡献大，不选它那个位置就拟合不好）。
- **能量窗口**：解纠缠 + 冻结两个窗口，见上。
- **k 网格密度**：越密越能拿到**更远距离的 hopping**，对金属尤其重要；拓扑半金属在"小区域能带反转"处必须加密。

### 25.6 怎么判断投影好不好

- **看 `wannier90.wout` 里的 `WF centre` 与 spread**：中心应落在原子位置附近，**spread 与晶格常数相当、越小越好**
  （对比笛卡尔坐标即可看出 Wannier 中心是否对应 Mo/Si/N 的排布）。
- **对比插值能带与 DFT 能带**：两者应当重合；如果出现**曲折的条纹**，说明 Wannier 函数**不够局域**。
- **调参诀窍**：**一开始把 `num_iter` 设为 0**，先看 spread 有多大；spread 太大就调窗口与投影，
  实在没办法再打开 `num_iter` 做最大局域化。

### 25.7 三种自旋情形

- **无 SOC**：按上面的流程即可。
- **SOC（含 SOC+铁磁/反铁磁）**：自洽加 **`LSORBIT=TRUE`**，并改用 **`vasp_ncl`** 提交；
  能带成分一般不变，所以**投影轨道通常不用改**；但 `.win` 里要 **`spinors = .true.`**，
  **`num_wann` 翻倍**、`num_bands` 同步加大。
- **无 SOC 的铁磁/反铁磁**：INCAR 加 **`ISPIN=2`**；要准备**两份**输入 **`wannier90.up.win` 与 `wannier90.dn.win`**，
  并且**分别运行** `wannier90.x wannier90.up` 和 `wannier90.x wannier90.dn`
  （原文评论区作者的回答；只跑一次不会生成另一自旋的文件）。
  - **反铁磁**里不同自旋的原子用**分数坐标**指定投影，例如：
    `begin projections` → `f= 0 0 0 : d`、`Bi : p`、`Te : p` → `end projections`，
    另一份 `.win` 里换成 `f= 0 0 0.5 : d`（即另一个自旋的子晶格）。

### 25.8 参考资源

- 接口关键词说明：`VASP2WAN90_v2_fix` 的 wiki（<https://github.com/Chengcheng-Xiao/VASP2WAN90_v2_fix/wiki/Keywords>）。
- `num_wann` / `num_bands` / energy window 的设置规则：科学网博客 <http://blog.sciencenet.cn/blog-2909108-1154273.html>；
  《构造 Wannier90 函数的要点》：<https://www.jianshu.com/p/ed0c5fd0d14f>。
- 练习体系：MoSi₂N₄（无 SOC / SOC）、MnBi₂Te₄（FM/AFM）、Bi₂Se₃（拓扑绝缘体）。
- **来源文章**：`articles/20261001-一文搞定VASP_wannier90构造紧束缚模型.md`（原文为"材料基因论坛"帖的转载稿）。

---

## 二十六、AIMD 验证结构热力学稳定性

> 用途：**不靠声子**，直接用第一性原理分子动力学（AIMD）看"这个结构在某个温度下能不能保持住"。
> 官方参考算例：**Liquid Si - Standard MD**（<https://www.vasp.at/wiki/index.php/Liquid_Si_-_Standard_MD>）。

### 26.1 准备

- **`KPOINTS`**：MD 模型很大，**用 Γ 单点即可**（`Gamma / 1 1 1 / 0 0 0`）。
  - 💡 **Γ-only 就用 `vasp_gam` 可执行文件跑，比 `vasp_std` 更快**（社区提示；`vasp_gam` 不做 k 点并行、
    内存与耗时都更省）。
- **`POSCAR`**：**模型尽量大，扩胞到 100 个原子以上**（否则有限尺寸效应会让"稳定性"结论不可靠）。
  - ⚠️ **初始速度是随机的**：若不在 `POSCAR` 里显式给出原子初速度，VASP 会**随机生成**——这「完全可以」，但要意识到：**两次计算的轨迹因此很难逐一对比**（想复现/对比轨迹就得自己给初速度或从 `CONTCAR` 续算）。
  - 积分器：`IBRION=0` 默认用 **Verlet**；如果 VASP 链接了 `stepprecor.o`，则用**四阶预测-校正器**。
- **`INCAR`（NVT + Andersen 热浴示例）**：

```
ISMEAR   = 0
IBRION   = 0          # 0 = 分子动力学
ISIF     = 2          # 见下方 26.2：NVT 要固定晶胞
MDALGO   = 1          # 1 = Andersen thermostat
ANDERSEN_PROB = 0.5
SIGMA    = 0.1
LREAL    = Auto
ALGO     = Fast
PREC     = Normal
ISYM     = 0
TEBEG    = 1000       # 起始温度
TEEND    = 1000       # 结束温度
NSW      = 3000       # 总步数
POTIM    = 3          # 时间步长（fs）
NCORE    = 8
```

- **`TEBEG`/`TEEND` 决定热浴温度**（两者相同 = 恒温）。
- **总时长 = `NSW × POTIM`**：原文明说**至少跑 10 ps**（例：3000 步 × 3 fs = 9 ps，可再加大）。

### 26.2 ⚠️ 系综与 `ISIF` 要配套（原文这里写错了）

- **`ISIF=2`：晶胞固定**（体积、形状都不变）→ 这才是标准的 **NVT**；
- **`ISIF=3`：允许晶胞变化**（体积与形状都动）→ 是 **NPT 味道**的设置。

原文标称 "NVT" 却写了 `ISIF=3`，**评论区当场指出「ISIF 应该 2」**——想做恒容 NVT 就写 `ISIF=2`；
只有确实要让胞随温度膨胀/收缩（NPT）时才用 `ISIF=3`。

- 其它热浴与系综见官方 `MDALGO` 手册：<https://www.vasp.at/wiki/index.php/MDALGO>。

### 26.3 一个省时间的事实：MD 里 `EDIFFG` 不参与判据

- MD（`IBRION=0`）的**步数上限是 `NSW`**；`EDIFFG`（力的收敛判据）**不会用来提前结束 MD**。
- 所以**不要把 `EDIFF`/`ENCUT` 设得比静态计算还严**——每一步只做有限电子步，判据过严只会白烧机时
  （社区反馈："`ENCUT=500`、`EDIFF=1e-5`、`EDIFFG=-0.01` 这个设置过于精确了"）。

### 26.4 跑完怎么分析

1. **能量时间序列**（最关键的一步）：

```bash
grep "free energy" OUTCAR | awk '{print $5}' > energy.dat
```

   画成图看**有没有漂移**：能量**有波动但围绕一个平台** → 该温度下结构稳定；
   **持续单调上升/下降**（漂移）→ 结构在该温度下不稳定，或步长/设置有问题。
2. **看轨迹结构**：把 `CONTCAR`（或 `XDATCAR`）导入 **OVITO**（见 `references/tools.md` 四.10），
   观察**结构是否被破坏**：有变化但没有散架，配合能量判据才能下结论。

### 26.5 社区追问（原帖未解答，按通用做法整理）

- **"设 400 K 温度却一路冲到 1200+"**（提问者跑的是 NPT）：先核对三件事——
  `POTIM` 是否偏大（含氢体系尤其敏感）、`ISIF` 是否让晶胞发生了变化、以及**是否留足了平衡时间**
  （前一段的升温过程不能当结果用）。
- **"扩胞后要不要先优化？"**：要。先用常规 `opt` 得到平衡结构再启动 MD，否则初始应力/受力偏大，
  能量曲线起步就会漂移。
- **"结构变了但没散，算稳定吗？"**：判据不能只看图。至少同时满足：**能量/温度无漂移**、
  在目标温度下**长时间保持同一相**、键长/配位数（必要时 RDF）合理。有限温度下结构本来就会振动、会有起伏。

- **来源文章**：`articles/20261001-第一性原理分子动力学分析结构稳定性_VASP-AIMD.md`（原文只有一个算例与一条 `grep`，本节括注了社区纠正与追问整理）。

---

## 二十七、有效质量（电子 / 空穴）

> 用途：载流子迁移率、热电、光吸收都要用到带边有效质量 `m*`。两条路：**手工拟合能带** 或 **VASPKIT**。

### 27.1 方法一：能带 + 二次拟合

1. **优化结构**（二维材料要处理范德华校正、用 `OPTCELL` 控制晶格，按实际体系决定）；
2. **`scf` 自洽** → 取 `CHGCAR` 做**能带**计算；
3. 能带算完得到 **`highk.dat`**（高对称点的坐标），对应能带图上的高对称位置；
4. **定位带边**（求电子有效质量取导带底、空穴取价带顶），在它附近取点——示例取了 **9 个点**；
   ⚠️ **只取一侧**（例如只取 `X–Γ` 一段）：不同 k 路径的曲率不同，两侧混在一起拟合没有意义；
5. **单位换算**（见下方 27.2 的争议提示）：纵坐标 eV → Hartree：`y' = y / 27.21`；
6. **拟合**：用 **2 阶多项式** `E(k) = E₀ + C·k²`，取二次项系数 `C`，则 **`m* = 1/(2C) · m₀`**。

- **为什么是 `1/(2C)`**（评论区有人问）：在**原子单位制**（`ℏ = 1`、`m₀ = 1`）下，
  `E(k) = E₀ + k²/(2m*)`，与拟合式对比即得 `C = 1/(2m*)` → `m* = 1/(2C)`。
  这正是**必须先把能量换成 Hartree、波矢换成 Bohr⁻¹** 的原因。

### 27.2 ⚠️ 横坐标换算有争议，务必自己核对

- **物理上的要求**：`m* = 1/(2C)` 只有在上面的**原子单位制**下才成立，所以横轴必须是 **Bohr⁻¹**。
- **若你的横坐标本身就是"倒空间长度（1/Å）"**：换算只需 **`x' = x × 0.5292`**
  （1 Bohr = 0.5292 Å）——这是评论区对原帖的质疑，**单位换算角度看它是对的**。
- **原帖写的是** `x' = x × 0.5292 × 2π/a`（`a` 取垂直于高对称路径面的晶格常数）——
  这是把横坐标当成**以 `2π/a` 为单位的归一化坐标**时的写法。
- **怎么判断手上是哪种**：看能带路径横轴的最大值——数值是"路径几何长度"（Å⁻¹ 量级）就用第一种；
  若是 `0.5`、`1` 这类归一化数值，才需要乘 `2π/a`。
- 💡 **最省事的做法是绕开这一步**：直接用 **VASPKIT 912/913**（它内部完成单位处理与拟合），
  或先用一个**文献里已有 `m*` 值**的材料把整个流程跑通、对上了再算新体系。

### 27.3 方法二：VASPKIT（911 / 912 / 913）

1. 先算能带，得到带边（价带顶 / 导带底均落在高对称 K 点上）；也可直接用 **`vaspkit 911`** 得到带边位置；
2. 准备 **`VPKIT.in`**；
3. 运行 **`vaspkit 912` 或 `913`** 生成 `KPOINTS`、`POTCAR`；
   ⚠️ **`INCAR` 必须自己写**——原文明说不能用 VASPKIT 生成的那份
   （社区里也有人追问"912 这一步的 INCAR 有什么要求"，原帖未答；
   **以官方教程为准**：<http://vaspkit.cn/index.php/52.html>）；
4. 提交 VASP 任务；然后把 **`VPKIT.in` 第一行的 `1` 改成 `2`**，**再次运行 `vaspkit 913`**，
   输出的就是**空穴与电子的有效质量**。

### 27.4 与其它章节的关系

- `workflows.md` 第十六节（二维载流子迁移率，形变势法）里也要用 `m*`：那边强调
  **先把能量 eV ÷ 27.21 换成 Hartree**，与本节的单位要求一致；
- 带边位置的确定依赖能带流程（见第三节）与态密度（第四节）。

- **来源文章**：`articles/20261001-基于vasp的电子和空穴的有效质量计算方法.md`（原文由科研服务公众号发布；本节已把评论区的换算质疑与
  "为什么是 1/(2C)"一并整理，并标注了争议点）。

---

## 二十八、收敛性测试：k 点与 ENCUT（含自动化脚本）

> **为什么必做**：`ENCUT` 直接决定计算量（运行时间 ∝ `ENCUT³`，见 `references/performance.md`），
> k 点密度同理。选择标准是：**再加大参数时总能的变化小于阈值**（常见取 ~1 meV/atom 量级），
> **且耗时还能接受**。脚本：`scripts/reference/kpoint_encut_test.sh`（作者 June976，jun997.xyz）。

### 28.1 准备

- 同级目录下放好 **`POTCAR`** 与 **`POSCAR`**（脚本按此读取），并已安装 **VASPKIT**。
- 先 `grep ENMAX POTCAR` 看赝势建议的截断能：脚本取 **`ENCUT0 = max(ENMAX) × 1.3`** 作为 ENCUT 测试的起点
  （与 `errors.md` §1.4 的 `ENCUT ≥ max(ENMAX)×1.2–1.3` 一致）。

### 28.2 脚本做两轮扫描

1. **k 点测试**：对间距 `0.05 / 0.04 / 0.03 / 0.025 / 0.02 / 0.01` 各建一个目录，
   用 VASPKIT 生成 KPOINTS：

```bash
echo -e "102\n2\n$i\n" | vaspkit     # 102 = 自动 K 点；2 = Gamma center；$i = 间距
```

   `ENCUT` 固定为 `ENCUT0`。
2. **ENCUT 测试**：从 `ENCUT0` 起 `+100 / +200 / +300` 四档，k 间距固定 `0.03`。
3. 每档跑一次**静态**计算，并抓两个数写进结果文件：

```bash
E=`grep "energy without" OUTCAR | tail -1 | awk '{print $7}'`   # 能量
T=`grep "Total CPU time" OUTCAR | awk '{print $6}'`             # CPU 时间
```

4. 画 **E–k间距** 与 **E–ENCUT** 曲线，取"曲线走平 + 时间可接受"的那一档。

### 28.3 测试用 INCAR 的共性

- `NSW=0` + `IBRION=-1`：**静态**计算；
- `ICHARG=2`：从原子密度叠加起步（测试够用且快）；
- `LWAVE=F` / `LCHARG=F`：省 I/O；
- `NELMIN=6`、`NELM=400`、`EDIFF=1E-8`：把电子步收紧，避免数值噪声干扰"是否收敛"的判断；
- `ALGO=VeryFast`：提速；**若能量噪声大就换 `ALGO=Normal`**；
- `ISMEAR=0` + `SIGMA=0.01`：适合原子/分子；**金属体系请按 `errors.md` §1.4 改成 `ISMEAR=1`**。

### 28.4 ⚠️ 直接拿来用之前要改的地方

- 脚本头是 **LSF（`#BSUB`）** 的写法，换 Slurm/PBS 要改提交段；
- `mpirun` 那一行是**绝对路径的 VASP**（`/gpfs/software/vasp/vasp.5.3-20181107`），改成自己的；
- `MAXEN_` **原文硬编码 300**——务必换成 `grep ENMAX POTCAR` 得到的真实最大值，或取消注释 `read` 手动输入。

- **相关**：`workflows.md` §一（优化前先定参数）、`errors.md` §1.4（ENCUT 与 ENMAX）、
  `references/performance.md`（ENCUT 是最大省时杠杆）。
- **来源文章**：`articles/20261001-自动进行K点和ENCUT测试bash脚本.md`（原文的代码块在网页上"行号+空行"渲染且**丢空格**，
  本库收集时已做最小修复并逐条列明，见 `scripts/reference/kpoint_encut_test.sh` 头部）。



### 28.5 不想扫参时怎么估 k 点密度（四种方法 + 三条例外）

**四种估法**（任选其一给出起点，**最后仍要做收敛性测试**）：

1. **按「长度 × k 点数」配平**（官网思路）：让三个方向的 **`晶格长度 × 该方向 k 点数` 大致相等**，
   即各方向的 k 点**密度一致**。例：绝缘体 `a = b = 6 Å`、`c = 15 Å`（真空层）→ 取 **`3 3 1`**。
   ⚠️ **这一招只对正交晶系成立**（此时正/倒格矢同向，倒格矢长度就是正格矢的倒数，所以 `1/(k·a)` 就是 k-spacing）。**非正交晶系不能用**：`a` 方向晶格矢量与对应的倒格矢并不同向，**晶格夹角越偏离 90°、`|k_a|` 越大**，用这种方法预判 k 点密度就越离谱。非正交体系请直接用第 3 种方法（VASPKIT）。
2. **用 Materials Studio 的 CASTEP Tools 看 k 点密度**：不同 k 点下看它的"密度"读数，
   **一般 `0.03` 附近最佳**；正交晶系里把晶格常数取模再取倒数，**三个倒数的比值**就是三个方向的 k 点分配。
   例：**fcc Cu → `7 7 7`**。
3. **非正交晶系**（倒格矢长度与实空间晶格常数**不成反比**，上面两法失效）→ 用 **VASPKIT**：

```bash
# 1 102 → 先选 1(M 点) 或 2(G 点) → 再输入倒格子中的 k 点间距（单位 Å⁻¹）
# 一般计算 0.04；精确计算 0.03 或 0.02
```

   这与本节前面说的 KP-resolved 档位（Low `0.08~0.05` / Medium `0.04~0.03` / Fine `0.02~0.01`）一致。
4. **简单粗暴**：**`晶格常数 × k 点数 ≈ 30~40`** 即可。但**别过分大**（撒点太密、白烧机时），
   也**别过分小**（计算不准）。

**三条例外/注意事项**（比估法更容易踩）：

- **真空层方向永远只取 1 个 k 点**（二维材料、表面体系）：那个方向本来就没有结构，
  多余的 k 点只会把"**周期性镜像之间的相互作用**"算得更准——**而那部分能量恰恰是我们不想要的**。
- **原子/分子体系**：一个 **Γ 点（`1 1 1`）**就够（绝大多数原子/分子计算这个文件不用改）；
  ⚠️ **但如果用 `ISMEAR=-5`（四面体法），必须把 `1 1 1` 改成 `2 2 2` 或 `3 3 3`**——
  k 点太少时四面体法不适用（见 `references/incar.md` 的 `ISMEAR` 条）。
- **六方晶系**：官方建议用 **Gamma centered**，M 点平移后网格对称性与晶胞不匹配、**可能导致计算出错**
  （本库三个独立来源一致，见 `errors.md` §8.20）。

**五行式 KPOINTS 的小脚本**（原文给的写法）：

```bash
echo K-POINTS >  KPOINTS      # ⚠️ 第一行必须是 >（覆盖）；原文用 >> 追加，
echo 0         >> KPOINTS     #    若 KPOINTS 已存在会写出重复内容
echo G         >> KPOINTS
echo $1 $1 $1  >> KPOINTS     # 用法：./kpoints.sh 5  → 5 5 5
echo 0 0 0     >> KPOINTS
```

> 更稳的做法：直接用本库的 `scripts/gen_inputs.py` 生成 `KPOINTS`（带 `--selftest`）。
> ⚠️ 另外提醒：**VASPKIT 生成 KPOINTS 时不会替你写 INCAR**，INCAR 必须自己准备
> （见 `workflows.md` §28.2 与 §27.3）。




---

## 二十九、杂化泛函能带（HSE06）

> 用途：PBE 低估带隙，**杂化泛函（HSE06）能给出接近实验的带隙**，但代价是**计算量比 PBE 高一个数量级**。
> 本节前半部分出自 **VASPKIT 开发者 Vei Wang** 的步骤说明（经公众号《学术之友》整理）。

### 29.1 VASPKIT 路线（推荐）

1. **准备 `POSCAR`**，用 **`vaspkit 303`（体相）/ `302`（二维）** 生成 **`KPATH.in`** 与 **`PRIMCELL.in`**：
   - 二维体系要检查 `PRIMCELL.in` 的**真空层是否沿 z 方向**，不是就用 **`vaspkit 923`** 或 **`407`** 强制；
   - 想改结构对称性的识别精度（`symprec` 默认 `1E-5`）：`vaspkit -task 302 -symprec 1E-6`。
2. ⚠️ **`cp PRIMCELL.vasp POSCAR` 之后再优化**：**`KPATH.in` 只针对原胞（primitive cell）**——
   少了这一步，能带路径与晶胞不匹配，**可能得到错误结果**。有必要时用在线工具 **SeeK-Path** 核对能带路径
   （比较 `KPATH.in`、`PRIMCELL.vasp` 与 `HIGH_SYMMETRY_POINTS`；**SeeK-Path 只支持体相结构**）。
3. 先用 **VASP-PBE 优化结构**（`cp CONTCAR POSCAR` 供下一步）。
4. （可选）**再用 HSE 优化一次结构**：严格来说 HSE 优化出的结构与 PBE 有差别，程度因体系而异
   （💡 经验上**先用 PBE 预优化再用 HSE 收尾**能显著减少 HSE 的离子步数，见 `errors.md` §3.1）。
5. **`vaspkit 251`** 生成能带计算用的 `KPOINTS`——它由**两部分**组成：
   - **第一部分**：不可约布里渊区中**权重非零**的 k 点 → 用于**自洽**，得到正确的**费米能**；
   - **第二部分**：**权重为 0** 的、沿特定路径的 k 点 → 用于**能带**。
6. 💡 **先用 PBE 跑一次并保存波函数**（这一步同时也能顺带得到 PBE 能带，与常规两步法等价）；
   ⚠️ **算完用 `vaspkit 252` 检查能带是否合理**再往下走。
7. **改 INCAR 的 HSE 参数，拿上一步的波函数再算一次**。
8. **`vaspkit 252`** 提取杂化泛函能带数据。

### 29.1b 社区的「两目录」做法（含 VASPKIT `251` 的交互过程）

> 另一篇教程给的是**可直接照做的目录组织**，与本节的 VASPKIT 路线互补：

1. **`scf/` 目录**：五行式 `KPOINTS` 做一次**纯泛函（PBE）自洽**，INCAR 里确保
   **`LCHARG=.TRUE.`、`LWAVE=.TRUE.`、`NSW=0`** → 留下 `CHGCAR`、`WAVECAR`。
2. **`hse/` 目录**：把 **`CHGCAR`、`WAVECAR`、`INCAR`、`POTCAR`、`POSCAR` 全部拷进来**。
3. 在 `hse/` 里跑 `vaspkit`：**`303`**（体相；二维用 `302`）生成含高对称点的 **`KPATH.in`** →
   **`251`**（*Generate KPOINTS for Hybrid Band-Structure Calculation*），然后按提示依次输入：
   - **①** 生成自洽用 k 网格的方法（`1`/`2`，本文选 **Gamma**）；
   - **②** **正常权重 K-Mesh 的 k 点密度**：一般 **`0.02~0.04`**；
   - **③** **0 权重 K-path 的 k 点密度**：**HSE 建议 `0.04~0.06`**。
   例：K-mesh 得 `3 3 3`，路径上 G→X 取 6 个点、X→M 取 6 个点……
4. 改 INCAR（见下），提交——**HSE 很慢（比 PBE 高一个量级甚至更多）**，等；**后处理取带隙与 PBE 完全相同**。

**HSE 的 INCAR 增量——两篇来源合起来看**（`2` 与 `5` 来自社区版，`1`/`3` 来自官方教程）：

```
LHFCALC  = .TRUE.      # 打开杂化
HFSCREEN = 0.2         # HSE06
AEXX     = 0.25        # 交换泛函混合系数
LMAXFOCK = 4           # HF 部分的 augmentation（社区常用值）
PRECFOCK = Fast        # HF 交换的 FFT 网格精度（想更准可提高）
ALGO     = Damped      # 或 ALGO = D
TIME     = 0.4
LDIAG    = .TRUE.
EDIFF    = 1.E-6
ISTART   = 1           # 读入上一步的 WAVECAR
ICHARG   = 1           # 由读入的波函数重算电荷密度
```

- ⚠️ **两个独立来源都强调同一件事**：HSE 这一步必须建立在**「纯泛函（PBE）算出来的 `WAVECAR`」**之上——
  社区流程的做法是"`scf/` 跑完把 `WAVECAR` 拷进 `hse/`"，官网的说法是"**用 DFT 的 `WAVECAR`，否则导带出现锯齿**"。
- 📌 评论区两个常见问题，本库已有答案：**"为什么 HSE 要用 PBE 的结构/自洽结果？"**——因为
  ① 波函数必须来自 DFT（见上）；② **先用 PBE 预优化再用 HSE 收尾能显著减少 HSE 离子步数**（`errors.md` §3.1），
  HSE 优化结构是可选项、与 PBE 差别通常很小；**"100 个原子的 HSE 要算多久？"**——按本节开头，
  计算量比 PBE 高**一个数量级以上**，先估机时再提交。

### 29.2 官方的「0-weight (fake) SC」做法（手写混合 KPOINTS）

VASP 官网 HSE 教程里给的另一条路（**DFT 与杂化都适用**，也是上面 251 的原理）：

1. 先做一个**标准 DFT** 自洽（例：`ISMEAR=0`、`SIGMA=0.01`、`6×6×6` 网格）；
2. 再做**杂化计算**，用一份**改造过的 `KPOINTS`**——**同一个文件里混着两类 k 点**：
   - 前面是**权重非零的 SC k 点**（真正参与自洽、定费米能），权重可以是 8、24 等；
   - 后面接**权重为 0 的路径 k 点**（`... 0.000`），只为取能带。
   对应 INCAR 关键项：

```
LHFCALC = .TRUE. ; HFSCREEN = 0.2 ; AEXX = 0.25
ALGO    = D      ; TIME = 0.4     ; LDIAG = .TRUE.
EDIFF   = 1.E-6
```

3. ⚠️⚠️ **这一步必须用「标准 DFT 跑出来的 `WAVECAR`」**（**不是** HSE 自己算出的波函数），
   否则**导带常出现锯齿（zig-zag）结构**——这是官方教程明确点出的坑。

### 29.3 与本库其它内容的关系

- **HSE 相关的报错**：`errors.md` §8.8（`ISMEAR=-2` + HSE 崩成 NaN）、§8.9（HSE 的 `BUG card`）；
- **HSE 优化慢 / 难收敛**：先 PBE 预优化（`errors.md` §3.1）；
- **`ALGO=D`（Damped）+ `TIME`** 的稳定化思路，见 `errors.md` §2.6；
- **能带路径工具**：VASPKIT（`302`/`303`，含二维）、SeeK-Path（仅体相）——见 `references/tools.md`；
- **从输出里提能带数据**（不用 VASPKIT 时）：见 §二十（`OUTCAR` 的 `band No.` 块）与 `scripts/reference/outcar_*.sh`。

- **来源文章**：`articles/20261001-VASP计算杂化能带详细步骤教程.md`（前半部分由 VASPKIT 开发者 Vei Wang 撰写，后半为 VASP 官网 HSE 教程转载；
  文末另附小木虫/科学网的三篇经典教程链接，已登记在 `references/tools.md` 六）。

### 29.4 第三条路线：四步（`opt` → `gamma-scf` → `hse-scf` → `band`）

前面 29.1/29.1b 是「一次杂化计算里混两类 k 点」（fake-SC）。另有一篇教程把步骤拆得更细、
更贴近"标准三步法"的直觉：

| 步 | 目的 | 关键点 |
| --- | --- | --- |
| **1 `opt`** | 得到能量最低的结构（`CONTCAR`） | 常规优化 |
| **2 `gamma-scf`** | **单点自洽，拿到 `WAVECAR`**（喂给下一步） | `NSW=0` 的静态自洽 |
| **3 `hse-scf`** | **杂化自洽**，拿到 HSE 的 `WAVECAR`/`CHGCAR` | 参数见 `references/incar.md` §二附 |
| **4 `band`** | **非自洽**取能带（沿高对称路径） | `ICHARG=11` + `LORBIT=10`，KPOINTS 由 VASPKIT `251` 生成 |

- **机时概念**：该文记录它的 `hse-scf` **用时 > 32 小时**（单体系）——再次印证 §29 开头"比 PBE 高一个数量级甚至更多"，
  **提交前先估机时**。
- **`251` 的路径精度怎么选**：**`0.03` 比较常用**；若能带曲线**不光滑（说明非零权重的 k 点不够）就降到 `0.02`**；
  目标是**非零权重的不可约 k 点数 ≈ 20 个左右**。
  （另有来源给的是"K-Mesh `0.02~0.04`、HSE 的 K-path `0.04~0.06`"——**两个作者的经验值不同**，
  以"曲线是否光滑 + 不可约 k 点够不够"为准。）
- **拿到数据之后**：`vaspkit 911` 可**粗略估带隙**；也可以自己写脚本；**p4vasp 读 `vasprun.xml` 导出 `.dat` 再画图**。
- **并行的 KPAR**：想加速可加 `KPAR`，取法有两种——`KPAR = NKPTS`，或**取总核数的一个公约数**
  （例：24 核用 `KPAR=6` → 每个 k 点分到 4 核）。与 `references/performance.md` §四 的结论一致。

> ⚠️⚠️ **这条路线最容易踩的坑（原文记录的真实报错）**：第 4 步若把 INCAR 里的
> **`ENCUT`、`EDIFF` 等改成与第 3 步不一致**，VASP 读上一步文件时会报/警告：
> **`CHGCAR` 维数不同、`WAVECAR` 的 cutoff 不同、力不正确**。
> **解法：把第 4 步 INCAR 的其它参数都保持与第 3 步相同，只加 `ICHARG=11` 与 `LORBIT=10`，
> 并设 `LWAVE=FALSE`（这一步不需要再输出波函数）。**
> 机理与 `errors.md` §8.14 同源：**`ENCUT` 决定 FFT 网格，改了它 `CHGCAR` 的维数就对不上**（详见 §8.24）。



### 29.5 VASPKIT 全流程的一条实操记录（含 `ALGO=ALL` 变体与并行规则）

> 同一位作者的另一篇（`articles/20261001-VASP_vaspkit_画_HSE06_能带图.md`，材料 **SrMoO₄**，
> 锆石族四方结构 `I4₁/a`）把每个 VASPKIT 命令**连参数一起写清楚**了，可直接照抄：

```bash
# 1) 结构弛豫
vaspkit 1 101 LR          # 生成结构弛豫用的 INCAR（LR = Lattice Relaxation）
vaspkit 1 102 2 0.03      # 生成 KPOINTS：2 = Gamma 方案；0.03 = k 点密度（Å⁻¹）
                          # ⚠️ 这一步会**同时生成 POTCAR**，不必另外生成

# 2) 能带（HSE06）
vaspkit 303               # 生成 KPATH.in（高对称路径）
vaspkit 251 2 0.04 0.06   # 2 = Gamma 方案；0.04 = 自洽 K-Mesh 密度；0.06 = 0 权重 K-path 密度

# 3) 画图
vaspkit 252 0             # 出图并导出数据
```

**这篇用的 HSE INCAR 与 29.2/29.4 略有不同**（同一批参数、不同写法，都可跑）：

```
LHFCALC  = .TRUE. ; AEXX = 0.25 ; HFSCREEN = 0.2
ALGO     = ALL            # 注意：这里用 ALL（等价 ALGO=58），不是 Damped
TIME     = 0.4
PRECFOCK = Fast
! NKRED  = 2              # 可选项：只在偶数 k 网格上算 HF（加速）
# HFLMAX = 4              # HF 截断（4d、6f）
# LDIAG  = .TRUE.         # 子空间对角化（默认就是 .TRUE.）
ICHARG   = 1              # 读入 WAVECAR 并重算电荷（与 29.4 的 ICHARG=11 不同，两者都有人用）
ISTART   = 1 ; LWAVE = .TRUE. ; LCHARG = .TRUE.
```

- ⚠️ **`NPAR` 与 `KPAR` 的约束**：**两者相乘需要是核数的整数倍**（与
  `references/performance.md` §四 的 `KPAR × NPAR × NCORE = 总核数` 一致，差值由 `NCORE` 吸收）。
  该文弛豫步用 `KPAR=4`、能带步用 `KPAR=6`。
- 💡 **中断后续算可能更快**：能带/HSE 这一步若**没算完就停了**，**在没删任何文件的前提下重新提交，
  第二次有时会比第一次快**（复用了已有的 `WAVECAR`/`CHGCAR`）。
- ⚠️⚠️ **`252` 画不出图，先查 `~/.vaspkit`**：必须把里面的
  **`PYTHON_BIN`（指向带 matplotlib 的 python）**与 **`PLOT_MATPLOTLIB .TRUE.`** 配好，
  否则 VASPKIT 出图这一步会失败。配好后 `vaspkit 252 0` 会生成：
  **`BAND.dat`、`REFORMATTED_BAND.dat`、`KLINES.dat`、`KLABELS`、`BAND_GAP`、`TDOS_EIG.dat`、`band.png`**
  （`BAND_GAP` 里直接写着带隙值，很省事）。官方示例（单层 MoS₂ 杂化）见
  <https://vaspkit.com/tutorials.html#example-single-layer-mos2-1>。
- **两步 vs 三步（作者自己的取舍说明）**：他那篇走的是「结构优化 → 能带计算」两步，
  **可以算，但精度不如「结构优化 → 静态自洽 → 能带」三步**，原因见
  `references/onboarding.md` §3.3（优化步留下的 `CHGCAR`/`WAVECAR` 对应的是**最后一步迭代**而不是优化后的结构）。



---

## 三十、DFT+U（Hubbard U）

> 用途：**强关联体系**（3d 过渡金属氧化物、4f 镧系、5f 锕系）用纯 GGA/PBE 常把 d/f 电子描述得过于离域，
> 加 **Hubbard U** 可修正定域化程度、改善带隙与磁矩。完整算例：
> `articles/20261001-VASP_vaspkit_Materials_Studio_DFT_U_画能带和DOS图.md`
> （**UO₂**，萤石型反铁磁绝缘体，`Fm-3m`，a = 5.468 Å）。

### 30.1 INCAR 里要写的六项

```
#+U
LDAU     = .TRUE.
LDAUTYPE = 2          # 默认就是 2
LMAXMIX  = 6          # ⚠️ f 轨道用 6；d 轨道用 4（默认 2 会出问题）
LDAUL    = 3  -1      # 按 POSCAR 元素顺序：3 = f 轨道加 U；-1 = 不加
LDAUU    = 3.70  0    # U 值（eV）；不加 U 的元素写 0
LDAUJ    = 0.40  0    # J 值（eV）；同上
```

| 参数 | 默认 | 含义与取值 |
| --- | --- | --- |
| `LDAU` | `.FALSE.` | 开关：是否启用 DFT+U |
| `LDAUTYPE` | **`2`** | `1` = Liechtenstein 旋转不变 DFT+U；**`2` = Dudarev 简化（旋转不变）**；`4` = 同 `1` 但**没有交换分裂** |
| `LMAXMIX` | `2` | **必须大于所加轨道的角量子数**：**d → `4`，f → `6`** |
| `LDAUL` | `NTYP*2` | **每个元素一个值**：`-1` 不加、`1` p、`2` d、`3` f |
| `LDAUU` | `NTYP*0.0` | **每个元素一个 U（eV）** |
| `LDAUJ` | `NTYP*0.0` | **每个元素一个 J（eV）** |

### 30.2 三个最容易错的地方

1. ⭐ **`LDAUL`/`LDAUU`/`LDAUJ` 是「一个元素一个值」，顺序必须与 POSCAR 的元素顺序一致**
   （与 POTCAR 拼接顺序同理）。UO₂ 只给 **U 的 5f** 加 U，所以 `LDAUL = 3 -1`；
   不给 O 加 U，对应位置就写 **`-1`**（`LDAUL`）与 **`0`**（`LDAUU`/`LDAUJ`）。
   **顺序写错不会报错，但结果全错**（见 `errors.md` §七）。
2. ⭐ **`LMAXMIX` 必须跟着轨道放大**：**d → `4`，f → `6`**（默认 `2`）。
3. **U 值不能随便设**：示例取自文献（U = `3.70 eV`、J = `0.40 eV`）——**U/J 要能追溯到文献，
   或用实验性质（如带隙）校准**（见 §30.5 最后一条）。

### 30.3 磁性设置（以反铁磁为例）

- 示例是**反铁磁** UO₂：**`MAGMOM = -1 1 -1 1 8*0`**——**用负号表示反平行的那些 U**；
- **U 是锕系元素、5f 未填满且有磁性 → 必须 `ISPIN = 2`**（这类体系别偷懒用 `ISPIN=1`）。
- 顺带：这就是"**带 +U 的体系一定要检查磁态**"的典型场景（见 `onboarding.md` §9.3 的磁矩检查）。

### 30.4 流程与数据提取

- **结构弛豫（+U）** → **非自洽（+U，能带 / DOS）**：
  非自洽目录里需要 `INCAR`、`POTCAR`、`POSCAR`（由 `CONTCAR` 复制）、**上一步的 `CHGCAR`**，外加提交脚本。
  ⚠️ 示例里 `ICHARG` **没有显式写**（用默认值）、也没拷 `WAVECAR`——**若发现费米能或能带与自洽步对不上，
  先检查是否真的读进了上一步的电荷密度**，必要时显式写 **`ICHARG = 1`**（读 `CHGCAR`）或 **`11`**（读并固定）。
- **能带路径**：`vaspkit → 3 → 303`（**三维结构**）生成 `KPATH.in` → 复制为 `KPOINTS`（二维用 `302`，见 §二十九）。
- **取能带数据**：`vaspkit → 21 → 211` → **`BAND.dat`**（可直接进 Origin；也可用 §29.5 的 `252` 自动出图）。
- **取 DOS**：`vaspkit → 11 → 111` → **`tdos.dat`**（总 DOS）。
- 💡 也可以用 Python 包 **`vaspvis`** 直接画能带/DOS 图（已登记在 `references/tools.md` 速查表）。

### 30.5 结果怎么分析（UO₂ 示例，可当模板）

- **先对带隙**：本次计算 **1.8676 eV**，文献 **1.95 eV**——**大致吻合**（+U 计算第一个该核对的就是它）；
- **态密度归属**：**价带 = U 5f + O 2p**；**导带 = U 6d + U 5f**；UO₂ 有**两个价带**——
  `-20 eV` 附近是 **U 6p + O 2s**，`-5 eV` 附近以 **O 2p** 为主外加少量 U 5f/6d；
- **成键判断**：**O 2p 与 U 5f/6d 的态密度出现共振 → 说明有成键**；**U 6d 带宽更宽 → 离域性更强 →
  O 2p–U 6d 成键更强**（"用 DOS 读成键"的标准套路，与 §十 COHP 可互相印证）；
- **尖锐的态密度峰**（示例里 `43.5~43.2 eV` 处的 U 6s）通常说明是**原子态轨道、尚未形成能带**；
- ⭐⭐ **最重要的方法论**：文献指出 **`U_eff` 会影响 U 5f 电子的分布；反过来，也可以用计算出的带隙宽度去修正
  `U_eff`**——即 **U 值不是一次性设定，而是可以（也应该）用实验数据校准**。

- **来源文章**：`articles/20261001-VASP_vaspkit_Materials_Studio_DFT_U_画能带和DOS图.md`（含 Materials Studio 建模步骤、`vaspkit` 命令序列与文献对比）。



---

## 三十一、铁电极化（Berry phase）与铁电性

> 用途：算**自发极化强度 `P`**（铁电体的核心量）、**Landau-Ginzburg 系数**与**居里温度 `Tc`**。
> 与 §二十三（波恩有效电荷，`LEPSILON`）不同：那一节算的是**极化对位移/电场的响应**，
> 这一节算的是**两个结构之间的极化差**。来源：`articles/20261001-VASP之铁电极化计算.md`（社区教程）。

### 31.1 极化强度：极化相 FE − 参考相 NP

思路：选**极化相 FE**（铁电相，`P ≠ 0`）与**参考相 NP**（中心对称相，`P = 0`），两相各算一次，
**`P = P(NP) − P(FE)`**。两相的 INCAR 基本一致：

```
SYSTEM  = FE            # 另一相改成 NP
ENCUT   = 600          # ⚠️ 极化计算建议用高精度
EDIFF   = 1E-6
IBRION  = -1 ; POTIM = 0.3 ; NSW = 0 ; EDIFFG = -5E-3
ISMEAR  = 0  ; SIGMA = 0.05
PREC    = Accurate
ISIF    = 2
LWAVE   = .FALSE. ; LCHARG = .FALSE. ; LREAL = .FALSE.
LCALCPOL = .TRUE.      # 打开铁电极化（Berry phase）计算
DIPOL    = 0.2 0.2 0.2 # 偶极修正的参考点：**不要设在原子上或迁移路径上**，放在真空层一侧/质心
IDIPOL   = 3           # 只沿 z（真空/极化）方向做偶极修正
# LDIPOL = .T. ⚠️⚠️ 不要这么写，见 31.2
```

**取结果**：

```bash
grep "Total electronic dipole momen" OUTCAR   # 电子部分 p[elc]
grep "Ionic dipole moment" OUTCAR             # 离子部分 p[ion]
```

**电子 + 离子 = 该相的极化**；再 **`NP − FE`** 得到极化强度 `P`，**注意单位换算**。

### 31.2 ⚠️ 两个必须知道的坑

1. ⚠️⚠️ **不要用 `LDIPOL=.TRUE.`**（社区在评论区给出的关键更正）：
   `LDIPOL=T` 时**默认 `IDIPOL=4`**，即让 VASP 按"偶极中心"自行判断一个**任意方向**的偶极，
   并在该周期方向上做偶极修正——**等价于在周期性方向上加了一个任意电场**，既容易出问题、又收敛很慢。
   **正确做法：显式给 `DIPOL` 与 `IDIPOL`（如 `IDIPOL=3`），而不要打开 `LDIPOL`。**
2. ⚠️ **单独一个相的偶极矩没有物理意义**：`p[ion]`/`p[elc]` 依赖原点选取、且只确定到"**极化量子**"的整数倍
   （见 §二十三）。所以**必须两相相减**（或按下面 31.3 的方法处理）；
   直接拿某一相的 `p[ion]`（如 `(-260.77, -5.44, -36.87) |e| Å`）去谈"极化方向"是没意义的
   （评论区里出现频率最高的问题就是这个）。
   - 顺带：原文表格里的单位换算写成 `eÅ = C/m`，**读者更正为 `eÅ = C·m`**（偶极矩的量纲是 电荷×长度）。

### 31.3 参考相不是半导体怎么办？（很常见）

1. **镜像法**：以 NP 为参照中心构造 **−FE 相**（极化方向与 FE 相反），
   用 **`(P(FE) − P(−FE)) / 2`** 得到极化强度（即"1 − (−1) = 2，再除以 2"）；
2. **线性插值法**：在 FE 与 NP 之间插一系列中间结构（0%(FE)、10%、20% … 100%(NP)），
   各自算极化后用 Origin 拟合，100% 处的值即 NP 相极化，两者之差就是 `P`。

### 31.4 Landau-Ginzburg 系数与居里温度

- **系数 A、B、C**：对**一系列原子位移**的结构（位移方式类似上面的线性插值）分别算极化，
  再用 L-G 公式**把极化与能量一起拟合**，得到前三项系数；
- **系数 D**：由 FE 原胞建 **4×4×1 超胞**算 `E1`；把其中**一个原胞换成 −FE**（相当于翻转一个偶极子）
  算 `E2`；按朗道有效哈密顿量的表达式比较 `E1`、`E2` 即得 `D`。
- **居里温度 `Tc` 的两种算法**：
  - **AIMD 法**（计算量大、更准）：不同温度下跑超胞 → 统计平均极化"距离" `d` → 换成该温度下的极化值
    → 用 **sigmoid（logistic）函数**拟合出 `Tc`；
  - **MC 法**（快，教程推荐）：用上面的 L-G 拟合，代码见 **`mpiPyMC`**
    （<https://github.com/Chengcheng-Xiao/mpiPyMC>，已登记到 `references/tools.md`）。

- **参考文献**：*Ferroelectricity and Phase Transitions in Monolayer Group-IV Monochalcogenides*,
  **PRL 117, 097601 (2016)**（原文所引，DOI `10.1103/PhysRevLett.117.097601`；涉及单层 IV 族单硫属化物的铁电相变）。



---

## 三十二、居里温度（`Tc`）计算

> ⚠️ **先说结论：VASP 本身不算温度**（一个高赞回答的原话）——它只给你**基态能量 / 磁矩 / 交换参数**，
> `Tc` 必须再走一步**统计模型**（蒙特卡洛或用能量差做平均场估计）。来源：知乎问答
> 《VASP 如何计算居里温度？》（`articles/20261001-VASP如何计算居里温度_-_知乎.md`，4 个回答）。

### 32.1 主路线：DFT 求交换参数 `J` → 蒙特卡洛求 `Tc`

**第一步：用 VASP 求近邻交换参数 `J`**（以 CrI₃ 为例，社区做法）：

1. 分别构建**铁磁基态超胞（FM）**与**反铁磁超胞（AFM）**；
2. 两者都**先做一次非磁性计算**，把 `WAVECAR`、`CHGCAR` 留下；
3. 再做**非共线磁性计算**（记得读上一步的 `WAVECAR`/`CHGCAR`）：

```
LNONCOLLINEAR = .TRUE.
ISPIN   = 2
MAGMOM  = 0 0 Z   0 0 Z   0 0 Z   0 0 Z     # 非共线：每个原子三个分量
LSORBIT = .TRUE.
LMAXMIX = 4                                  # 含 d 电子（f 电子用 6）；见 §三十
GGA_COMPAT = TRUE
```

4. 用能量差求 `J`：

$$J = \frac{H_{AFM} - H_{FM}}{2 \, X \, S^{2}}$$

其中 `X` 是**最近邻磁性原子个数**、`S` 是**磁矩**（**注意把磁矩换算成玻尔磁子，`S/2`**）。

**第二步：把 `J` 喂给蒙特卡洛程序**，扫描温度得到磁化强度/热容，再由**热容 `C` 或磁化率 `χ` 的峰值**
（或磁化强度趋于零的位置）定出 `Tc`：

$$C = \frac{\langle E^{2}\rangle - \langle E\rangle^{2}}{k_B T^{2}}, \qquad
\chi = \frac{\langle M^{2}\rangle - \langle M\rangle^{2}}{k_B T}$$

- 💡 **单位换算**：**`1 meV ≈ 11.6 K`**（原文写作 "1 meV = 11.xxx K"）——`J`、各向异性 `A/D` 都要先换算成 K；
- 💡 **扫描方向**：MC 模拟**建议从高温往低温降**，且每个温度点先跑一段"瞬态"再统计，
  否则低温下容易**卡在局域态**（某回答的实现里 `transient=5000`、`mcs=5000`）。

### 32.2 三个现成的蒙特卡洛工具

| 工具 | 出处 | 特点 |
| --- | --- | --- |
| **Mc solver** | 山东大学刘亮博士，<https://github.com/golddoushi/mcsolver> | 有代码端 + **可视化界面**；填晶格基矢、超胞大小、原子位置、**单离子各向异性 `DX/DY/DZ`**（一般 Z 轴就填 `DZ`）与 **Bond List**（`J` + 近邻连接）；可选 **XY / Ising / Heisenberg** 模型；**铁磁与反铁磁都能算**，上手快 |
| **MTC**（Multi-dimensional Curie Temperature Simulation） | 东南大学王金兰课题组，<https://physics.seu.edu.cn/jlwang_zh/mtc/list.htm> | 需**自行编译**；**直接读 VASP 的 `POSCAR` 并自动生成近邻表**，在 `INPUT` 里填参数提交，结果写进 `OUTCAR`；还能算磁滞回线；**说明书只讲了铁磁**。**引用**：*Comput. Mater. Sci.* **2021**, 197, 110638 |
| **公众号「计算凝聚态物理」的 Python MC 代码** | <https://mp.weixin.qq.com/s/owdAe-U53IzA89gbJUx9oQ> | 提供**三种模型**，以 CrI₃ 做过测试；**换成六角等其它晶格要自己改代码** |

**MTC 的 `INPUT` 长这样**（照抄自回答，可作模板）：

```
Method = Heisenberg      # Heisenberg or Ising
System = Loop            # Tc or Loop
Setting = Auto           # Auto or Set
[Lattice] Sample = 5 ; Lattice = 20 ; Temperature = 10 70 1
[Magnetic] % Cr  3
J = 0.002944
A = 0 0 0.000744 0 0 0
[Loop] LoopTemp = 10 ; LoopVector = 0 0 1 ; LoopRange = 3E-3 1E-4
[Stop]
Hfield = 0 0 0 ; TotalSteps = 300000 ; RelaxSteps = 100000 ; LogicCell = true
```

### 32.3 更省事的估计与它的偏差

- **平均场近似**（由 FM/AFM 能量差直接套公式）**能给出量级，但结果通常偏高**——问题本身就说"用平均场
  近似来算但是结果（偏高）"；**要发文章级数字，还是走 32.1 的 MC**。
- 体系简单时也可以**从 `J` 用量级估算**：`k_B T_c ~ z J S²`（`z` 为配位数）先判断"大概多少 K"，再决定 MC 的
  温度扫描区间——**扫描区间设错（比如 `Tc` 远高于 `T` 上限）是 MC 白跑一晚上的常见原因**。

### 32.4 其它

- 单层 / 二维磁体的 `Tc` 对**磁各向异性**极其敏感（Mermin-Wagner 定理：各向同性二维海森堡模型没有有限温
  长程序），所以 `DX/DY/DZ`（或 `A`）这一项**不能省**。
- 还有一个回答提到：**含 RPA 的 `U` 作为函数**去算 `Tc`（把 `U` 与 `Tc` 一起讨论）——
  这属于强关联 + 磁性的进阶做法，本库暂未展开。



---

## 三十三、自旋轨道耦合（SOC）与磁各向异性

> 用途：算**磁各向异性（MAE）**、拓扑/自旋电子学相关的能带（Rashba、反常霍尔等），或任何需要
> **磁矩方向有意义**的计算。来源：`articles/20261001-第一性原理_VASP计算自旋轨道耦合与相关参数.md`
> （内容基本是 VASP 手册 `LSORBIT`/`SAXIS` 条目的整理与翻译）。

### 33.1 开关与两个前提

- **`LSORBIT = .TRUE.`** 打开 SOC，**并会自动设置 `LNONCOLLINEAR = .TRUE.`**（非共线）；
- ⚠️ **`LSORBIT` 只对 PAW 赝势有效，对超软赝势（USPP）无效**——先确认自己的 `POTCAR` 是 PAW；
- **`SAXIS = sx sy sz`** 指定全局自旋量子化轴，**默认 `SAXIS = (0+, 0, 1)`**（`0+` 是 x 方向上一个
  无限小的正数）；
- ⭐ **VASP 读写的全部"磁矩/类自旋量"都以该轴为基准**：INCAR 里的 `MAGMOM`、`OUTCAR`/`PROCAR` 里的
  总磁化与局域磁化、`WAVECAR` 里的类自旋轨道、`CHGCAR` 里的磁化密度 **都是**。
- ⭐ **不开 SOC 时，能量不依赖磁矩方向**（把所有磁矩整体转一个角度，能量原则上完全相同）——
  **所以不做 SOC 就不必设 `SAXIS`**。

### 33.2 两种"指定磁矩方向"的写法

```
# 写法 A：方向写进 MAGMOM
MAGMOM = x y z          # 局域磁矩（三分量）
SAXIS  = 0 0 1          # 量子化轴沿 z

# 写法 B：方向交给 SAXIS（推荐）
MAGMOM = 0 0 total_magnetic_moment
SAXIS  = x y z          # 量子化轴沿 (x,y,z)
```

- 两者**原则上给出完全相同的能量，但写法 B 通常更精确**；
- 💡 **写法 B 还允许读取预先算好的 `WAVECAR`**（此前跑过共线或非共线都行），**以不同的自旋方向继续算**——
  这正是做 MAE 时最省机时的路子；**读入非共线 `WAVECAR` 时，自旋被假定与 `SAXIS` 平行**。

### 33.3 计算磁各向异性（MAE）的推荐流程

1. **先做一次共线计算**，得到 `WAVECAR` 与 `CHGCAR`；
2. 接着在新目录里加这些标签：

```
LSORBIT = .TRUE.
ICHARG  = 11            # 非自洽：读上一步的 CHGCAR
SAXIS   = x y z         # 想考察的磁化方向
NBANDS  = 共线计算的能带数 × 2      # ⚠️ SOC 下能带数要翻倍
LMAXMIX = 4             # ⚠️ 要在【共线那一步】就设好：d 区 4、f 区 6
```

3. VASP 会读 `WAVECAR`/`CHGCAR`，把自旋量子化轴对齐到 `SAXIS`（即磁矩与 `SAXIS` 平行）后做非自洽计算；
   **把不同方向的能量相减，就得到 MAE**（比如 `E(100) − E(001)`）。

- 注：**用完全自洽（`ICHARG=1`）原则上也可以**，但**自旋波函数从初始方向"转"到真正易轴的基态非常慢**
  （自旋重定向带来的能量收益很小）；**收敛标准不严时，全自洽也能给出合理结果**，但别指望它自动找到易轴。

### 33.4 三条必须注意的事（官方口吻）

1. ⚠️ **SOC 计算建议完全关掉对称性：`ISYM = -1`**——因为**k 点集会随自旋方向变化**，
   结果的可转移性变差；**更要紧的是：k 点数一变，`WAVECAR` 就无法被正确重读**（MAE 流程全靠重读）。
2. ⚠️ **SOC 的能量差极小**：MAE 常在 `μeV` 量级，**k 点收敛繁琐缓慢、机时不确定**——
   这也是 `workflows.md` §一 里"关注 `μeV` 量级性质时用 `LREAL=.FALSE.`"的原因。
3. **非共线计算建议 `GGA_COMPAT = .FALSE.`**（手册在 VASP 4.6 起给出，可提高 GGA 的数值精度）。

### 33.5 怎么确认 SOC 真的生效了

计算正常结束后，`OUTCAR` 里会出现 **`Spin-Orbit-Coupling matrix elements`** 块：

```
Ion:  1 E_soc:  -0.0984080
   l=  1  ...
   l=  2  ...
   l=  3  ...
```

- **`E_soc`**：在该离子（增强投影波球内、半径 R1 范围）**SOC 能量贡献的加和**；
- 后面按角动量 `l` 分组的是 **SOC 矩阵元**；
- 💡 **只要 `grep "E_soc" OUTCAR` 有输出**，就说明 SOC 部分真的在算（否则多半是赝势不支持或标签没生效）。



### 33.6 操作层面：必须用 `vasp_ncl`（含两个流程变体与四条常见问答）

> 另一篇 SOC 教程（`articles/20261001-VASP_SOC自旋轨道耦合效应的计算.md`）把"怎么跑"这件事写得更实在，
> 补进本节。

#### ① ⚠️⚠️ **SOC / 非共线计算必须用 `vasp_ncl` 可执行文件**

**`vasp_std`（普通版）不支持非共线/SOC**——**从你在 INCAR 里写下 `LSORBIT=.TRUE.` 的那一步开始，
提交脚本里就要把 `vasp_std` 换成 `vasp_ncl`**（"非线性版本/non-collinear version"）。
这一步没做，是"SOC 算了但结果像没开 SOC"的最常见原因（见下面问答 4）。
（`vasp_ncl` 的编译见编译指南文章；本库 §二十五 Wannier90 一节也提过 SOC 要改用 `vasp_ncl`。）

#### ② 两种流程变体（都对，按需选）

| | 变体 A（手册/官网式） | 变体 B（本篇教程式） |
| --- | --- | --- |
| 第一步 | **先做共线**（普通）结构优化 + 自洽，留 `WAVECAR`/`CHGCAR` | 结构优化（PBE，**先不开 SOC**）→ 静态自洽时**就打开 `LSORBIT`**，写出**非共线**的 `WAVECAR`/`CHGCAR`（`LWAVE=.TRUE.`、`LCHARG=.TRUE.`、`NSW=0`、`IBRION=-1`） |
| 第二步 | 加 `LSORBIT`/`SAXIS`/`NBANDS`×2，**`ICHARG=11`** 非自洽（读共线的 `WAVECAR`），比较各方向能量得 MAE | **`ISTART=1` + `ICHARG=11`**，接着算（此时已是非共线，换 `SAXIS` 可平滑切换方向） |
| 用哪个二进制 | 第二步起用 **`vasp_ncl`** | **第一步的静态自洽起就要用 `vasp_ncl`**（因为它已经开 SOC 了） |

> 🗣️ 评论区确实有人问"第二步就开始 `ncl` 计算吗"——**对，凡是 INCAR 里有 `LSORBIT` 的那一步就必须用 `vasp_ncl`**。

#### ③ `MAGMOM` 的非共线写法（原子多时别手写）

- **非共线时每个原子给 3 个数**（自旋的三个分量）：2 个 Fe、磁矩 3 都沿 z → **`MAGMOM = 0 0 3 0 0 3`**；
- **原子多时**（比如 100 原子的 slab）手写不现实：用**脚本生成**（本库 `scripts/gen_inputs.py -w mag --magmom "Fe:5,Mn:4"`
  能生成**共线**的磁矩串；非共线需要自己按"每原子 3 个数"拼，或用 `MAGMOM` 的重复语法 `n*value` 逐段拼）。
  **别靠肉眼数原子**——磁矩个数与原子数不符会直接报错（见 `errors.md` §2.5）。

#### ④ SOC 下遇到对称性报错的三条并行办法

1. **关掉对称性**：`ISYM = -1`（本库 §33.4 的官方建议）；
2. **收紧对称性判据**：**`SYMPREC = 1E-8`**（判据变严 → 程序不再把体系当成高对称，从而避开
   "对称性相关的报错"；与 `errors.md` §8.2 里"放宽 `SYMPREC` 来解决识别问题"的做法**方向相反**，
   取决于你遇到的到底是哪类问题）；
3. **调整 `ISYM` 的取值**（如 `ISYM=0`），或干脆调整磁构型。

#### ⑤ 四条常见问答（评论区高频，本库给出答案）

1. **"`LSORBIT` 要在结构优化的时候就加吗？我加了感觉好慢。"**
   —— **一般不必**：SOC 的能量效应小，但会让每步都变慢。**常见做法是先做 PBE 结构优化，只在静态/MAE 这一步开 SOC**
   （§33.3 的官网流程就是"先共线、后非自洽"，本篇教程也是"先优化、静态自洽时才开"）。
2. **"算完怎么没看到各轨道对磁矩的贡献？"**
   —— 加上 **`LORBIT = 11`**（投影到各原子各轨道；`≥10` 不需要 `RWIGS`），SOC 下还会给出各方向的贡献。
3. **"非线性的提交脚本能给一份吗？"**
   —— 不需要特别的脚本，**把提交脚本里的可执行文件名 `vasp_std` 改成 `vasp_ncl`** 即可（其余不变）。
4. **"我换了不同磁态，能量却完全一样？"**
   —— **第一嫌疑是 SOC 根本没生效**：**没跑 `vasp_ncl`**，或赝势不是 PAW（`LSORBIT` 对超软赝势无效）。
   原理上，**不开 SOC 时能量本来就不依赖磁矩方向**（§33.1）；用 **`grep "E_soc" OUTCAR`** 验证是否真的在算（§33.5）。

> ⚠️ **一处原文表述偏松，提醒一下**：该文把 `ISPIN = 2` 与 `LSORBIT` 并列为"共同控制计算的参数"——
> **严格说 `LSORBIT=.TRUE.` 会自动打开 `LNONCOLLINEAR=.TRUE.`**（`ISPIN=2` 写上无害，但不是必需项）；
> 评论区也有读者指出了这点。以 §33.1 的官方口径为准。



### 33.7 `SAXIS` 的角度与旋转：为什么"写法 B"更值得用

> 另一篇非共线磁性总结（`articles/20261001-VASP中的非线性磁性计算总结.md`）是 VASP 手册
> `LNONCOLLINEAR`/`LSORBIT`/`SAXIS` 三页的翻译，本节只补**库里原先没有的数学细节**与两处易忽略的规则。

#### ① 四个先明确的概念

- **饱和磁化强度**：外磁场下自旋方向趋于一致时达到的最大磁化强度；
- **磁各向异性能（MAE）**：**饱和磁化强度矢量取不同方向时能量的差**；
- **易磁化轴**：这些方向中**能量最低**的那个；
- **`SAXIS`**：全局自旋量子化轴——**改它就等于"整体转磁矩"**（下面看到为什么）。

#### ② `SAXIS` 对应的两个旋转角

若 `SAXIS = (sx, sy, sz)`，则

$$\alpha = \arctan\frac{s_y}{s_x} \qquad \beta = \arctan\frac{\sqrt{s_x^2+s_y^2}}{s_z}$$

`α` 是 `SAXIS` 与 **x 轴**的夹角、`β` 是 `SAXIS` 与 **z 轴**的夹角。**默认 `SAXIS=(0⁺,0,1)` 时两角都为零**——
这正是"写法 A（把方向写进 `MAGMOM`）"能生效的原因。

#### ③ 两种"转向"在数学上的区别（这是本节的关键）

把 `MAGMOM` 里给的 `M^axis` 按上面的两个角做两次旋转，就得到实际用于计算的磁矩 `M`：

- **写法 A：`SAXIS = 0 0 1` + `MAGMOM = x y z`**
  `α = β = 0` → **`MAGMOM` 里写的就是实际方向**（每个原子可以各不相同——真正的非共线）；
- **写法 B：`MAGMOM = 0 0 TOTAL_M` + `SAXIS = x y z`**
  旋转变换后所有磁矩都**与 `SAXIS` 平行**，方向完全由 `SAXIS` 控制。
  ⭐ **换句话说：写法 B 算的其实仍是"共线"情形（所有自旋平行），只是通过 `SAXIS` 让整体的空间指向任意可调**——
  而**磁各向异性能本身就是比较"取向不同、但各自内部共线"的能量**，所以**做 MAE 时写法 B 更有优势**
  （更精确、还能复用已算好的 `WAVECAR`）。

> 💡 附带一条实现细节：**读取非共线 `WAVECAR` 时，VASP 假定自旋与 `SAXIS` 平行**，
> 因此**刚读入时它报告的磁矩只出现在 z 方向**——这不是算错了。

#### ④ 两条容易被忽略的规则

1. ⚠️ **`MAGMOM` 并不总是生效**：**只有当 `ICHARG = 2`（原子密度叠加起步）、
   或者 `CHGCAR` 里只含电荷而不含磁化密度时，`MAGMOM` 才作为"初始磁矩"被使用**。
   所以"改了 `MAGMOM` 结果一点没变"往往不是错觉（详见 `references/incar.md` 的 `MAGMOM` 行）。
2. ⚠️ **非共线计算不能在"选定的原子上"局部旋转磁矩**：VASP 可以读入以前**非磁性或共线**计算留下的
   `WAVECAR`/`CHGCAR`，但**不能只把某几个原子的磁矩单独转过一个角度**。官方因此推荐**两步走**：
   1. **先算非磁性基态**，生成 `WAVECAR` 与 `CHGCAR`；
   2. **再读入这两个文件**，并用 `MAGMOM` 给出初始磁矩（**非共线时每个离子给 3 个分量**，
      如 `MAGMOM = 1 0 0 0 1 0` 表示"第 1 个原子磁矩沿 x、第 2 个沿 y"）。
   这比"先共线优化再转非共线"更贴合手册的推荐（MAE 那边用"先共线"是因为要复用共线 `WAVECAR`，
   见 §33.3 与 §33.6 的两种变体——**两者输入文件不同，别混**）。



### 33.8 磁矩单位、`m` 与 `s` 的泡利矩阵视角，以及一套可直接用的 MAE 参数

> 出自另一篇 MAE 文章 `articles/20261001-vasp_磁各向异性计算.md`。
> ⚠️ **来源可信度提示**：该文作者在评论区**自述"磁性计算我不擅长，相关评论都没有回复，怕误导人"**——
> 所以本库把它主要当作**参数示例**收录，**其中的结论性说法请以官方手册为准**（下面凡有存疑处都已标注）。

#### ① 磁矩的单位（初学者最容易含糊的地方）

- 单个电子的自旋磁矩 `μ_s = −g·μ_B·S`（朗德因子 `g ≈ 2`、自旋角动量 `S = 1/2`）→ **一个电子约贡献 `1 μ_B`**；
- **VASP 里磁矩的单位就是玻尔磁子 `μ_B`**；
- ⭐ **共线情形下，VASP 给出的磁矩 = 自旋向上与向下的电子数之差**（单位 `μ_B`）；
- ⭐ **去哪里看**：`OUTCAR` 里 **`number of electron`** 那一行后面的 **`magnetization`** 值，
  就是**原胞内积分得到的总磁化**（每次迭代都会更新）。

#### ② `m` 与 `s`：为什么 `MAGMOM = 0 0 m` 不表示"指向 z"

非共线的自旋方向由两个向量决定：**`m`**（各原子磁矩，写在 `MAGMOM` 里）与 **`s`**（即 `SAXIS`）。手册的写法是：

$$\hat\sigma_3 = \frac{\mathbf{s}}{|\mathbf{s}|}, \qquad
\mathbf{m} = m_1\hat\sigma_1 + m_2\hat\sigma_2 + m_3\hat\sigma_3$$

即**`MAGMOM` 给的是磁矩在"以 `ŝ` 为第三轴的基"下的分量**，而不是笛卡尔分量。于是：

- **写法 A：固定 `SAXIS = 0 0 1`** → `σ̂₃ = ẑ`，三个基矢量就是 `x̂, ŷ, ẑ` → **`MAGMOM` 里的三个数
  就是笛卡尔分量**（每个原子可各自不同）；
- **写法 B：`MAGMOM = (0, 0, m₃)`** → `m = m₃·σ̂₃`，**方向与 `SAXIS` 相同**——
  ⚠️ **注意：这不意味着磁矩指向 `ẑ`！** 举例：`MAGMOM = 0 0 m₃` 配 **`SAXIS = 0 1 1`**，
  则**磁矩的方向是笛卡尔坐标下的 `(0,1,1)` 方向**。
- 手册**推荐写法 B**（与 §33.2、§33.7 的结论一致，这里给的是更本质的解释）。

#### ③ 一套可直接抄的 MAE 参数（两步）

**第 2 步：共线静态自洽**（产出 `WAVECAR`/`CHGCAR`）

```
ISTART = 0                # 从零开始
ICHARG = 2                # 原子密度叠加起步
PREC   = Accurate
ISMEAR = -5               # 静态总能/磁性：四面体法
LREAL  = .FALSE.          # 准确基态所必需
ISYM   = -1               # 关掉全部对称性（见下方说明）
ISPIN  = 2
MAGMOM = 4*5 8*0          # 按体系改（共线：每原子一个数）
LMAXMIX = 4               # d 区 4、f 区 6
LORBMOM = .TRUE.          # ⭐ 输出【轨道磁矩】——MAE 里常常要它
```

**第 3 步：非共线 + SOC**（读上一步文件，换方向比能量）

```
ICHARG = 11               # 非自洽：读 CHGCAR
PREC   = Accurate
ISMEAR = -5
LREAL  = .FALSE.
ISYM   = -1               # 官网建议；见下方"一处争议"
NBANDS = 128              # = 共线那一步的 2 倍：grep NBANDS ../collinear/OUTCAR
LNONCOLLINEAR = .TRUE.
ISPIN  = 2
LSORBIT = .TRUE.
LMAXMIX = 4
LORBMOM = .TRUE.
MAGMOM = 0 0 5  0 0 5  0 0 5  0 0 5  24*0   # ⭐ 每原子3个数 与 n*0 可以混写
SAXIS  = 0 1 1            # 想考察的磁化方向
GGA_COMPAT = .FALSE.      # 做磁各向异性时重要
LWAVE = .FALSE. ; LCHARG = .FALSE.

# 需要时再加（混合）：
# AMIX=0.2  BMIX=0.00001  AMIX_MAG=0.8  BMIX_MAG=0.00001
# 需要时再加（+U）：
# LDAU=.TRUE. LDAUTYPE=2 LDAUL=2 -1 LDAUU=5.00 0.00 LDAUJ=0.00 0.00
# LDAUPRINT=1  LMAXMIX=4
```

- ⭐ **`MAGMOM` 的混写语法很有用**：既写"每原子 3 个数"，又用 `24*0` 这种重复语法批量补零——
  **这正是"原子多时怎么办"的实用答案**（见 §33.6 的问答 ③）。
- ⭐ **`NBANDS` 怎么取**：先 `grep NBANDS ../collinear/OUTCAR` 看共线步的能带数，**再乘 2**。
- ⭐ **`LORBMOM = .TRUE.`**：输出**轨道磁矩**；研究 MAE 的轨道贡献时要用（默认不输出）。
- 这套参数里还出现了 `AMIX_MAG=0.8`、`BMIX_MAG=0.00001`，与 `errors.md` §2.6 里
  "`AMIX_MAG=0.8`/`BMIX_MAG=0.0001`"是同一路的磁性混合设置（**尾数量级会因体系而异，需实测**）。

#### ④ 关于 K 点（原文只给了一句英文转述，观点不完整）

> 原文：**简单磁结构**用 **Monkhorst-Pack** 采样可能就够了；**复杂磁构型、或对磁相互作用精度要求高**时，
> **Γ 点方法**可能更合适（采样围绕 Γ 点），"对捕捉正确磁行为可能重要……"

- ⚠️ 这段是**英文段落的转述且以省略号结尾**，**结论不完整**，本库如实记录、不做延伸；
- 📌 但请注意它**说的不是"k 点要多密"**，而是"**用 MP 还是 Γ-centered 网格**"——两者不要混为一谈
  （MAE 的收敛性测试仍要按 `workflows.md` §二十八 做，且**MAE 常在 `μeV` 量级、对 k 点极敏感**）。

#### ⑤ 一处评论区争议的澄清

有读者问："**官网推荐非共线计算用 `ISYM=-1`，这条我在哪里能找到？**"

- 这条**确有出处**：VASP 手册 **`LSORBIT`** 页明确写着"**我们建议完全关闭对称性（`ISYM=-1`）**"，
  本库 §33.4 就是那页的译文（`articles/20261001-第一性原理_VASP计算自旋轨道耦合与相关参数.md`）；
- 作者自己也补了一句："测试 `ISYM=0` 对结果似乎无影响，可能和体系相关，安全起见用 `-1`"——
  **与 §33.4 的官方表述一致**（关对称性是为了避免 k 点集随方向变化、以及 `WAVECAR` 无法重读）。

#### ⑥ 本篇评论区留下的未决问题（本库给出可用思路，标注为"通用做法"）

1. **"算完在哪里查看单轴各向异性常数？"**（未答）——**通用做法**：算若干个磁化方向的能量
   （如 `SAXIS` 取 `001`、`100`、`110`…），再按
   `E(θ) = K₀ + K₁sin²θ + K₂sin⁴θ` 拟合出 `K₁`、`K₂`（单轴情形 `MAE = K₁` 量级，单位换算见 `constants.md`）；
   只要 `E(θ)` 曲线在手，各向异性常数是拟合出来的，**没有一个"自动输出 K"的命令**。
2. **"VASPKIT 能算磁各向异性吗？"**（未答）——**本库暂无验证过的结论，不做推断**。
3. **"导入电荷密度计算时 `OUTCAR` 内容不全、像是没算上？"**（未答）——
   先按 `errors.md` §8.24 排查：**`ENCUT`/`EDIFF` 是否与上一步一致**（不一致会导致 `CHGCAR` 维数不匹配、
   计算早早退出），再看任务是否正常结束。



---

## 三十四、约束磁矩（`I_CONSTRAINED_M`）

> 用途：**`MAGMOM` 只给"初值"**，自洽过程中磁矩会往能量更低的方向跑——如果你想**强制**体系处于某个
> 磁构型（自旋向上/向下、面内/面外、或某个非共线方向），就要**约束磁矩**。
> 典型场景：**判断易磁化方向**、做**四态映射（4-state mapping）**以提取各向异性 `J`、DMI、单离子各向异性。
> 来源：本人文章 `articles/20261001-如何在_VASP_中约束磁矩.md`（译自 Tharindu 的英文博客
> <http://thauwa.me/2023/12/08/how-to-constrain-magnetic-moments-in-vasp/>）。

### 34.1 前提：**必须在非共线框架里做**

- 用 **`vasp_ncl`** 可执行文件（不是 `vasp_std`）；
- 打开 **`LNONCOLLINEAR = .TRUE.`**；需要 SOC 时再开 **`LSORBIT = .TRUE.`**
  （**非共线时不要再指望 `ISPIN=2`**，见 §33.1）；
- ⭐ **即使你只想约束"共线"的自旋（±1），也仍然要走非共线设置**——这是本方法最反直觉的一点；
- **`MAGMOM` 按非共线给**：**每个离子三个数**（笛卡尔向量），例如两个离子要 `(1,2,0)` 与 `(3,1,1)`：

```
MAGMOM = 1 2 0   3 1 1
```

**快速判断各向异性方向**时可以只改 `MAGMOM` 的方向（每离子三元组）：

```
x 面内：MAGMOM = 1 0 0   1 0 0   1 0 0
y 面内：MAGMOM = 0 1 0   0 1 0   0 1 0
z 面内：MAGMOM = 0 0 1   0 0 1   0 0 1
45°（xy 面内）：MAGMOM = 0.707107 0.707107 0   ...（三个离子都这样写）
```

### 34.2 三个开关与参数块

| `I_CONSTRAINED_M` | 约束什么 |
| --- | --- |
| **`1`** | **只约束方向**（大小可变） |
| **`2`** | **约束大小 + 方向** |
| **`4`** | **约束方向 + 符号**（⚠️ **至少需要 VASP 6.4.0**） |

- ⚠️ **作者经验：`I_CONSTRAINED_M=1` 分不清"同一直线上的正反向"**（`0 0 1` 与 `0 0 -1` 视为一样）；
  **要区分符号就用 `=4`**。

一个完整例子（Nb₃Cl₈，三个 Nb 沿 x、其余 24 个 Cl 不加约束）：

```
I_CONSTRAINED_M = 4
RWIGS  = 1.270 1.111        # Nb、Cl（按 POSCAR 元素顺序）
LAMBDA = 9
MAGMOM = 1 0 0  1 0 0  1 0 0  24*0
M_CONSTR = 1 0 0  1 0 0  1 0 0  24*0
```

- ⭐ **`M_CONSTR`（目标）与 `MAGMOM`（初值）应设成完全相同**——作者的实践经验是**这一点对拿到想要的结果很重要**；
- 💡 **`24*0` 这类重复语法**可以用（不然要手写 8 遍 `0 0 0`）；
- **`M_CONSTR` 的格式与 `MAGMOM` 一致**（每离子三元组）。

### 34.3 `RWIGS` 与 `LAMBDA` 都要做收敛测试

- **`RWIGS`**（Wigner-Seitz 半径，Å）：手册给了确定最佳值的建议（对非单原子体系无法唯一定义），但很耗时。
  **实用起点：直接用 `POTCAR` 里给的值**——`grep -e RWIGS POTCAR`，输出的那行形如
  `RWIGS = 2.400; RWIGS = 1.270 wigner-seitz radius (au A)`，**两个数分别是 a.u. 与 Å**；
  也可以改用文献里的**原子共价半径**（注意不同来源数值不同）。**最终判据是"算出来的结果有意义"**。
- **`LAMBDA`**：它是**加到体系上的能量惩罚**。手册要求**逐步增大 `LAMBDA`，直到惩罚项对能量的贡献变得很小**。
- ⭐⭐ **惩罚项 `E_p` 在哪里、怎么用**：
  - **在 `OSZICAR` 文件末尾的最后一块**，形如
    `E_p = 0.36856E-07  lambda = 0.500E+02  <lVp>= 0.30680E-02  DBL = -0.30680E-02`，
    后面还列出每个离子的 `MW_int` 与 `M_int`；
  - ⚠️⚠️ **实际 DFT 总能 = `OUTCAR` 里的能量（如 `energy(sigma->0)`）减去 `E_p`**——
    因为 **`OUTCAR` 的能量已经包含了惩罚项**（原文作者说明：手册里没找到明文，但**用不同 `LAMBDA` 的简单测试验证过**）。
    **报能量（尤其做能量差比较）时忘了减 `E_p`，会得到系统性偏差。**
- **`LAMBDA` 的扫描流程**（作者习惯）：先粗后细
  `[0, 1, 10, 25, 50, 75, 100, 125, 150]` → 发现**过高会出错**就缩范围 →
  `[1,10,25]` → `[1,3,5,7,10,13,15,17,20]` → `[4,…,12]` …… 直到**`E_p` 足够小、且最终磁矩方向正确**。
- **工作流策略**：**先用 POTCAR 的 `RWIGS` 去测 `LAMBDA` → 再用最佳 `LAMBDA` 反过来微调 `RWIGS`**，
  并**始终检查"积分磁矩"是否符合预期**。

### 34.4 怎么验证约束真的生效了

- **打开 `LORBIT = 11`**，然后在 `OUTCAR` 里看 **`magnetization (x)` / `(y)` / `(z)`**
  （每个离子的 `s`/`p`/`d`/`tot` 分解）；
- 这些数**应与 INCAR 里 `MAGMOM`/`M_CONSTR` 一致**；
- ⚠️ **若没约束大小（`I_CONSTRAINED_M=1`），幅度可以不同**；**用 `=2` 时最终大小才应接近设定值**；
- **物理自洽检查（例子）**：Nb₃Cl₈ 里预期"三个 Nb 共享一个半自旋"→ 每个 Nb 应约 `(1/2)/3 ≈ 0.17`；
  作者算到 `0.217`，**通过减小 `RWIGS`（积分区域变小、不重叠）可以让它更接近 0.17**——
  ⚠️ 但作者也提醒"**小心使用这条规律**"，因为 `OSZICAR` 里还有 `M_int`/`MW_int` 等参数参与。

### 34.5 收敛困难时的两个实用招

1. ⭐ **借非极化电荷密度起步**：**先做一次 `ISPIN = 1` 的非极化计算，然后用它的 `CHGCAR` 配
   `ICHARG = 1` 继续**——作者发现这样**对收敛、速度与精度都有帮助**；
   ⚠️ **前提**：先确认那次非极化计算在 `OUTCAR` 里**识别出的对称性符合预期**。
2. **换个思路找解**：约束磁矩的收敛是公认的"棘手问题"，社区有大量零散经验；
   连 VASP 手册某页都把 **「祈祷（prayer）」** 列为一种潜在解决方法（原文引用了这条，算是苦中作乐）。

### 34.6 用脚本生成 `MAGMOM`/`M_CONSTR`（大体系别手写）

大体系（例：Nb₃Cl₈ 的 4×4 超胞 = 48 个 Nb + 128 个 Cl）手写磁矩串**既麻烦又容易错**，原文给了一段脚本：

```python
def generate_string(a, b, c, n1, n2, n3):
    result = []
    result.extend(a * n1)
    result.extend(b * n2)
    result.extend(c * n3)
    return "M_CONSTR = " + " ".join(map(str, result)) + " 384*0"   # Cl 的 128*3 = 384 是写死的

n1 = 3; n2 = 3; n3 = 42          # 各段的离子数
a = [1, 0, 0]; b = [-1, 0, 0]; c = [0, 1, 0]   # 各段的目标磁矩
print(generate_string(a, b, c, n1, n2, n3))
```

- 💡 思路很省事：**把"每离子三元组"当成列表拼接**，再在末尾补上不需要约束那些离子的 `n*0`；
- ⚠️ **注意它的脆弱处**：末尾的 `384*0` 与各段离子数都是**硬编码**，**没有校验总数是否等于原子总数**
  （写错不会报错，只会静默算错）——用之前自己数一遍，或把总数做成参数并断言。



---

## 三十五、磁性设置总纲（`ISPIN` / `MAGMOM` / 初值策略）

> 用途：**做任何磁性计算前先看这一节**——把"要不要给初始磁矩、给多少、给错了会怎样"讲清楚。
> 来源：本人文章 `articles/20261001-VASP中的磁性设置.md`（含一个 O₄ 的完整实例与一组时间实测）。

### 35.1 先把名词对齐

| 磁有序 | 净磁矩 | 变成顺磁的临界温度 |
| --- | --- | --- |
| **铁磁（FM）** | 有（磁矩同向、同大小） | **居里温度 `T_C`** |
| **亚铁磁** | 有（两种离子反向、大小不同） | **居里温度 `T_C`** |
| **反铁磁（AFM）** | **无**（反向、同大小） | **奈尔温度 `T_N`** |
| 顺磁 | 无（无场时无序） | — |

- **居里定律**（顺磁）：`M = C·B/T`（磁化强度与磁场成正比、与温度成反比）；
- **居里-韦斯定律**（`T > T_C` 时的修正）：`χ = C/(T − T_C)`；
- 求 `T_C` 的计算方法见 **§三十二**（DFT 求 `J` + 蒙特卡洛）。

### 35.2 要不要给初始磁矩？

- **简单磁性材料**：只要 **`ISPIN = 2`**，**不必写 `MAGMOM`**；
- **复杂磁性体系**：`ISPIN = 2` **加上** `MAGMOM`；
- ⭐ **注意默认行为**：**只设 `ISPIN=2` 时，VASP 会给每个原子默认加上磁矩 `1`**——
  所以"没写 `MAGMOM`"并不等于"从 0 开始"，对磁性较弱的体系这有可能是**过头**的初值。

### 35.3 三条初值规则（都很实用）

1. ⭐ **把初值设得略大于预期**：**用实验/文献磁矩 × `1.2` ~ `1.5`**——这样更容易收敛到期望的磁基态；
2. ⭐⭐ **最终磁态很大程度上由 `MAGMOM` 初值决定**——**即使关掉对称性（`ISYM=-1`）也一样**，
   因为**自旋密度泛函的交换关联泛函有很多局部极小**。
   ⇒ 这不是"设不设"的问题，而是**你必须显式选择要考察哪个磁态**，算完**必须核对磁矩**（`onboarding.md` §9.3）；
3. **`MAGMOM` 不要求精确**：知道确切磁矩就写，不知道就按物理假设猜一个（例如 O₂ 每个 O 写 `1`）。

### 35.4 `MAGMOM` 的三种写法

```
# ① 按 POSCAR 原子顺序逐个数
MAGMOM = m1 m2 m3 m4 ...

# ② 重复语法（n 个原子的磁矩都是 m）
MAGMOM = 4*5  8*0

# ③ 长串换行：INCAR 里可以用反斜杠 \ 续行（大体系、非共线时尤其需要）
MAGMOM = 3.0 2.0 1.0 \
        -3.0 -2.0 -1.0 \
         3.0 2.0 1.0 \
         ... \
         24*0.0
```

- 💡 **写法 ③（反斜杠续行）**在官方文档里是允许的，**长磁矩串不必挤在一行**；
- **非共线时每原子 3 个数**（见 §33.1/§34.1），所以长串更常见。

### 35.5 一个实例（O₄ 板状体系）

**INCAR 的关键行**：`ISPIN=2`、**`MAGMOM = 1.5 1.5 1.5 1.5`**、`ISMEAR=0`、`SIGMA=0.05`、
**`LORBIT=11`**、**`NEDOS=2001`**、`NELM=60`、**`EDIFF=1E-08`**（KPOINTS 用 Gamma 网格、k-spacing `0.020`）。

**算完在 `OUTCAR` 里核对每个原子的磁矩**（`s`/`p`/`d`/`tot` 分解）：

```
# of ion    s       p       d       tot
   1     0.010   0.803   0.000   0.814
   2     0.010   0.803   0.000   0.814
   ...
 tot     0.042   3.213   0.000   3.255
```

- **O₂ 为什么初值可以写 1**：O₂ 有 12 个价电子，两个 `π*` 反键轨道上按**洪特规则**
  填了两个**自旋平行**的单电子 → **O₂ 基态是三重态、呈顺磁性** → 每个 O 写约 `1` 是合理的起点。

### 35.6 ⭐ "先算非磁基态再续算磁性"到底省不省时间？（附实测）

手册里有一句常被引用的话：

> *"If you have problems converging to a desired magnetic solution, try to calculate first the
> non-magnetic ground state and continue from the generated WAVECAR and CHGCAR."*

**注意它的前提是"converging problems（收敛困难）"，不是"为了省时间"。** 原文给了一组实测（同一体系）：

| 做法 | 磁性那一步 | 非磁起步那一步 | **总计** |
| --- | --- | --- | --- |
| 直接做磁性 | **629.2 s** | — | **629.2 s** |
| 先非磁、再读 `WAVECAR`/`CHGCAR` 做磁性 | **487.0 s**（变快了） | **284.0 s** | **771.0 s** |

- **磁矩收敛结果完全一样**（两种做法的 `OUTCAR` 磁矩表一致）；
- ⭐ **结论：非磁起步只是把"磁性那一步"的耗时降下来了，算总账反而多花了 ~22.5%**。
  ⇒ **它应当作为"磁性收敛困难时的救命手段"，而不是常规的加速技巧**；
  真要省时间，还是回到 `performance.md` 的那些手段（降 `ENCUT`、`KPAR`/`NPAR`、分步优化等）。
- 📌 顺带一条同类经验（来自 §33.7/§34.5）：**非共线/约束磁矩**里"先非磁再续算"同样常见，
  但理由不同——那里是为了**给一个干净的初始电荷密度**。



---

## 三十六、光学性质（介电函数 / 吸收谱）

> 用途：算**频率相关的介电函数**，进而得到**吸收系数、折射率、反射率、消光系数、能量损失谱**。
> 来源：社区教程 `articles/20261001-VASP_的光学性质计算及_vaspkit_的安装与使用.md`（2017 年，VASPKIT 0.51 时代）。

### 36.1 流程与 INCAR

**结构优化 → 静态自洽（scf）→ 光学**；光学这一步通常直接**从 scf 目录拷贝一份**再改 INCAR：

```bash
cp -rf scf optic      # 在 optic/ 里改 INCAR
```

关键 INCAR（★ = 光学特有）：

```
ISTART = 0 ; ENCUT = 350 ; EDIFF = 1E-5 ; PREC = Accurate
IBRION = -1 ; NSW = 0 ; ISIF = 2          # 静态单点
ISMEAR = 0 ; SIGMA = 0.05
ISYM   = 0                                 # 关对称性
NPAR   = 1                                 # ★ 光学计算常把并行调小（示例从 4 改成 1）
LREAL  = Auto
NBANDS = <原值 × 2>                        # ★ 见下
LOPTICS = .TRUE.                           # ★ 打开光学（频率相关介电矩阵）
```

- ⭐ **`NBANDS` 要取原来的 2 倍**：先 `grep NBANDS OUTCAR` 看 scf 步的能带数，再乘 2 填进去
  （光学要覆盖更高的跃迁能，空带不够会**截断高能端**）；
- 想覆盖**更高的跃迁能量**，就把 `NBANDS` 再加大——**VASP 没有"只算某个波段"的输入**，
  输出的能量范围由可达跃迁决定，**需要哪一段在出图时截取**即可。

### 36.2 结果在 `OUTCAR` 里，注意它的物理前提

计算完成后 `OUTCAR` 里会出现两段：

```
frequency dependent IMAGINARY DIELECTRIC FUNCTION (independent particle, no local field effects)  E(ev)  X  Y  Z  XY  YZ  ZX
frequency dependent REAL     DIELECTRIC FUNCTION (independent particle, no local field effects)  E(ev)  X  Y  Z  XY  YZ  ZX
```

- ⚠️⚠️ **括号里那句是前提**：**独立粒子近似（independent particle）+ 无局域场效应（no local field effects）**——
  它**不含激子、不含局域场修正**，所以与实验、BSE 计算、或某些商业软件的结果**在量级和峰位上本来就可能不同**；
- **六列的含义**：`X`/`Y`/`Z` 是介电张量的**对角分量**（三个晶轴方向）；`XY`/`YZ`/`ZX` 是**非对角分量**
  （用于光学各向异性/二色性分析，**画吸收谱一般用对角分量**）。

### 36.3 用 VASPKIT 后处理（含版本差异）

**老版本（0.5x）的流程**：先 `opt` 生成 **`REAL.IN` / `IMAG.IN`**（介电函数实部/虚部的两列数据），
再 `kit` 进菜单选 **`51) Linear Optics`**，得到：

| 产物 | 含义 |
| --- | --- |
| `ABSORB.dat` | 吸收系数 |
| `REFRACTIVE.dat` | 折射系数 |
| `REFLECTIVITY.dat` | 反射率 |
| `EXTINCTION.dat` | 消光系数 |
| `ENERGYLOSSSPECTRUM.dat` | 能量损失函数 |

进 Origin 作图即可。

- ⚠️ **版本差异（很重要）**：**新版 VASPKIT 会直接从 VASP 的输出/INCAR 读取并处理**
  （运行时会显示 `Reading Input Parameters From INCAR File...`），**不再需要手工准备 `REAL.IN`/`IMAG.IN`**；
  菜单编号也做了调整——**1.x 版本里光学在 `711`，产物是 `ABSORPTION.dat`**（见 §36.7，
  该文件同样给出 `XX,YY,ZZ,XY,YZ,XZ` 六列）。**跨版本使用时以本机菜单为准**
  （`references/tools.md` §4.1 记了几条现代版本的常用命令）。
- 💡 `REAL.IN`/`IMAG.IN` 本质就是**"能量 + 各分量"的文本表**——自己从 `OUTCAR` 抽出来写也可以
  （老版本的 `examples/optic/optics.sh` 干的就是这件事）。

### 36.4 VASPKIT 的安装（历史流程，仍可参考）

```bash
tar -zvxf vaspkit.*.tar.gz
cd vaspkit.*/src
# 按机器环境修改 Makefile
make
```

- ⚠️ **VASP 4.x 用户**要设 `src/module.f90` 里的 **`vasp5 = .false.`**——
  因为 5.x 与 4.x 的 `POSCAR`/`CONTCAR`/`CHGCAR` 格式略有不同；
- 便捷别名（写进 `~/.bashrc` 后 `source`）：

```bash
alias kit="~/software/vaspkit.0.51/src/vaspkit"
alias opt="~/software/vaspkit.0.51/examples/optic/optics.sh"
```

### 36.5 画图时该选哪一列、结果差几倍怎么办

**选列**：

- **各向同性 / 立方体系**：`X = Y = Z`，**任取一列**即可（也可取 `(X+Y+Z)/3` 作平均）；
- **各向异性体系**：**按方向分别画**（或选与你关心的物理量对应的那个方向）；
  **二维材料通常要分开讲"面内（x/y）"与"面外（z）"**。

**结果与文献对不上（差 5~10 倍、峰位也偏）——本库整理的排查清单**（按"从方法到设置"的顺序）：

1. **方法差异（最常见）**：`LOPTICS` 是**独立粒子、无局域场**；文献/商业软件可能含**局域场效应、激子（BSE）、
   或用了剪刀操作**——**量级差几倍并不罕见**，先确认对方用的是什么方法；
2. **k 点不够密**：光学谱对 k 点极其敏感，**k 点稀会让峰位偏移、峰形失真**；
3. **`NBANDS` 不够**：高能端被截断（见 §36.1）；
4. **展宽**：`LOPTICS` 常配 **`CSHIFT`**（复数位移，控制谱线平滑度）——另一篇教程用的是 **`CSHIFT = 0.1`**（见 §36.7）；展宽不同，峰高可以差很多；
5. **二维材料的"归一化"**：报**介电函数**还是**二维极化率**、体积用**含真空的晶胞**还是**有效体积**，
   都会显著改变数值——**和文献比之前先对齐这一条**。
   📌 本库另有一篇专门讲这个坑的文章（`articles/20260930-二维材料静态介电常数和光学性质计算Tips.md`）：
   **把 3D 的静态介电常数/光学性质定义直接套到 2D 材料上，"不是 well-defined 的物理量"**——
   多数课题组会忽略真空层效应，**对比文献时务必先确认对方怎么处理的**；
6. **其它**：泛函（PBE vs HSE）、是否含 SOC、是否做了 scissor 修正等。

> 💡 结论：**"差几倍"不等于算错**，但**必须找到差异来源**；把这 6 条逐项排除，比反复重算有效得多。

### 36.6 两个相关问题的答案

- **静态介电常数怎么算？** `LOPTICS` 给出的**实部在 `E → 0` 的极限**就是**电子贡献 `ε∞`**；
  若要**含离子贡献的静态介电常数**（以及波恩有效电荷、压电常数），用 **`LEPSILON = .TRUE.`（DFPT）**——
  见 §二十三。**两者不是一回事：`LOPTICS` 只给电子部分。**
- **算介电常数要加外电场吗？** **不需要**：`LOPTICS` 本身就是**零场下的线性响应**。
  想研究"外加电场下的响应"那是另一套技术（有限场/`EFIELD` 等），**不要混用在同一个流程里**。

- **参考**：VASP wiki `LOPTICS` 页、wiki 的 "Dielectric properties of SiC" 例子、
  以及 [ResearchGate 上关于 VASP 算吸收谱的讨论](https://www.researchgate.net/post/How_can_we_calculate_the_absorption_spectra_by_vasp)。



### 36.7 另一篇教程的增量：`CSHIFT` / `NEDOS` / `ALGO=Exact` / 泛函选择 / 现代 VASPKIT `711`

> 出自 `articles/20261001-VASP计算光学性质.md`（作者重复了 **InSe** 的光学性质，
> 对照文献 *Sci. Technol.* **2017**, 7, 2744）。

**它的 INCAR（InSe 实例，可直接对照）**：

```
SYSTEM = InSe
ISTART = 0 ; PREC = Accurate ; ENCUT = 500 ; GGA = PE
NSW = 1 ; ISIF = 3 ; ISYM = 2 ; IBRION = 2
EDIFF = 1E-05 ; EDIFFG = -1E-2
ALGO = Normal ; LREAL = .FALSE. ; LPLANE = .TRUE.
ISMEAR = 0 ; SIGMA = 0.02 ; ICHARG = 2
LWAVE = .F. ; LCHARG = .F.
LOPTICS = TRUE          # 开启光学
NEDOS = 2000            # ★ 光学里它控制"频率网格"的密度（不是 DOS 那个）
CSHIFT = 0.1            # ★ 复数位移（谱线展宽）
NBANDS = 120            # ★ 光学需要很多空带，以覆盖更多跃迁
```

**五条增量**：

1. ⭐ **`CSHIFT` 有了明确取值**：**`CSHIFT = 0.1`**——它就是**介电函数虚部里的那个"复数位移"**，
   决定谱线的**展宽/平滑**（所以 §36.5 第 4 条中"本库补充"的标注已更正为有来源）；
2. ⭐ **`NEDOS` 在光学里控制频率网格密度**（示例 `2000`）——名字与 DOS 里的一样，但作用在这里是"把谱画细"；
3. ⭐ **`NBANDS` 的量级感**：`InSe` 直接给了 **`120`**——**光学需要大量空带**以覆盖更多跃迁可能；
   实践中先用 `grep NBANDS OUTCAR` 的 2 倍起步，再按需要的能量上限加大；
4. ⭐⭐ **`ALGO` 的官方推荐与实测代价**：官网对光学推荐 **`ALGO = Exact`**，但作者实测
   **"几乎算不动"（太慢）** → 建议**先用较低精度起步、逐步提高**。
   （这也解释了为什么 LOPTICS 用 `ALGO=Normal` 起步的人很多——**先把流程跑通，再为精度付时间**。）
5. ⭐⭐ **光学对泛函精度要求极高，一般改用 HSE**：
   **光子把电子从价带激发到导带，谱形对"带隙"极其敏感**，而 PBE 低估带隙 ⇒
   **要发表级别的光学谱，通常用 HSE 杂化泛函**（流程与坑见 §二十九）。
   - 📌 因此 §36.5 的排查清单第 1、6 条里"泛函差异"往往**不是细节，而是主因**。

**流程上的一处实测对照**（与 §36.1 的做法不同，但结论是"差别很小"）：

- **§36.1 的做法**：先做 scf，再**另拷一个 `optic/` 目录**、改 INCAR 后重算；
- **本篇的做法**：**直接在静态自洽的 INCAR 里就加上光学参数**，一次算完；
- 作者用 PBE 对比过：**两者差别很小**，所以**直接在 SCF 里加光学参数是可行的**；
  若你更在意"scf 的干净程度"（例如还要拿同一份 `WAVECAR`/`CHGCAR` 做别的），那就仍然分两步走。

**现代 VASPKIT 的光学命令（1.x 版本）**：

```
vaspkit → 711        # 线性光学
# 产物：ABSORPTION.dat 等，同样给出 XX,YY,ZZ,XY,YZ,XZ 六列
```

- 选列规则与 §36.5 相同（各向同性取任一列/平均；各向异性分方向；非对角留作各向异性分析）；
- 💡 评论区问"用哪一列"的问题在两篇教程下都出现过——**这是这条路线上的高频困惑**，故 §36.5 与本节都写了。

- **来源文章**：`articles/20261001-VASP计算光学性质.md`（公众号《计算物理》，2022-11-05）。



### 36.8 三步标准流程、量化要求，以及 ⚠️ VASPKIT 对低维材料的警告

> 出自 `articles/20261001-vasp计算光学性质教程.md`（作者 **贺勇**，公众号《学术之友》转载，
> 原文个人博客 <https://yh-phys.github.io>；例子是**二维 InSe**）。这是本库收录的三篇光学文章里
> **流程最规范**的一篇（结构优化 → 静态自洽 → 光学，三步各自的 KPOINTS 都给了）。

**三步的 KPOINTS 与要点**（以二维 InSe 为例，`Gamma` 网格 `n×n×1`）：

| 步 | KPOINTS | INCAR 关键项 |
| --- | --- | --- |
| ① 结构优化 | `13 13 1` | `NSW=200`、`ISIF=3`、**另放一个 `OPTCELL` 文件固定 z 方向**（内容 `100110000`，见 `errors.md` §4.7） |
| ② 静态自洽 | **`25 25 1`**（≈ ① 的 **2 倍**） | `NSW=0`、`ISIF=2`、`IBRION=-1`、`ICHARG=2`、**`LWAVE/LCHARG=.TRUE.`**（要留下文件） |
| ③ 光学 | **`29 29 1`**（再加密） | **`ISTART=1`**、**`ICHARG=11`**、`LWAVE/LCHARG=.FALSE.`、**`LOPTICS=.TRUE.`**、`NBANDS=72`、`NEDOS=2000`、**`CSHIFT=0.1`** |

- ② 的 k 网格**约取 ① 的两倍**（"自洽要求有密的 k 网格"）；
- ③ 需要 ② 留下的 **`WAVECAR` 与 `CHGCAR`**（所以那一步必须打开 `LWAVE`/`LCHARG`）。

⭐⭐ **量化要求（本篇最有价值的一句）**：

> 光学（介电函数）计算**需要足够多的空带和致密的 k 网格**才能收敛：
> **`NBANDS` 一般取自洽步默认值的 `2~3` 倍**（去自洽的 `OUTCAR` 里 `grep NBANDS` 拿默认值），
> **k 网格取自洽值或适当增加**。

（这比"×2"更完整：**空带与 k 点要一起加**；前面两篇给的 `NBANDS=120`、`NBANDS=72` 也都落在这个区间。）

**三步 INCAR 里还出现了一批本库此前没记的参数**（都可用默认值，知道含义即可）：

| 参数 | 文中取值 | 作用 |
| --- | --- | --- |
| `NWRITE` | `2` | `OUTCAR` 的输出详细程度 |
| `NBLOCK` / `KBLOCK` | `1` / `1` | 输出与内部处理的块大小（一般不用改） |
| `LSCALU` | `.FALSE.` | 并行时是否做 LAPACK 缩放（大体系常设 `.FALSE.`） |
| `NSIM` | `4` | 每个 band 同时优化的数目（见 §二附6） |
| `LDIAG` | `.TRUE.` | 子空间对角化 |
| `ICORELEVEL` | `1` | 输出芯能级信息 |

**数据处理：`vaspkit 71 → 711`**

- **VASPKIT 1.0 及以上不需要再手工准备 `REAL.IN`/`IMAG.IN`**——**直接跑 `711` 即可**
  （老流程是用 `optics.sh` 里的 `awk` 从 `vasprun.xml` 抽 `<real>`/`<imag>` 段生成那两个文件；
  本库已把该脚本收进 `scripts/reference/optics_extract_awk.sh`）；
- `71) Optical-Properties` 下面的档位：**`711` 线性光学谱**、`712` 单 k 点跃迁偶极矩、
  `713` 能带上的跃迁偶极矩、**`716` 总联合态密度（JDOS）**、**`717` 分波 JDOS**；
- 运行时会让你选能量单位：**`1) eV / 2) nm / 3) THz`**；
- 产物（与前面两篇一致，另外**明确给了单位**）：
  `ABSORB.dat`（**吸收系数，单位 `cm⁻¹`**，列名即 `#energy xx(cm^-1) yy(cm^-1) zz(cm^-1) xy(cm^-1) yz(cm^-1) zx(cm^-1)`）、
  `ENERGYLOSSSPECTRUM.dat`、`EXTINCTION.dat`、`REFLECTIVITY.dat`、`REFRACTIVE.dat`；
- 数据实际是**从 `vasprun.xml` 抽出来的**（不是只从 `OUTCAR`）。

⚠️⚠️ **必须指出的一处矛盾（本库注）**：`vaspkit 711` 运行时自己会打印一句 Warm Tips：

> *"See an example in `vaspkit/examples/Si_bse_optical`. **This module is NOT suitable for
> low-dimensional materials.**"*

——**而本篇教程恰好用二维 InSe 做例子**。也就是说：**软件作者明确提示"线性光学模块不适用于低维材料"，
但二维体系的教程仍在用它**。本库的立场是**把矛盾如实记录**，并给出判断依据：

- 库里另一篇更早的文章（`articles/20260930-二维材料静态介电常数和光学性质计算Tips.md`）已经指出：
  **把 3D 的介电常数/光学性质定义直接套到 2D 材料上"不是 well-defined 的物理量"**；
- 本篇前言也给了 **2D 光学性质的理论公式出处：`DOI: 10.1021/acsnano.9b06698`**（以及 VASPKIT 论文
  **arXiv:1908.08269**）；
- ⇒ **做二维材料的光学性质时，先想清楚"你要报的是 3D 介电函数还是 2D 极化率/电导率"**；
  若沿用 `vaspkit 711` 的 3D 输出，**至少要在文中说明这一点**（这也是 §36.5 排查清单第 5 条"归一化"
  更本质的版本）。

- **引用提示**：使用 VASPKIT 的光学功能时，按原作者要求应引用 **VASPKIT 论文（arXiv:1908.08269）**。

**附：`optics.sh` 里的抽取脚本（本库已收进参考脚本库）**

```bash
# extract imaginary and real parts of dielectric function from vasprun.xml
awk 'BEGIN{i=1} /<imag>/,/<\/imag>/ {a[i]=$2;b[i]=$3;c[i]=$4;d[i]=$5;e[i]=$6;f[i]=$7;g[i]=$8; i=i+1}
     END{for (j=12;j<i-3;j++) print a[j],b[j],c[j],d[j],e[j],f[j],g[j]}' vasprun.xml > IMAG.in
awk 'BEGIN{i=1} /<real>/,/<\/real>/ {a[i]=$2;b[i]=$3;c[i]=$4;d[i]=$5;e[i]=$6;f[i]=$7;g[i]=$8; i=i+1}
     END{for (j=12;j<i-3;j++) print a[j],b[j],c[j],d[j],e[j],f[j],g[j]}' vasprun.xml > REAL.in
```



### 36.9 ⭐ 低维材料的正确档位：`710`（2D）与 `711`（3D），以及几个默认值公式

> 出自本人文章 `articles/20261001-VASP_vaspkit_光学性质_1.md`（同样以**二维 InSe**为例，
> **参考的正是 §36.8 那篇贺勇博客** <https://yh-phys.github.io/2019/10/12/vasp-optics/>）。
> 这篇**解决了 §36.8 里那个"VASPKIT 说 711 不适用于低维材料，教程却用它算二维"的矛盾**。

#### ① `vaspkit 71` 下面的两条分支（关键）

```
vaspkit → 71 → 710 → 选能量单位     # ★ 二维/低维材料走这条
vaspkit → 71 → 711 → 选能量单位     # 三维块体材料的线性光学
```

- **`710` = 二维材料的光学性质**，输出的是**带 `_2D` 后缀**的一套文件：

| 产物 | 含义 |
| --- | --- |
| **`ABSORPTION_2D.dat`** | 光吸收系数 |
| `IMAG_OPTICAL_CONDUCTIVITY_2D.dat` | 光学电导率虚部 |
| `real_OPTICAL_CONDUCTIVITY_2D.dat` | 光学电导率实部 |
| `REFLECTION_2D.dat` / `TRANSMISSION_2D.dat` | 反射 / 透射系数 |
| `IMAG.in` / `real.in` | 复介电函数的虚部 / 实部 |

- ⇒ **§36.8 那句 “This module is NOT suitable for low-dimensional materials” 说的正是 `711`**：
  **低维材料应该改用 `710`**，不要再"明知不适合还沿用 3D 输出"；
- （作者为**与参考文献逐项对齐**，也做过一次 `711` 的对照计算，见下面的未决现象。）

#### ② 几个默认值（此前库里只写了"默认 0.1"这类半截话）

- ⭐ **`NBANDS` 默认值**：**`max(NELECT/2 + NIONS/2, NELECT*0.6)`**；
  含义是"KS/QP 轨道的总数"；**最小要求是"所有占据态 + 一个空带"**，否则 VASP 会警告；
  光学计算则按 §36.8 的规则取**自洽步默认值的 2~3 倍**；
- ⭐ **`CSHIFT` 默认值**：**线性响应 `0.1`**；**GW 计算为 `OMEGAMAX×1.3 / max(NOMEGA,40)`**；
  作用是在**线性响应的 Kramers-Kronig 变换**与 **GW 的 Hilbert 变换**里设置那个**（小）复位移 η**。
  → 所以前面两篇写 `CSHIFT = 0.1` 并不是"某个人的经验值"，**它就是线性响应的默认值**；
- `LOPTICS` 默认 `.FALSE.`；打开后**在电子基态确定之后**计算频率相关的介电矩阵。

#### ③ 第三个 InSe 三步实例（参数可直接对照）

| 步 | KPOINTS（KPT-resolved `0.020` + Gamma） | INCAR 关键项 |
| --- | --- | --- |
| ① 结构优化 | **`15 15 3`** | `ISPIN=1`、`ENCUT=500`、`PREC=Normal`、`ISMEAR=0`、`SIGMA=0.02`、`NSW=100`、`IBRION=2`、`ISIF=2` |
| ② 静态自洽 | **`25 25 3`** | `NSW=0`、**`LWAVE/LCHARG=.TRUE.`**（留文件） |
| ③ 光学 | **`30 30 3`** | **`ISTART=1`、`ICHARG=11`**、`LOPTICS=.TRUE.`、**`NBANDS=96`**、`NEDOS=2000`、**`CSHIFT=0.1`** |

- 处理用 **VASPKIT 1.2.4**；吸收峰出现在 **3.7871 eV 与 4.0992 eV**（二维 InSe，可作参考数据点）。

#### ④ ⚠️ `OPTCELL` 的前提：**必须改源码并重新编译 VASP**

- §36.8 说二维材料的优化要"另放一个 `OPTCELL` 固定 z 方向"——**但这里有个前提**：
  **`OPTCELL` 是配合修改过的 `constr_cell_relax.F` 使用的，必须重新编译 VASP 才生效**；
  **没有重新编译的 VASP 不需要也无法准备这个文件**（作者就没用）。
- 想固定真空层厚度而不优化它，就必须走"改源码 + 重编译"这条路；
  博文（刘锦程）：<https://blog.shishiruqi.com//2019/05/05/constr/>
  （与 `errors.md` §4.7 里记的 <http://blog.wangruixing.cn/2019/05/05/constr/> 是同一篇的**两个域名**）。

#### ⑤ ⚠️ 一个**未决**现象：二维材料的吸收谱在"带隙以下"仍有吸收

作者的原始困惑：**"为什么结果在材料带隙以下还有吸收系数？我参考的那篇教程里没有。"**
他给出的**归因**是"**我把真空层的厚度也一起优化了**"；但他随后做了对照：
**把各步输入文件全部改成与贺勇博客一致（唯一差别是没有 `OPTCELL`）、并改用 `711`**——
**带隙之下依然有吸收谱**。

- ⇒ 本库的处理：**如实记为"未决"**——现象可复现，但作者的归因**未被自己的对照实验证实**；
  若你遇到同样现象，可优先排查的方向（**本库列的方向，非结论**）：
  ① 真空层是否参与了优化（有无 `OPTCELL`/固定基矢）；
  ② **是否误用了 `711` 而应为 `710`**；
  ③ 带隙本身是否被低估（PBE）或体系是否出现带隙内态（缺陷/表面态/SOC）；
  ④ 展宽 `CSHIFT` 是否把吸收边"抹"到了带隙以下。



### 36.10 ⚠️ 适用范围与"五个导出量"的公式（理论篇）

> 出自本人文章 `articles/20261001-VASP_vaspkit_光学性质_2.md`（光学系列第 2 篇）。
> 这篇把**介电函数到各种光谱的换算公式**和**二维材料的正确物理量**都写清楚了；
> 理论来源：<https://doi.org/10.1016/j.cpc.2021.108033>（Computer Physics Communications）。

#### ① ⚠️⚠️ 先记住适用范围：**该方法不适用于金属**

> **VASP 计算介电函数时只考虑了带间直接跃迁（interband direct transitions），
> 因此只适用于半导体或绝缘体，不适用金属体系。**

- 金属里主导的是**带内（intraband/Drude）**贡献，`LOPTICS` 的这套做法**不包含**它；
  给金属算"介电函数"会得到物理意义不明的结果（低频端尤其）；
- 这条与 §36.2 里 `OUTCAR` 那句 `independent particle, no local field effects` 是**两件事**：
  那一句说的是"不含局域场/激子"，这一条说的是"不含带内跃迁、金属不适用"。

#### ② 五个导出量的公式（`ε₁`、`ε₂` → 各种光谱）

有了介电函数 `ε(ω) = ε₁(ω) + iε₂(ω)`（虚部按单电子图景对**所有 `v→c` 直接跃迁**求和，
实部由 **Kramers-Kronig 关系**给出——式中的主值 `P` 与**复平移参数 `η`** 正是 `CSHIFT` 的物理含义），
其余量都是它的代数组合：

| 量 | 公式 |
| --- | --- |
| 折射率 | `n(ω) = [ (√(ε₁²+ε₂²) + ε₁) / 2 ]^(1/2)` |
| 消光系数 | `k(ω) = [ (√(ε₁²+ε₂²) − ε₁) / 2 ]^(1/2)` |
| **吸收系数** | **`α(ω) = (√2·ω/c) · [ (√(ε₁²+ε₂²) − ε₁) ]^(1/2)`** |
| 能量损失函数 | `L(ω) = Im(−1/ε) = ε₂/(ε₁²+ε₂²)` |
| 反射率 | `R(ω) = [(n−1)² + k²] / [(n+1)² + k²]` |

- 💡 这也解释了 `ABSORB.dat` 等文件的**单位**：`α` 里带 `ω/c` ⇒ **`cm⁻¹`**（§36.8 已记）；
- 💡 只有 `ε₁`、`ε₂` 是"原始输出"，其余五个（`n`、`k`、`α`、`L`、`R`）都是推出来的——
  所以**自己用脚本从 `REAL.in`/`IMAG.in` 算这五个量是完全可行的**（不必依赖 VASPKIT）。

#### ③ ⭐⭐ 二维材料：为什么"介电函数"不合适，该报什么

原文把这件事从原理上讲透了：

- 用"**层间距 `L` 足够大的周期堆叠**"来模拟二维体系（避免周期镜像相互作用）时，
  **介电函数不是直接的（不 well-defined）**：厚度 `L` 取多少会影响数值；
  ⇒ 因此**折射率、消光系数、吸收系数、能量损失函数、反射率这五个公式对低维材料"并不明确"**。
  （这就从理论上解释了 §36.8 里 VASPKIT 那句 "NOT suitable for low-dimensional materials"，
  以及 §36.9 为什么要改用 `710`。）
- ⭐ **正确做法：改用二维光学电导率 `σ_2D(ω)`** 来表征 2D 片层，它与三维量通过**层厚度**直接相关：

```
σ_3D(ω) = i[1 − ε(ω)]·ε₀·ω
σ_2D(ω) = L · σ_3D(ω)          # L 是模拟单元中的层厚度
```

- 法向入射时，**归一化反射率 `R`、透射率 `T`、吸光度 `A` 与偏振无关**（`σ̃ = σ_2D/(ε₀c)`）：

| 量 | 公式 |
| --- | --- |
| 反射率 | `R = \| (σ̃/2)/(1 + σ̃/2) \|²` |
| 透射率 | `T = 1 / \| 1 + σ̃/2 \|²` |
| 吸光度 | `A = Re σ̃ / \| 1 + σ̃/2 \|²` |

- 三者满足 **`A + T + R = 1`**（只考虑带间贡献时，对半导体/绝缘体的 2D 晶体成立）；
- ⭐ **常用近似**：**2D 片层的反射率非常小，于是 `A(ω) ≈ Re σ_2D(ω)/(ε₀c)`**；
- 单位约定：光学电导率图常用 **`σ₀ = e²/(4ħ)`** 作单位（VASPKIT 输出的 `*_OPTICAL_CONDUCTIVITY_2D.dat`
  纵轴就是 `σ_2D/σ₀`，见 §36.11 的绘图脚本）；
- 文献校验：文中**石墨烯与磷烯单层**的 PBE 线性谱与已有理论曲线一致（磷烯还区分了
  **扶手椅/锯齿两个偏振方向**的实线/虚线）。

#### ④ 方法层级：DFT(`LOPTICS`) → GW → GW-BSE

原文以**硅**为例说明了为什么要往上走：

- **Si 是间接带隙**，所以**吸收系数要到 ~`3.0 eV` 之后才显著**（可见光区吸收很低）——
  这是"用基态 DFT 算光学"和实验对不上的典型来源之一；
- **GW**：在**多体准粒子**框架里用自能项（依赖单粒子格林函数 `G` 与动态屏蔽库仑作用 `W`）
  **修正 DFT 的单电子本征值**；`G₀W₀` 表示 `G` 只做**一次**自洽更新、`W` 固定在初值；
- **BSE**：把"确定 `W` 时缺少**梯形图（ladder diagrams）**"带来的误差用
  **Bethe-Salpeter 方程**概括进去（即计入电子-空穴相互作用/激子效应）；
- ⇒ **GW-BSE 的光学谱与实验一致性更好**。所以：**PBE 的 `LOPTICS` 适合快速定性/趋势判断，
  发表级别的吸收边与激子峰要靠 GW-BSE（或至少 HSE 起步，见 §36.7）**。

### 36.11 GW-BSE 四步流程（Si 实例）与 VASPKIT 1.4.1 的新流程

> 同一篇文章的实操部分。工具版本：**VASP 5.4.4、VASPKIT 1.4.1、Python 3.11**。
> ⚠️ 原文提醒：**用 VASPKIT 1.2.4 做这一步的数据处理"会有一些问题"，请尽量用更新的版本**。
> VASPKIT 自带例子里有 **`optical_2D`** 与 **`Si_BSE_optical`** 两套输入文件可直接对照。

#### ① 四步与各步的 INCAR

| 步 | 做什么 | 关键 INCAR | 产出 |
| --- | --- | --- | --- |
| ① DFT | 基态 | `PREC=Normal`、`ENCUT=250`、`ISMEAR=0`、`SIGMA=0.01`、**`KPAR=8`**、`EDIFF=1E-8` | `WAVECAR` |
| ② **空态** | 一次迭代算出空轨道 | **`ALGO=EXACT`**、**`NELM=1`**、**`NBANDS=216`**、`LOPTICS=.TRUE.` | `WAVECAR`、**`WAVEDER`** |
| ③ **`G₀W₀`** | 准粒子修正 | **`ALGO=GW0`**、`NELM=1`、`NBANDS=216`、**`NOMEGA=72`**、`LWAVE=.TRUE.`、`LSPECTRAL=.TRUE.`、`LOPTICS=.TRUE.` | `WAVECAR.chi` + **`*.tmp`**（临时文件数与 **k 点数**有关） |
| ④ **BSE** | 电子-空穴（激子） | **`ALGO=BSE`**、`NOMEGA=72`、**`OMEGAMAX=10`**、**`NBANDSO=16`**、**`NBANDSV=16`**、`NEDOS=3000`、`LSPECTRAL`、`LOPTICS` | 光谱 |

- ⚠️ **每步都要把上一步的文件拷齐**：② 要 ① 的 `WAVECAR`；③ 要 ② 的 `WAVECAR` **和 `WAVEDER`**；
  ④ 要 ③ 的 `WAVECAR`、`WAVEDER`、**`WAVECAR.chi`**、以及**所有 `*.tmp`**。
  （`WAVEDER` 是光学计算需要的"波函数对 k 的导数"文件；**缺了它第三步直接算不了**。）
- `KPAR=8` 要求**核数是它的整数倍**（见 `references/performance.md`）；
- **`NBANDS=216` 的用意**：把**空态/激发态**算够——"从基态到激发态的跃迁需要足够多的能带"。

#### ② 数据处理（VASPKIT 1.4.1）

```
vaspkit → 71 → 711 → 1 → 1
```

- ⭐ **1.4.1 比旧版多了一步**：可以**单独输出**你想要的折射率 / 消光系数 / 吸收系数 /
  能量损失函数 / 反射率；
- 之后在第四步目录下运行附带的绘图脚本 `optical.py`（本库已收进
  `scripts/reference/optical_plot_pdf.py`），得到四联图 PDF（`Optical.pdf`）：
  吸收系数、折射率、反射率、消光系数；**作者与文献对比结果符合**。

#### ③ 二维体系（石墨烯）的对照做法

- 石墨烯的 INCAR 关键项：`ENCUT=400`、`ISMEAR=0`、**`SIGMA=0.20`**、`NELM=30`、**`NBANDS=216`**、
  **`NOMEGA=72`**、`LWAVE`/`LSPECTRAL`/`LOPTICS` 三个都开、`EDIFF=1E-08`、**`NEDOS=10001`**；
- **三开关一起打开**：**`LWAVE=.TRUE.` + `LSPECTRAL=.TRUE.` + `LOPTICS=.TRUE.`**；
- ⚠️ **"计算光谱时 KPOINTS 里的 k 点要取得非常密"**（比普通自洽密得多）；
- 处理仍走 **`710`**（因为石墨烯是二维材料）：
  - **`ABSORPTION_2D.dat` 是"能量 + `xx` + `yy`"三列**（与 3D 的 `ABSORB.dat` 七列不同）；
  - ⭐ **它的纵轴单位是百分比 `%`**——这正好回答了 §三十六 前面那篇教程评论区里
    "为什么有的光学性质纵坐标是 %"的疑问；
  - **光学电导率图**读 `REAL_OPTICAL_CONDUCTIVITY_2D.dat` 与
    `IMAG_OPTICAL_CONDUCTIVITY_2D.dat`，**纵轴为 `σ_2D/σ₀`**（`σ₀ = e²/(4ħ)`）；
- 附带的两个绘图脚本已收进 `scripts/reference/`（见 `graphene_absorption_plot.py`、
  `graphene_optical_conductivity_plot.py`）；结果与文献符合。



---

## 三十七、有限温度声子谱（TDEP 与自洽声子）

> 用途：算**高温下的声子色散、声子线型（寿命）、非简谐效应、热膨胀、软模与结构相变**。
> 常规的**有限位移法/DFPT 声子只在 0 K 简谐近似下成立**；温度一高，"原子偏离平衡位置变大、
> 高阶力常数不可忽略"，就需要**用 MD 轨迹拟合力常数**这一类方法（TDEP / ALAMODE-SCPH 等）。
> 来源：`articles/20261001-TDEP计算高温声子谱_天帝君豪的个人博客.md`
> （天帝君豪博客 2020-06-28，<https://tiandijunhao.github.io/2020/06/28/tdep-ji-suan-sheng-zi-pu/>）。

### 37.1 总体思路与两条"产生位移-力数据"的路线

TDEP 的输入就是一批**构型（坐标）+ 力（+能量/应力）**，先拟合出**二阶（必要时三阶）力常数**，
再据此算声子色散、线型、热导等。数据可以来自两条路：

| 路线 | 做法 | 优点/代价 |
| --- | --- | --- |
| **A. 机器学习势 + LAMMPS MD** | 用 MTP/MLIP 等势跑 MD（可跑很长的轨迹、很大超胞） | 便宜、能取很多构型；**精度取决于势** |
| **B. VASP 从头 MD** | `IBRION=0` 直接跑 AIMD，再用脚本提取 | **精度最高**；代价大、轨迹短 |

⚠️ **两条路线共有的一个致命小坑**：**TDEP 用的初始超胞 `infile.ssposcar` 必须与 MD 实际所用的
原子坐标一致**（原文把这条写了两遍）。**不一致不会报错，只会让力常数拟合悄悄算错。**

### 37.2 路线 B：VASP AIMD 的 INCAR（Si 例子）

```
IBRION = 0          # 打开分子动力学
NSW    = 20000      # 步数（要足够长才能采样好）
POTIM  = 1          # 时间步长（fs）
SMASS  = 0          # 0 = 正则系综 NVT（-3 = 微正则 NVE）
TEBEG  = 300        # 起始温度（K）
TEEND  = 300        # 终止温度（K）
MDALGO = 2          # 热浴：2 = Andersen
ISYM   = 0          # 关对称性
ISIF   = 2          # 只动原子（不动晶胞）
ISMEAR = -1 ; SIGMA = 0.02585201664
KPAR = 2 ; IALGO = 38 ; NELMIN = 4
LREAL = Auto ; ENCUT = 400 ; PREC = Normal ; GGA = PE
LWAVE = .FALSE. ; LCHARG = .FALSE.
```

- 超胞用 **3×3×3**（Si 原胞两个原子）；
- 提取输入文件用脚本 **`process_outcar_5.3.py`**：
  `mpirun -np 16 vasp_std process_outcar_5.3.py OUTCAR --skip n`（`n` = 从第几步开始取，
  用来跳过**平衡阶段**；⚠️ 该脚本原文**没有给出内容**，本库无法收录，需自行准备）；
- 通用 AIMD 的其他注意事项见 **§二十六**（AIMD）——这里只列 TDEP 相关项。

### 37.3 路线 A：LAMMPS + 机器学习势（MTP/MLIP）

需要准备的文件（原文清单）：

```
in.lammps     # LAMMPS 输入（超胞也能直接在里面设置）
data.cell     # 超胞结构
grep_dump.sh  # 把 LAMMPS 的 dump 转成 TDEP 需要的输入文件
MTP100.mtp    # 机器学习势文件（种类按需选，不唯一）
```

LAMMPS 脚本的要点（原文给了两段，NVT 段 + NVE 段）：

- `units metal`、`boundary p p p`、`atom_style atomic`、`pair_style MLIP mlip.ini`；
- **NVT 段**：`velocity all create $t <seed> dist gaussian mom yes`、`velocity all scale $t`、
  `fix int all nvt temp $t $t 0.5`（阻尼建议 **0.2~2.0**）、`timestep 0.001`、`run 5000`；
- **采样段**：`run 20000`，同时用两个 `dump` 分别输出**坐标**（`dump.positions`）与
  **受力**（`dump.forces`），并用 `fix print` 把
  `step / etotal / pe / ke / temp / press / 六个应力分量` 写到 `dump.stat`；
- 💡 `dump_modify ... sort id` 很关键：**必须按原子 id 排序**，否则每帧顺序不一致，
  TDEP 会把力配错原子。

### 37.4 TDEP 的输入文件（六个 `infile.*`）

| 文件 | 内容 |
| --- | --- |
| `infile.ucposcar` | **原胞**（unit cell） |
| `infile.ssposcar` | **初始超胞**（⚠️ 必须与 MD 实际超胞一致） |
| `infile.meta` | MD 元信息：结构数目、温度、步长等 |
| `infile.positions` | **每一帧的原子坐标** |
| `infile.forces` | **每一帧的原子受力** |
| `infile.stat` | 每帧的能量、温度、压强、应力 |

- 另外还有 **`infile.qpoints_dispersion`**：自定义的高对称点路径（见 §37.5）。

### 37.5 计算命令链

```bash
# 1) 拟合力常数（-rc2 = 二阶截断半径，单位：晶格常数；要更准就再加三阶 -rc3）
extract_forceconstants -rc2 5
mv outfile.forceconstant infile.forceconstant

# 2) 声子色散
phonon_dispersion_relations
gnuplot outfile.dispersion_relations.gnuplot

# 3) 声子线型 / 动态结构因子（含三阶力常数时）
extract_forceconstants -rc2 5 -rc3 3
mv outfile.forceconstant infile.forceconstant
mv outfile.infile.forceconstant_thirdorder infile.forceconstant_thirdorder
lineshape --path -qg 12 12 12 -ne 600 --temperature 300
```

- **`-rc2` / `-rc3`** 是**二阶/三阶力常数的截断半径**（以晶格常数为单位）；
  二阶不够就加三阶（非简谐/线型必须要三阶）；
- `lineshape` 的 `-qg 12 12 12` 是 **q 点网格**、`-ne 600` 是**能量格点数**、
  `--temperature 300` 指定温度（线型本身是温度相关的量）；
- 产物：`outfile.dispersion_relations.gnuplot`（色散）、**`outfile.sqe.hdf5`**（动态结构因子
  `S(q,E)`，可画成声子线型图，见 §37.6）。

### 37.6 高对称路径与绘图

**`infile.qpoints_dispersion`** 支持两种写法（原文给了两种）：

```
# ① 自定义
CUSTOM                      ! 类型
100                         ! 每段点数
4                           ! 段数
0.000 0.000 0.000  0.000 0.500 0.500   GM X
0.000 0.500 0.500  0.000 0.625 0.375   X U
0.375 0.750 0.375  0.000 0.000 0.000   K GM
0.000 0.000 0.000  0.000 0.500 0.000   GM L

# ② 用内置 Bravais 类型
FCC                         ! 布拉伐格子类型
100                         ! 每段点数
4                           ! 段数
GM X
X U
K GM
GM L
```

**绘图**：色散直接 `gnuplot outfile.dispersion_relations.gnuplot`；线型用 `h5py` 读
`outfile.sqe.hdf5`（含 `q_values`、`energy_values`、`intensity`、`q_ticks`、
属性 `q_tick_labels`），用对数色标 `pcolormesh` 画成 `S(q,E)` 热图——
脚本已收进 `scripts/reference/lineshape_sqe_plot.py`。

### 37.7 同一博客的两篇姊妹文（后续可收录）

- ⭐ **《alamode_scph 计算高温声子谱》**
  <https://tiandijunhao.github.io/2020/07/04/alamode-scph/>
  ——**ALAMODE 的自洽声子理论（SCPH）**路线，`alamode-1.1.0`，输入 `vasprun.xml`（MD 轨迹）。
  与本节是**同一问题的另一套工具**：**TDEP 用"MD 轨迹 + 拟合有效力常数"，
  SCPH 用"自洽地修正声子频率"**；ALAMODE 在本库 `references/tools.md` §4.7 有速查条目。
  📌 **更正（本库注）**：该文**本库早已收录**（2026-10-01 早期，`articles/20261001-alamode_scph计算高温声子谱_天帝君豪的个人博客.md`），其流程已提炼为 `workflows.md` **第二十二节「高温声子：自洽声子理论（ALAMODE SCPH）」**（含 `alm.in`/`anphono.in` 的参数含义、`alm` → `anphon` 命令链、`scph.scph_bands` 产物），`errors.md` §五也有 ALAMODE 专项条目——**本节只补 TDEP 路线，两者的对照关系见下**。
- **《TDEP 安装教程》** <https://tiandijunhao.github.io/2020/06/24/tdep-an-zhuang/>
  ——基于 **gfortran** 环境、解压后按 **`important_settings`** 文件配置再编译。



---

## 三十八、声子谱：方法选择与 phonopy 实操（含 `IBRION=8` 路线）

> 用途：**用声子谱判断动力学稳定性**（审稿人最常问的一项）。本篇把"两种方法的原理差别"
> 与"phonopy 的完整操作"讲全了，并给出**虚频该怎么判读**的社区经验。
> 来源：`articles/20261001-vasp计算声子谱教程.md`（贺勇，公众号《学术之友》，
> 个人博客 <https://yh-phys.github.io>；例子同样是**二维 InSe**）。
> 相关章节：§六（有限位移法速览）、§七（晶格热导率）、§二十二（SCPH）、§三十七（TDEP）。

### 38.1 两种方法的原理与取舍（先想清楚用哪条）

| | **直接法（frozen-phonon）** | **DFPT（微扰密度泛函）** |
| --- | --- | --- |
| 做法 | 在优化的平衡结构里**引入原子位移**，算 **Hellmann-Feynman 力**，由动力学矩阵得色散 | 算**能量对外场微扰的响应**，直接得到"原子移动引起的势场变化"，再构造动力学矩阵 |
| 限制 | ⚠️ 要求**声子波矢与原胞边界正交**，或原胞大到 H-F 力在胞外可忽略 ⇒ **高对称晶体、合金、超晶格等必须用超胞**，计算量急剧增加 | ⭐ **不限定波矢与原胞边界正交，不需要超原胞也能对任意波矢求解** |
| 出身 | 早期通用做法 | **1987 年 Baroni、Giannozzi、Testa 提出**；CASTEP/VASP 的 linear response 即此类 |

- ⇒ **能用 DFPT 就优先 DFPT**（尤其高对称/复杂体系）；直接法在"超胞不大、想要力常数细节"时更灵活；
- 💡 稳定性问题的**配套手段**：**声子谱 → 动力学稳定性**；**AIMD → 热稳定性**；
  个别体系还有旁证（钙钛矿看离子半径、异质结看结合能）——写文章时通常要**至少两项互相印证**。

### 38.2 phonopy 的安装（源码 + Anaconda）

```bash
# 1) Anaconda 环境
bash Anaconda3-2019.07-Linux-x86_64.sh
echo "export PATH=/……/anaconda3/bin:$PATH" >> ~/.bashrc ; source ~/.bashrc

# 2) 编译安装 phonopy（示例 2.2.0）
tar zxvf phonopy-2.2.0.tar.gz
cd phonopy-2.2.0
python3 setup.py install --user

# 3) 环境变量指向安装生成的脚本目录（版本号按实际改）
echo "export PATH=/……/phonopy-2.2.0/build/scripts-3.7:$PATH" >> ~/.bashrc ; source ~/.bashrc

# 4) 自检
phonopy
```

### 38.3 ⚠️ 先做高精度优化（否则必出虚频）

> 原文原话：**"声子谱的计算需要对原胞结构做高精度的充分优化，否则很容易出现虚频"**。

二维 InSe 例子用的优化 INCAR 关键项：`PREC=Accurate`、`ENCUT=500`、**`EDIFF=1E-08`**、
**`EDIFFG=-0.001`**、`ISIF=3`、`ISMEAR=0`、`SIGMA=0.02`、`LREAL=.FALSE.`、`ALGO=Normal`、
`NSW=200`、`IBRION=2`；二维体系另加 **`OPTCELL 100110000`**（固定 z 方向晶格，
⚠️ 但**它需要改源码重编译 VASP 才生效**，见 §36.9 ④）。

### 38.4 建超胞：`phonopy -d`

```bash
cp CONTCAR POSCAR
phonopy -d --dim="4 4 1"
# 产出：phonopy_disp.yaml  SPOSCAR  POSCAR-001 … POSCAR-016

cp POSCAR POSCAR-unitcell     # 原胞留一份给后面的 -c 用
cp SPOSCAR POSCAR             # 超胞作为接下来 VASP 计算的 POSCAR
```

- ⚠️ **建超胞前先在建模软件（如 Materials Studio）里把对称性找对**，否则位移构型会多出一大堆、
  **计算量成倍增加**；
- 💡 **别被 `POSCAR-00x` 迷惑**：`phonopy -d` 会**同时**产出
  **`SPOSCAR`（超胞本身）**和 **`POSCAR-001…016`（一个个位移构型）**。
  **`IBRION=8` 路线只需要 `SPOSCAR`**；那些 `POSCAR-00x` 是**有限位移路线**才要用的
  （逐个算完再用 `phonopy -f` 汇总，见 §六）。

### 38.5 `IBRION=8`：让 VASP 自己算 Hessian（本教程走的路线）

```text
ISTART = 0 ; IBRION = 8 ; NSW = 1        # ★ IBRION=8：算力学 Hessian（力常数）
IALGO = 38 ; NELM = 200
EDIFF = 1E-07 ; EDIFFG = -0.001
ENCUT = 500 ; PREC = Accurate ; LREAL = .FALSE. ; ADDGRID = .TRUE.
ISMEAR = 0 ; SIGMA = 0.02
LWAVE = .FALSE. ; LCHARG = .FALSE.
```

- **Hessian 矩阵会写进 `vasprun.xml`**（这就是下一步 `phonopy --fc` 的输入）；
- KPOINTS 可按服务器能力**适当加密**，POTCAR 不变；
- 📌 这条路线的优点：**不需要你手工提交 16 个位移构型的作业**（VASP 用对称性在内部做位移差分）；
  代价是单次作业更重、且对 `NELM`/`EDIFF` 更敏感。

### 38.6 后处理与出图

```bash
# 1) 从 vasprun.xml 生成力常数
phonopy --fc vasprun.xml            # → FORCE_CONSTANTS
```

`band.conf`（高对称点路径）：

```
ATOM_NAME = In Se            # 元素名，顺序与 POSCAR 一致
DIM = 4 4 1                  # 超胞大小
BAND = 0.5 0.0 0.0  0.0 0.0 0.0  0.333333 0.333333 0.0  0.5 0.0 0.0
FORCE_CONSTANTS = READ       # 读取力常数文件
```

- ⚠️ **每条路径上的高对称点之间用"两个空格"分隔**（`BAND` 行的解析规则）；
- ⚠️ **原文笔误**：文中把力常数文件写成 `FORCE_CONSTRAINS`，**正确名字是 `FORCE_CONSTANTS`**
  （本库按正确拼写记录，`band.conf` 里的关键字同理）。

```bash
# 2) 生成 band.yaml
phonopy --dim="4 4 1" -c POSCAR-unitcell band.conf

# 3) 导出画图数据
phonopy-bandplot --gnuplot > PBAND.dat
```

- 💡 **phonopy 默认在两个高对称点之间打 `51` 个点，且 `PBAND.dat` 中每组高对称点之间以一个空行分隔**
  ——知道这两点才好直接画图/分段处理。

### 38.7 ⭐ 虚频该怎么判读（原文后记，社区经验）

1. **只有 Γ 点有一点点虚频、其余都好** ⇒ **材料很可能是稳定的，只是优化精度不够**；
   **进一步提高优化精度（更严的 `EDIFF`/`EDIFFG`）通常能消掉这一点虚频**。
2. **二维材料的 Γ 点小虚频**：**基本可以认为是稳定的**——"大部分二维材料都会有此现象"，
   而且 **VASP + phonopy 算二维材料在 Γ 点尤其容易出现虚频**。
   - 作者补充：**Quantum-ESPRESSO 的 PWSCF/PH 模块内存需求更小、对二维材料声子谱更友好**
     （他预告了 QE 的声子教程——本库暂未收录）。
3. 📌 本库提醒：以上都是"**小虚频**"的经验判据。**若虚频出现在 Γ 以外、或幅度不小（如 > 0.5 THz 量级），
   那就不是精度问题而是真的动力学不稳定**——此时值得交叉验证：加大超胞（`DIM`）、
   核对 `OPTCELL`/固定基矢是否正确、检查 `ISYM`/`ISMEAR`，必要时用 **§二十二（SCPH）或 §三十七（TDEP）**
   看有限温度下是否被非谐效应"稳住"。



### 38.9 两条路线的"产物对照"与几个环境坑（另一篇 phonopy 教程）

> 出自 `articles/20261001-vasp_phonopy计算声子谱.md`（June976 / <https://www.jun997.xyz>，
> 以 **Si** 为例）。这篇把**有限位移**与 **DFPT/`IBRION=8`** 两条路线**并列写下来**，
> 正好补上本节前面缺的"产物对照"，另外给了 `IBRION=8` 的两个环境注意事项。

#### ① 先记住"支数规则"（判断声子谱对不对的第一招）

- **`m` 维晶体、原胞内有 `n` 个原子** ⇒ 振动自由度 `mn` ⇒ **`m` 支声学波 + `m(n-1)` 支光学波**；
  （例：三维 Si（`n=2`）⇒ 3 支声学 + 3 支光学 = **6 支**，与本文算出来的谱一致。）
- **声学支**：`k → 0` 时 `ω → 0`（Г 点处三条都归零，这就是"声学"的含义）；
- **光学支**：`k → 0` 时 `ω → ≠0`；
- **声子谱**本身 = **声子频率 `ω` 与波矢 `k` 的色散关系（布里渊区内）**；
- 🔍 **稳定性判据**：**全谱都在 0 以上（无虚频）⇒ 动力学（热力学）稳定**。
- 💡 声子的由来（概念）：简正坐标下振动能量量子化为
  `ε = (n + 1/2)ℏω_k`，**以 `ℏω_k` 为最小激发单元** ⇒ 把这个量子称为"声子"（准粒子，非实体粒子）。

#### ② ⭐⭐ 两条路线的命令与产物对照（最容易混淆的一对）

| | **有限位移法** | **DFPT / `IBRION=8`** |
| --- | --- | --- |
| 建超胞 | `phonopy -d --dim='3 3 3' -c CONTCAR` | 同样用 `phonopy -d`，但**只需要 `SPOSCAR`**（位移构型不用） |
| VASP 要算什么 | **每个位移超胞各跑一次单点**（`POSCAR-001`…；**结构复杂时会有很多个，全都要算**） | **只跑一次**：在超胞上做 `IBRION=8` 的微扰/Hessian 计算 |
| 单点 INCAR 要点 | **`NSW=0`**、⚠️ **`ISIF` 不能设为 `0`**（要算 **Hellmann-Feynman 力**！）、**扩胞后要减小 KPOINTS 网格密度** | **`NSW=1`**、`IBRION=8`、⚠️ **并行参数要关**（见 ③） |
| 提取力常数 | **`phonopy -f disp-001/vasprun.xml`** ⇒ **`FORCE_SETS`** | **`phonopy --fc vasprun.xml`** ⇒ **`FORCE_CONSTANTS`** |
| `band.conf` 里 | **不写**力常数关键字（默认读 `FORCE_SETS`） | 要写 **`FORCE_CONSTANTS = READ`** |
| 出图 | `phonopy -p -s band.conf` ⇒ **直接得到 PDF** | 同左 |

- ⚠️ **这一对名字极像**（`FORCE_SETS` vs `FORCE_CONSTANTS`），却是**两条不同路线**的产物：
  拿错文件不会报错、只会给出**错误的谱**——**先确认自己走的是哪条路线**；
- ✅ 两条来源可以互相印证：**"`IBRION=8` 只需要 `SPOSCAR`、不需要位移构型"** 在 §38.4 也写了 ✓

#### ③ ⚠️ `IBRION=8` 的两个环境注意事项（本篇独有）

1. **并行参数要关掉**：原文明确说 **`NPAR`、`NCORE`、`KPAR` 等并行参数"都关闭，不然会报错"**；
   （注意：这一点与 §38.5 那篇的例子（用 `KPAR` 跑 MD）**语境不同**——**做 `IBRION=8` 的 Hessian 步时，
   并行参数容易触发报错**，稳妥做法是先设 `NPAR=1`/不设 `KPAR`/不设 `NCORE` 试一次。）
2. **建议打开对称性 `ISYM = 2`**：**"为了减小计算量"**——因为**对称性可以直接减少需要做的位移数**；
   （⚠️ 与 §33/§38.4 里"SOC/某些场合要关对称性"并不矛盾：**那里关是为了让 k 点集与磁构型可控，
   这里开是为了少做位移**——**看你要解决的是哪一类问题**。）

#### ④ `band.conf` 的进阶写法（比 §38.6 更细）

```
ATOM_NAME = Si
DIM = 3 3 3
BAND = 0.0 0.0 0.0  0.5 0.0 0.5  0.625 0.25 0.625,  0.375 0.375 0.75  0.0 0.0 0.0  0.5 0.5 0.5
BAND_POINTS = 101                      # 每段的点数（默认 51）
BAND_LABELS = $\Gamma$ K X $\Gamma$ L    # 高对称点标签（画图时直接标注）
FORCE_CONSTANTS = READ                 # 仅 DFPT/IBRION=8 路线需要这一行
```

- **路径可以用逗号分成若干段**（逗号处就是"断开"的位置，便于画不连续路径）；
- **`BAND_POINTS`** 控制每段点数、**`BAND_LABELS`** 给高对称点起名（省得自己标）；
- 运行 **`phonopy -p -s band.conf`**：**`-p` 画图、`-s` 保存**（直接产出 PDF/PNG），
  比 §38.6 里"导出 `PBAND.dat` 再自己画"更省事——两种方式按需选。
- 参数含义的权威出处：<https://phonopy.github.io/phonopy/setting-tags.html> ✓



---

## 三十九、U 值怎么来：线性响应法求自洽 Hubbard `U`（`Ueff`）

> 用途：**§三十 讲的是"给了 `U` 之后怎么用、有哪些静默陷阱"**，本节补上前置问题——
> **`U` 到底取多少**。做法是 **VASP 官网的线性响应方法（Cococcioni 方案）**：
> 给体系**加一系列 `U` 扰动**，看**占据矩阵的响应**，由"加 U 前 / 加 U 后"两条响应曲线拟合出 `Ueff`。
> 来源：`articles/20261001-基于Shell_VASP实现自动计算DFT_U中的U值_附源代码.md`
> （作者 **SuYun Wang**，2021-10-18，附完整 shell 脚本）；官方教程见文末链接。

### 39.1 五步流程（官方方法的自动化版）

| 步 | 做什么 | 要点 |
| --- | --- | --- |
| 0 | **生成输入文件** | 只有 `POSCAR` 是必须的（可由 Materials Project 等获取）；`KPOINTS`/`POTCAR`/`INCAR` 可让脚本调 **VASPKIT** 生成。⚠️ **自动生成的 INCAR 是"不完整"的，尤其 `MAGMOM` 必须自己设**（磁性/强关联体系这一步不能省） |
| 1 | **算 DFT 基态**（无 `U`） | 需要指定**要算哪个原子的 `U`**（在 `POSCAR` 中的位置）与**加到哪个轨道**（`d`/`f`） |
| 2 | **算 +U 的自洽与非自洽** | 对扫描范围内的每个 `U` 值：**先 NSCF、再 SCF**（脚本目录名即 `1-U-NSCF` / `2-U-SCF`） |
| 3 | **提取并拟合 `Ueff`** | 输出 `output.wsy`，**最后一行就是该原子的 `U` 值**；也可按官网做法**用数据列线性拟合**得到 |
| — | 中间文件 | `input.wsy`（脚本用，**不要改**） |

### 39.2 关键参数与"扫描"的写法

```sh
# 脚本顶部的初始化设置（U 值扫描范围，单位 eV）
MAX  =  0.20
MIN  = -0.20
STEP =  0.05
```

- ⭐ **做法是"扫 `U`"**：在 `-0.20 ~ +0.20`（步长 `0.05`，共 9 个点）范围内，
  **每个 `U` 值各做一轮 NSCF + SCF**，再由这些数据的响应关系拟合 `Ueff`；
- ⭐⭐ **核心参数是 `LDAUTYPE = 3`**（脚本如此设置，与官网《Calculate U for LSDA+U》教程一致）：
  **它是"线性响应求 U"专用的类型**——⚠️ 但 **VASP wiki 的常规参数表里只列了 `1`/`2`/`4`**，
  **没有列 `3`**，所以第一次看到会怀疑写错了（评论区就有人问"为什么设 3"）——
  **这正是这套方法的特殊之处，不要照抄到常规 +U 计算里**（常规计算用 `LDAUTYPE = 2`，见 `references/incar.md`）。

### 39.3 注意事项与实测差异

- ⚠️ **赝势不同，算出的 `U` 与官网例子会有差别**（原文明确说明）——所以 **`U` 不是"普适常数"**，
  **要在你自己的赝势/结构上重算**；
- ⚠️ 该方法的**第一性依据是"线性响应"**，因此对**初始磁构型、`MAGMOM`、展宽/`ISMEAR`** 都比较敏感，
  建议全程保持一致、并**核对每个 `U` 值下是否都收敛到同一磁态**（呼应 §三十 的"三处静默陷阱"）；
- 📌 **拿到 `Ueff` 之后**：把它填进常规 DFT+U 计算（`LDAU=.TRUE.`、`LDAUTYPE=2`、`LDAUL`/`LDAUU`/`LDAUJ`），
  并按 §三十 检查 `LMAXMIX`（`d→4`、`f→6`）与混合参数；
- 💡 同时存在一个**社区实现** <https://github.com/sylearn/Ueff_VASP>（评论区提到），
  与本篇脚本可以互相校对。

### 39.4 现成工具

| 工具 | 说明 |
| --- | --- |
| **`vasp_Ueff-1.0.wsy`**（本文作者脚本） | 交互式菜单 shell：`0` 生成输入 → `1` DFT 基态 → `2` +U 的 NSCF/SCF → `3` 提取 `Ueff`。**本库已收集**（`scripts/reference/vasp_Ueff-1.0.wsy`，⚠️ 原文导出丢换行，**请以上游仓库的可运行版本为准**） |
| 作者 GitHub | <https://github.com/Code-WSY/Code-WSY> |
| 社区实现 | <https://github.com/sylearn/Ueff_VASP> |
| **官方教程** | VASP wiki: *Calculate U for LSDA+U*（中文转述：<https://mp.weixin.qq.com/s/93nuu0ksVPH_MzuSKysqKA>） |



### 39.5 ⭐ 脚本内部的实际公式：`Ueff = 1/χ_SCF − 1/χ_NSCF`

> 上面第五节把"扫 `U`、看响应"说得比较笼统。本库通读了随文的 shell 源码后，
> 把**它究竟怎么算**写清楚（这条是本节的钥匙，理解了它就知道每一步在干什么）：

**① 每个 `U` 值下为什么既做 NSCF 又做 SCF**

| 目录 | `ICHARG` | 物理含义 |
| --- | --- | --- |
| `1-U-NSCF` | **`ICHARG = 11`**（读 `CHGCAR`，**固定电荷密度**） | 得到**非自洽响应 `χ₀`**（电子密度不跟着 U 变） |
| `2-U-SCF` | **`ICHARG = 1`**（**自洽**） | 得到**自洽响应 `χ`**（电子密度随 U 重新分布） |

- 两者都要读一遍 DFT 基态步的 `CHGCAR`/`WAVECAR` 作为起点；
- 在 SCF 那一步的 INCAR 里追加：`LDAU=.TRUE.`、**`LDAUTYPE=3`**、`LDAUL`、`LDAUU`（= 当前扫描的 `U`）、`LDAUJ`。

**② 占据数从哪里读**

- 从 `OUTCAR` 里取**目标原子对应轨道的 `total charge`**（占据数），DFT / NSCF / SCF 三个值各取一次；
- 这就是为什么要 **`LORBIT = 11`**（输出按原子/轨道投影的信息）与 **`LMAXMIX = 4`**（`d` 电子）。

**③ 公式：两条响应曲线的斜率**

脚本只取**扫描区间的两端**（`MIN = -0.2` 与 `MAX = +0.2`）算斜率，即两点线性拟合：

```
χ_SCF  = [N_SCF(+0.2)  − N_SCF(−0.2)]  / ΔV          # 自洽响应
χ_NSCF = [N_NSCF(+0.2) − N_NSCF(−0.2)] / ΔV          # 非自洽响应
Ueff   = 1/χ_SCF − 1/χ_NSCF                          # ★ 这一行就是线性响应法求 U
```

- 这正是线性响应法（Cococcioni 方案）的核心表达式：**`U` 补偿的是"自洽响应"与"非自洽响应"之差**；
- 原文说的"也可以用**第一列和最后两列数据线性拟合**"，指的就是**用全部 9 个点而不是只用两端**
  来做同样的斜率拟合——**点数越多，拟合越稳**（本库建议：若两端取值对斜率影响大，就用全点拟合）。

**④ 脚本预置的 INCAR（作者给的起点，注意 `MAGMOM` 是空的）**

```
SYSTEM = CAL-Ueff ; PREC = A ; EDIFF = 1E-6
ISMEAR = 0 ; SIGMA = 0.2 ; ISPIN = 2
MAGMOM =                 # ⚠️ 脚本留空，必须自己填（磁性/强关联体系这一项不能省）
LORBIT = 11 ; LMAXMIX = 4
```

- ⚠️ 这也印证了 §39.1 里那句"**自动生成的 INCAR 是不完整的**"：`MAGMOM` 空着就直接跑，
  很可能收敛到错误的磁态，**算出来的 `U` 也就没有意义**。



---

## 四十、`U` 值选得对不对：判据清单与两个常见困惑

> 用途：**§三十九 解决"U 从哪来"（线性响应怎么算），§三十 解决"给了 U 怎么用"**；
> 本节解决最后一环——**怎么判断你手上这个 `U` 靠不靠谱**。
> 来源：`articles/20261001-VASP计算之DFT_U.md`（转载自公众号《VASP学习交流》，2021-09-21）。

### 40.1 ⭐⭐ 判断 `U` 是否合适的五项清单（原文给的顺序）

| # | 判据 | 备注 |
| --- | --- | --- |
| 1 | **磁矩是否与实验值吻合** | 最直接、最常用 |
| 2 | **磁基态是否与实验吻合** | 铁磁/反铁磁/亚铁磁哪个是基态 |
| 3 | **磁转变温度（居里 `Tc` / 奈尔 `Tn`）是否与实验吻合** | 📌 **金属体系用 Heisenberg 模型预测转变温度通常会高估**（见 §三十二） |
| 4 | **能带在定性上是否与实验吻合** | ⚠️⚠️ **不要追求能隙数值吻合**——**LDA/GGA 本来就低估能隙**，+U 也不是为了凑带隙 |
| 5 | **U 对所关心性质的影响有多大** | 若是**自己预测的新体系**：**不同 `U` 都测一遍**，看结论是否随 `U` 大幅变化（**结论稳健才是好结论**） |

- ⚠️ **前提认知**：**`U` 本质上是经验参数**——**同一元素在不同晶体配位环境下的 `U` 通常也不同**，
  所以**不能直接照抄文献里同元素的 `U`**，要查文献 + 自己测试。
- 📌 **社区补充讨论**（原文评论区）："同一元素不同配位环境 U 不同"这一点**在文献里常被忽略**，
  有读者质疑"考虑这么细的性价比如何"——**本库如实记为未决**：实践中至少应做到
  **"改结构后重测 `U`（或说明沿用理由）"**，而不是默默沿用。

### 40.2 两个常见困惑

**① "我要用 PBE+U，INCAR 里写什么？"**

- **还是 `LDAU` 系列标签**（`LDAU = .TRUE.`、`LDAUTYPE`、`LDAUL`、`LDAUU`、`LDAUJ`）；
- **"+U 的类型"由 `POTCAR` 决定**：用 **PBE 赝势**跑出来就是 **GGA+U**，用 LDA 赝势就是 LDA+U——
  **INCAR 里没有"GGA+U"这样的开关**。

**② "体系里既有 `d` 又有 `f` 电子，怎么设？"**

- `LDAUL`/`LDAUU`/`LDAUJ` **按 `POSCAR` 里的元素顺序逐个给**，所以混合体系就是**每个元素写自己的**：

```
# 例：POSCAR 顺序为 Ce(4f) O(2p) Co(3d)
LDAUL  = 3   -1   2
LDAUU  = 5.0  0.0  3.0
LDAUJ  = 0.0  0.0  0.0
LMAXMIX = 6        # ★ 取"最大的那个"：有 f 电子就写 6（只有 d 则 4）
```

- ⚠️ **`LMAXMIX` 取最大值**这一点最容易漏：只要体系里有 `f` 电子，为了能带/`ICHARG=11` 的正确性就应设 `6`。

### 40.3 ⚠️ `LDAUTYPE = 2` 时 `Ueff = U − J`：**别拿不同 `U`/`J` 的总能量互相比较**

- `LDAUTYPE = 2`（Dudarev 简化式）下，**总能量同时取决于 `U` 与 `J`**，真正起作用的是 **`Ueff = U − J`**；
- ⚠️⚠️ 因此**"用不同 `U` 和/或 `J` 算出来的总能量放在一起比较"是没有意义的**
  （这正是本库把这条同时收进 `errors.md` §七 的原因——它属于"**静默给出错结论**"的那一类）；
- ✅ **正确的比较方式**：**固定 `Ueff`**（例如都取 `Ueff = 3 eV`，用 `U=3, J=0` 或 `U=4, J=1`），
  或者**只比较"同一套 `U`/`J` 下的相对能量**（如不同磁构型之间）。

### 40.4 加 U 的机理（一小段就够）

- 未屏蔽的电子-电子相互作用可以用 **Slater 积分 `F0`、`F2`、`F4`、`F6`**（`f` 电子）表示；
- 但**用原子波函数算出的 Slater 积分会"过度估计"真实相互作用**——因为**固体里库仑作用被屏蔽了（尤其 `F0`）**；
- 所以实践中**把这些积分当作参数**，**调到与实验在某种意义下一致**（平衡体积、磁矩、带隙、结构），
  通常就以**有效库仑/交换参数 `U` 与 `J`** 的形式给出（`U`、`J` 也可由**受约束的 LSDA 计算**提取）；
- VASP 的实现里：**在位用 Hartree-Fock 型相互作用替换 L(S)DA**，同时**减去双重计数能 `Edc`**
  （它被假定等于在位 L(S)DA 对总能的贡献）。

### 40.5 一个最小参数示例（`Co O` 体系）

```
LDAU    = .TRUE.     # 打开 U
LDAUTYPE = 2         # 类型（默认 2，Dudarev 简化式）
LDAUL   = 2  -1      # 对哪些轨道加 U：1=p、2=d、3=f、-1=不加
LDAUU   = 3.0 0.0    # U 值（eV），按元素顺序
LDAUJ   = 0.0 0.0    # J 值（eV）
LMAXMIX = 4          # d 电子写 4，f 电子写 6
```

- ⚠️ **原文一处疑似笔误**：文中在 `LDAUL` 行后也写了"**默认是 2**"——这句更像是在说 `LDAUTYPE`；
  **`LDAUL` 的含义是"每个元素的轨道类型"，没有"默认 2"的说法**，本库按含义记录。
- 📌 **与 `ICHARG=11` 的联动**（本库 §8.24 与 §三十 已记，此处原文再次强调）：
  **`CHGCAR` 只包含 PAW 占用矩阵在 `LMAXMIX` 之前的信息**，
  所以 **L(S)DA+U 的能带计算严格要求 `LMAXMIX` 取足**（`d → 4`、`f → 6`），否则非自洽能带会明显偏离自洽结果。



### 40.6 ⭐ `U` 的典型取值范围（速查，可作为起点）

| 体系 | 常用 `U` |
| --- | --- |
| **过渡族金属（Ti、V、Cr、Mn、Fe 等）的 `d` 电子** | **典型 ≈ `3.0 eV`，多在 `2.0 ~ 4.0 eV`** |
| **稀土氧化物（`f` 电子）** | **多为 `4 ~ 7 eV`** |
| `J` | **一般比 `U` 小一个数量级**（常见取 `0 ~ 1 eV`；`LDAUTYPE=2` 下起作用的是 `U−J`） |

- 用法：**先用这个范围做起点**，再按 §40.1 的五项判据验证；**不要把它当成"标准答案"**；
- 与 §39.5 的关系：**能自己算就用线性响应算**（`Ueff`），文献值/经验值用于交叉验证。

### 40.7 DFT+U 的思想框架，以及"DFT 带隙问题"的具体表现

**① 为什么需要 `+U`（一句话框架）**

- 把体系的轨道**分成两个子体系**：
  1. **一般的 DFT（LDA/GGA）能比较准确描述**的那部分；
  2. **定域在原子周围的 `d`/`f` 轨道**——标准 DFT **给不出正确的"能量 ↔ 占据数"关系**；
- 对这第二部分，**用一个与轨道占据和自旋相关的有效 `U`** 来描述电子间关联能 ⇒ 这就是 DFT+U；
- 更本质的说法：简单固体理论里忽略电子间静电作用，而**强关联体系里这部分不能忽略**
  （写进哈密顿量就是 **Hubbard 模型**）；含 `d`/`f` 电子的**过渡金属氧化物、稀土及其化合物**是典型对象。

**② "带隙问题"到底有多严重（具体例子）**

| 体系类型 | LDA/GGA 的表现 |
| --- | --- |
| **Si、GaAs 等简单半导体** | **带隙远远偏小**（定性还行，定量差） |
| ⚠️ **Ge、InN 等小带隙半导体** | **被算成金属态**，而实验上是半导体 |

- ⇒ ⚠️ **"算出来是金属"时，先怀疑泛函**：如果是小带隙半导体，很可能只是 LDA/GGA 的错，
  **不要直接下"该材料是金属"的结论**；
- 📌 但也要记住 §40.1 第 4 条的警告：**+U 不是为了把带隙"凑"到实验值**——
  它能改善带隙**定性**，但定量仍需 HSE/GW（见 §二十九、§36.10）。

### 40.8 ⚠️ 一个真实案例：参数顺序写反**不会报错**（原文示例即如此）

原文给的例子是：**POSCAR 元素顺序为 `La`、`S`，其中 `S` 不加 U、`La` 的 `f` 轨道加 U（`U−J`）**，
然后写成了：

```
# ✗ 原文（顺序与它自己的说明相反）
LDAUL = -1  3
LDAUU =  0  5.5
LDAUJ =  0  0.5
```

- ⚠️ **这与它自己第 1 条说明"三个参数顺序应与 POSCAR 元素顺序一致"直接矛盾**——
  **`La` 在前，就应该把 `La` 的值写在前面**；
- ✅ **按 `POSCAR` 顺序（`La`、`S`）的正确写法**：

```
# ✓ 修正后（La 的 f 轨道加 U；S 不加）
LDAUL = 3  -1
LDAUU = 5.5  0
LDAUJ = 0.5  0
```

- ⚠️⚠️ **为什么这条特别危险**：写反**不会报错**——`LDAUL=-1 3` 会让 `S` 去"加 `f` 轨道的 U"
  （S 根本没有 `f` 电子），结果是**U 实质上没加到该加的元素上**，而计算照样跑完、照样收敛。
  本库把这条同时收进 `errors.md` §七（静默陷阱：**改完 `LDAU*` 一定回头对一遍 `POSCAR` 元素顺序**）。
- 📌 这条其实是被**评论区读者发现的**（"作者是不是写反了……"）——**原文未更正**，
  本库按正确顺序记录并在此标注。

**③ 评论区另外两个未答问题（本库给出答案）**

1. **"如果不考虑带隙问题，是不是就可以不考虑加 U 了？"**
   —— **不行**。`+U` 的作用**远不止修带隙**：它主要改善**磁矩、磁基态、电子局域化/占据数、
   晶格常数（体积）**，这些正是 §40.1 里的前几项判据。**只关心磁性和结构时，同样可能需要 +U**；
   反过来，"只为了带隙"而加 `U` 也不是好理由（见 §40.1 第 4 条）。
2. **"从最开始结构优化就要加 U 吗？"**
   —— **建议全程一致**（优化阶段就加 `U`）。理由：**结构必须在"与后续性质计算相同的能量面"上优化**，
   否则优化出来的几何与带 `U` 的能量面不自洽；而 `+U` 会显著影响局域轨道与晶格常数。
   （若只为快速获得初始结构而先不加 `U`，**至少要再用带 `U` 的设置重新优化一遍**。）



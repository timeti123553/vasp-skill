---
name: vasp-skill
description: "VASP 计算工作流助手：诊断 VASP 报错、生成基于 VASP 的计算流程与输入文件、输出数据画图，可沉淀用户提供的 VASP 文章为可检索知识库。当用户（1）粘贴 VASP 报错信息 / OUTCAR / 日志片段，想定位错误发生在哪个阶段、原因是什么、如何解决；或（2）表述想算的性质（结构优化、静态自洽、能带、态密度、磁性、声子谱、晶格热导率 / 三声子四声子、热电 Seebeck / ZT、高通量筛选等），想要一套基于 VASP 的完整计算流程（先后步骤、关键 INCAR/KPOINTS/POTCAR 参数、提交与验证方法），并可用 pymatgen/ase 自动生成 VASP 输入文件；或（3）提供 VASP/LOBSTER 输出数据（vasprun.xml / DOSCAR / OSZICAR / OUTCAR / COHPCAR.lobster / 声子谱 / 热导率等），想把结果画成图（DOS、能带、收敛曲线、COHP/ICOHP 等；`vasprun.xml`/`DOSCAR` 等大文件由 skill 生成可在本地运行的 Python 画图脚本，而不是读进上下文）；或（4）提供 VASP 使用文章 / 教程 / 报错记录，希望收录进 skill 的知识库用于后续报错检索时使用。"
---

# vasp.skill

面向计算材料科研的 VASP 工作流助手，覆盖**三大能力**：**VASP 报错诊断**、**VASP 计算流程生成（含输入文件生成）** 和 **VASP 输出数据画图**（另有知识库与文章收录作为支撑）。

## 核心能力

### 1. VASP 报错诊断

用户提供报错信息（OUTCAR 片段、stdout、错误消息）时：

- 先按 `references/errors.md` 的「诊断流程」定位：确认版本/运行方式 → 判断报错阶段（初始化 / SCF / 离子步 / 后处理 / MPI 编译）→ 区分致命错误与警告。
- 用报错中的稳定关键词匹配该文件中的错误分类（INCAR / POSCAR / KPOINTS / POTCAR / SCF 收敛 / 离子步 / 数值 NaN / 内存 / ALAMODE 等），给出**定位 + 成因 + 可执行方案**，并说明改哪个文件哪个参数、重跑后如何确认。
- **目录或条目未直接命中时，先运行 `python scripts/search_kb.py "<报错关键词>"` 全库检索**——它会查 `errors.md`、`workflows.md` 和 `articles/` 文章知识库，返回命中文件、行号与上下文，再据此定位。
- 表内/知识库都未命中时，按「阶段定位 → 成因分类 → 排查」通用路径给出结构化方案，不要机械复读。

读取时机：收到报错诊断请求时读取 `references/errors.md`；关键词命不中时运行 `scripts/search_kb.py` 并读取命中片段（含 `articles/` 中的文章）。

### 2. VASP 计算流程生成

用户表述想算的性质时：

- 读取 `references/workflows.md`，按「流程选择」判断主流程（优化 → 静态自洽 → 属性）。
- 输出含：一句话流程、每步关键参数表（INCAR 的 PREC/EDIFF/EDIFFG/IBRION/NSW/ISMEAR/ISPIN/MAGMOM 等、KPOINTS 类型与密度、POTCAR 元素）、提交与验证方式、脚本命令、风险与边界。
- 如需生成输入文件，调用 `scripts/gen_inputs.py`（见下）。
- 本机已有 POTCAR 库时：`python scripts/gen_inputs.py -s <结构文件> -w opt --potcar-root <POTCAR库> --subdir` 在**结构文件同级目录**下建 `<结构文件名>_<流程>`（如 `Si.cif` + `-w opt` → `Si_opt/`）并写入 INCAR/KPOINTS/POSCAR/POTCAR；`--same-dir` 则直接写在结构文件同级目录（不建子目录）。每个元素的 POTCAR 变体由 `map.json`（`{"元素": "变体目录名"}`）决定——**技能已自带 `scripts/map.json`**，所以使用者通常**只需提供两个路径**（结构文件 + POTCAR 库），无需自备 map.json；探测顺序为「POTCAR 库内 → 库的上级 → 技能自带」，要换自己的选势方案时把自写的 map.json 放在 POTCAR 库旁（优先级更高）或用 `--map` 显式指定——**只有显式传 `--map` 时才会把该路径记入 INCAR 头的注释行**，用技能自带（或从库内探测到）的 map.json 不写这一行。已有同名文件默认拒绝覆盖，需显式 `--force`；多步流程（opt/scf/band）用 `--subdir` 分目录避免互相覆盖。生成的 INCAR **默认带 `ENCUT = 520`**（`--encut` 覆盖，`--no-encut` 省略该标签），整条流程共用同一值。
- COHP/COOP 成键分析走 `scripts/gen_lobsterin.py`（见资源），流程见 `references/workflows.md` 第十节。

读取时机：收到计算流程/输入文件生成请求时读取 `references/workflows.md`。

### 3. VASP 输出数据画图（结果可视化）

用户提供 VASP / LOBSTER 输出数据、想把结果画成图时：

- **常见画图目标与数据来源**：
  - 态密度 DOS / 分波 PDOS：`vasprun.xml`（或 `DOSCAR`）。
  - 能带结构：`vasprun.xml`（含高对称 k 路径时）。
  - 能量 / 力收敛曲线：`OSZICAR`（离子步自由能）、`OUTCAR`（电子步能量）。
  - COHP / ICOHP：`COHPCAR.lobster`（能量 0 为费米面；第 2/3 列平均 COHP/ICOHP，之后每两列一个原子对）。
  - 声子谱 / 晶格热导率：phonopy `band.yaml`/`mesh` 或 ALAMODE 输出；热导率 vs 温度。
  - AIMD 轨迹的动力学分析（RDF / RMSD / 速度自相关 VACF）：把轨迹转成含速度的 GROMACS `.gro` 后用 `gmx` 分析，流程见 `references/workflows.md` 第十一节。
  - 二维势能面（PES，如 GSFE）与最小能量路径（MEP）：三列数据（x、y、能量）→ 势能面图 + string 法自动找 MEP，流程见 `references/workflows.md` 第十二节。
  - 理想拉伸 / 剪切的应力应变曲线：`engineeringstressstrain.all` 与 `truestressstrain.all`（`idealdeform.sh` 产出）→ 应力应变图（单位 GPa），流程见 `references/workflows.md` 第十三节。
  - 外压迭代的收敛过程：`pressure.all`（`vaspeqstress.sh` 产出）→ 每步外压随迭代步的变化图，流程见 `references/workflows.md` 第十四节。
  - 差分电荷密度 / 平面平均差分：三个 `CHGCAR`（AB、A、B 同格子自洽）→ VESTA 等值面，或沿指定方向的平面平均曲线（横轴为格点数），流程见 `references/workflows.md` 第十五节。
  - 形变势法迁移率的拟合链：VBM/CBM（扣真空能级）vs 应变、总能量 vs 应变、Γ 附近能带拟合 `m*`，流程见 `references/workflows.md` 第十六节。
  - 弹性矩阵与各向异性模量：`OUTCAR` 的 `TOTAL ELASTIC` 块（单位 kBar，下标顺序需重排）→ 3D 杨氏模量曲面或 2D 极坐标 `E(φ)`/`ν(φ)`，流程见 `references/workflows.md` 第十八节。
  - STM 模拟：带分解电荷密度 `PARCHG`（`LPARD=.TRUE.` + `NBMOD=-3` + `EINT`）→ `vaspkit 325` 恒定高度图，流程见 `references/workflows.md` 第十九节。
  - 任意量的提取与出图：`re` 正则抓 `OUTCAR` → `pandas` 整理 → 画图 + CSV（通用配方见 `references/workflows.md` 第二十节）。
- ⚠️ **大文件不要读进上下文，改为生成画图脚本**：`vasprun.xml`（动辄几百 MB～数 GB）、`DOSCAR`、`CHGCAR` 这类大文件**不要**用 read/grep 读内容，也不要试图在对话里解析——既撑爆上下文又取不全。做法是**生成一个能在用户本机独立运行的 Python 脚本**，由用户自己跑；脚本把 PNG/SVG 与中间 CSV 写到磁盘，再据结果图解读。只有确实很小的文本（几 KB 的 `OSZICAR`、`COHPCAR.lobster`）才直接读。
- **脚本怎么写**：`vasprun.xml` / `DOSCAR` 走 pymatgen `DosPlotter` / `BSPlotter`（流式解析、不占内存）；文件很大时用 `iterparse` 或先转 JSON 只抽需要的部分，必要时改用 `DOSCAR` / `EIGENVAL` 兜底。收敛曲线、`COHPCAR.lobster` 等纯文本用 matplotlib 直接读。脚本要有 `--help` 和可配参数（输入文件、输出目录、能量范围、费米面平移），交付带单位与高对称点标注的高清 PNG/SVG。
- **关键约定**：能量轴单位 eV、费米面定为 0；COHP 常画 `-COHP`（成键朝右）；收敛图横轴为离子步 / 电子步；能带图标注高对称点。
- 出脚本前先确认输入文件的路径与格式；脚本落地后告诉用户运行命令（如 `python plot_dos_band.py --vasprun vasprun.xml --out figures/`）以及该看什么。

读取时机：收到「把 VASP/LOBSTER 输出数据画成图 / 可视化」请求时——默认产物是**一份可在本地运行的画图脚本**加一张结果图。
AIMD 轨迹分析（RDF / RMSD / VACF 等）类请求，读 `references/workflows.md` 第十一节。

### 4. 知识库与文章收录（支撑能力）

用户可能会陆续提供 VASP 使用的文章、教程、笔记或报错记录，用于沉淀为可检索的知识库。处理方式：

- **收录文章/链接**：当用户提供文章、教程、报错记录，或给出 **http(s) 链接**时，用
  `python scripts/add_article.py <文件或URL> [--tag "xx"] [--proxy <代理>]` 将其转成带元数据头的 markdown 存入 `references/articles/`（文件名带日期，自动避免覆盖）。链接会抓 HTML 正文并记录标题/作者/期刊/DOI/抓取时间；PDF（本地或链接）需要 `pypdf`；抓不到正文时（登录墙、Cloudflare、纯 JS 渲染）改用原 PDF 或另存文本再收录。
- **抓不到的站点**（需要登录态或强反爬）：**知乎**、`error.wiki`、腾讯文档等会返回 403 或验证页，补 `Referer`/浏览器头也无效。按站点选择路径：
  1. **微信公众号 / 普通博客**：直接 `add_article.py <URL>`（脚本的浏览器 UA 能过）；
  2. **知乎本人文章**：走知乎开放平台 CLI——`zhihu-cli me content --content-url "<知乎链接>"` 拿 JSON，取 `Data.Title`/`Data.Body` 包成 HTML，再 `add_article.py <本地html> --source-url "<原链接>"` 收录（`me content` 只读本人内容）；
  3. **其它被拦站点**：请用户粘贴正文，或另存网页（`Ctrl+S` → 仅 HTML）到工作区后按本地文件收录。
  收录脚本会保留 `<a href>` 为 markdown 链接、并把知乎的 `link.zhihu.com` 跳转还原成真实 URL。
  ⚠️⚠️ **收录前必须先查库（任何链接、不只是重发的）**：文章可能是**很久以前**收的，光看聊天记录判断不出来。收到链接后**先查其 URL 是否已在库里**：
  `grep -r "<原链接>" references/articles/`（或按标题/站点搜），**命中就直接引用既有提炼、不要重新抓取**；
  否则会出现 `…_2.md` 这样的重复文件。（本库确实发生过一次：一篇早期收录的文章被再次抓取。）
  ⚠️ **同一链接不要反复抓取**：微信对**重复访问**会返回「环境异常，完成验证后即可继续访问」的验证页
  （此时 `add_article.py` 与网页抓取都拿不到正文）。**一次抓好即入库**；用户重发同一链接时，
  先在 `references/articles/` 里核对该篇是否已存在，**不要重新抓取**；确需重收（作者改过正文）时请用户另存网页。
- **沉淀报错知识**：收录后通读文章，把其中有价值的报错/参数经验提炼补充进 `references/errors.md` 或 `references/workflows.md`（保持既有条目格式），避免知识只埋在文章里。
- **检索**：报错诊断时可随时用 `python scripts/search_kb.py "<关键词>"` 命中任意已收录文章的相关片段。
- 已收录文章可作为格式模板直接参照：示例「VASP 收敛参数速查」、LAPACK ZPOTRF/ZHEGV、VASP+LOBSTER COHP。

读取时机：用户提供 VASP 相关文章时；报错诊断/流程生成需要查阅既有文章时。

## 脚本：gen_inputs.py（生成 VASP 输入文件）

用 pymatgen（优先）或 ase 读取结构（POSCAR/CIF 等），按工作流生成 `INCAR`、`KPOINTS`、`POSCAR`，并按需生成 `POTCAR`。

```text
python scripts/gen_inputs.py -s <结构文件> -w <workflow> [选项]
```

- `-s/--structure`：结构文件（POSCAR、CIF、…）。
- `-w/--workflow`：`opt`（结构优化）| `scf`（静态自洽）| `band`（能带，自动用原胞生成高对称 k 路径）| `dos`（态密度）| `mag`（磁性，含 ISPIN/MAGMOM/混合参数）。
- 声子 / ALAMODE 位移构型计算属于普通 scf：对每个位移 POSCAR 用 `-w scf` 即可。
- 常用选项：`--outdir`（输出目录）、`--kdens`（自动网格密度，默认 2000）、`--encut`、`--prec`、`--ispin`、`--magmom`（如 `"Fe:5,Mn:4"`）、`--potcar`（POTCAR 文件，或含各元素 POTCAR 的目录，自动按 POSCAR 顺序拼接）、`--noncollinear`/`--soc`（磁性）、`--nbands`。

示例：

```text
python scripts/gen_inputs.py -s POSCAR -w opt
python scripts/gen_inputs.py -s structure.cif -w scf --kdens 3000 --encut 520
python scripts/gen_inputs.py -s POSCAR -w mag --magmom "Fe:5,Mn:4" --ispin 2
python scripts/gen_inputs.py -s POSCAR -w band --outdir band_run
python scripts/gen_inputs.py -s POSCAR -w scf --potcar /path/to/PAW_PBE
```

注意：

- 未提供 `--potcar` 时只写 `POTCAR.placeholder`（含拼接指引），需用户链接/复制真实 POTCAR。
- `band` 工作流会把结构转为原胞以保证干净的 k 路径，并在 INCAR 顶部注明——对应的 scf 也要在原胞上跑。
- 运行环境需装有 pymatgen 或 ase；脚本读不到结构时会提示激活相应 Python 环境（如 `conda activate <env>`）。

## 资源

- `scripts/README.md`：**脚本库索引与编写约定**——新增或查找脚本先读它；脚本按 `parse/`（输出解析）、`plot/`（画图）、`submit/`（提交与批处理）、`post/`（后处理）四个任务族收录，并标注依赖等级（L0 纯标准库 … L3 pymatgen/ase/phonopy）与典型命令。
- 画图能力：用 pymatgen `DosPlotter`/`BSPlotter` 与 matplotlib 读 VASP/LOBSTER 输出作图；`scripts/plot/` 是该类任务的落位处，脚本落地后按 README 索引复用，未落地时**按需生成独立的画图脚本**（不要把 `vasprun.xml`/`DOSCAR` 等大文件读进上下文）。
- `references/errors.md`：VASP 报错分类与定位（初始化 / SCF / 离子步 / 内存 / ALAMODE / LOBSTER / **二维介电-光学等静默错误** / **社区错误集精选（SGRCON、PRICEL、NMAX_DEG、HSE NaN…）** 等）+ 高频注意事项，顶部含目录与检索提示。
- `references/workflows.md`：各性质计算流程（opt/scf/band/dos/mag/声子/热导率/热电/高通量/**COHP 成键分析**/**AIMD 轨迹分析（VASP→GROMACS）**/**二维 PES 与 MEP（string 法）**/**理想拉伸-剪切（应力应变）**/**任意外压（vaspeqstress）**/**电荷密度可视化（总 / 差分 / 平面平均）**/**二维载流子迁移率（形变势）**/**弹性矩阵与各向异性杨氏模量**/**STM 模拟（VASPKIT）**/**波恩有效电荷与极化**/**Wannier90 紧束缚模型**/**AIMD 热稳定性验证**/**有效质量**/**杂化泛函（HSE06）能带**）+ 通用输出模板；第十七节指向 `tools.md`（外部脚本/工具速查），第十八节起依次为弹性矩阵、STM 模拟、OUTCAR 数据挖掘、ML 势数据集、SCPH 高温声子、波恩有效电荷、吸附能/迁移能垒、Wannier90 紧束缚模型、AIMD 热稳定性验证、有效质量、收敛性测试、杂化泛函（HSE06）能带。
- `references/onboarding.md`：**入门地图**——写给做实验、刚开始做计算的人：计算与实验的对应、三种运行环境与 VASP 授权提醒、四个输入文件、起步参数、常用数据源，以及到其它文档的导航。
- `references/potcar.md`：**POTCAR 使用与选势指南**——组装规矩（顺序/只读/禁改 `LEXCH`）、后缀官方定义、**按元素分区与按计算类型的选势建议**（第一行元素、碱土、d/p/f 区、GW/杂化、类氢与 `_2`/`_3` 势）、版本差异。
- `references/incar.md`：**INCAR 参数速查**——按「全局 / 电子步 / 离子步」分类的各参数含义与常用取值（`ISTART`/`ICHARG`/`ISMEAR`/`ISIF`/`IBRION`/`EDIFFG`/`POTIM`…），含原文笔误订正与库内交叉印证。
- `references/linux.md`：**Linux 常用命令速查**——面向 VASP 操作的文件/目录命令、`for`+`seq` 批量造目录、`sed -i` 就地改参数、通配符与引号、以及破坏性命令的安全习惯。
- `references/performance.md`：**运行效率与并行调优**——时间标度律（为什么降 `ENCUT` 最省时）、`LREAL`/`ALGO`/`NPAR`/`KPAR` 的取舍，以及「多个小作业优于一个大作业」的排队策略。
- `references/constants.md`：**物理常数与单位换算速查**——kBar/GPa、Bohr/Å、eV/Hartree、声子频率等换算集中备查（写参数、做后处理、核对单位时先看它）。
- `scripts/reference/README.md`：**参考脚本库索引**——从文章里**原样收集**的脚本（未验证、不保证可运行，仅供查阅）；要能跑的工具请看 `scripts/` 下的自带脚本。
- `references/tools.md`：**外部脚本与工具功能速查**——要「找有没有现成脚本 / 工具、它是干什么的、入口在哪」时先读它；收录第三方脚本（`chgdiff.pl`、`vtotav.f`、`idealdeform.sh`、`vaspeqstress.sh`、`mobility.sh`、`crecip.py`、`VASP2GRO`、`MEPSearcher`…）、外部程序（VASPKIT / VESTA / GROMACS）、自带 `scripts/` 一览与相关文献链接；新收录脚本或工具需在此登记。
- `references/articles/`：用户 VASP 文章知识库（已含：示例文章、LAPACK ZPOTRF/ZHEGV、VASP+LOBSTER COHP）。
- `scripts/gen_inputs.py`：VASP 输入文件生成脚本（需 pymatgen/ase）。`--potcar-root` + **自带的 `scripts/map.json`** 按 POTCAR 库选势变体（使用者只需给结构文件与 POTCAR 路径），`--subdir` 在结构文件同级目录下建 `<结构文件名>_<流程>` 子目录、`--same-dir` 直接就地写，已有输入文件需 `--force` 才覆盖；INCAR 默认 `ENCUT=520`（`--no-encut` 可省）；`--selftest` 自检。
- `scripts/map.json`：**POTCAR 选势映射**（`{"元素": "变体目录名"}`，83 项，PBE 口径）——`gen_inputs.py` 用它把 POSCAR 里的元素映射到 POTCAR 库中的变体目录（如 `Fe` → `Fe_pv`、`Yb` → `Yb_2`）。使用者无需自备；要换方案就在自己的 POTCAR 库旁放一份同名文件覆盖它。
- `scripts/gen_lobsterin.py`：生成 LOBSTER 的 lobsterin（COHP/COOP），含统计键长与按元素+键长写 `cohpGenerator`（需 pymatgen）。
- `scripts/search_kb.py`：全库关键词检索（纯标准库），报错定位与查阅文章用。
- `scripts/add_article.py`：把用户文章收录进 `references/articles/`——本地文件（txt/md/log/py/rst/html/pdf）或 **http(s) 链接**（HTML 转正文并抓题录，PDF 自动下载解析，支持 `--proxy`；纯标准库，pdf 需 `pypdf`）。

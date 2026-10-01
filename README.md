<!-- README_SYNC: source=working-tree; updated=2026-10-01 -->

<h1 align="center">vasp.skill</h1>

<p align="center">
  <strong>不只替你写 INCAR，更帮你看懂报错、走通流程、把结果画成图。</strong>
</p>

<p align="center">
  面向计算材料科研的 VASP 工作流助手，<br>
  把「报错诊断 → 流程与输入文件生成 → 输出数据画图 → 知识沉淀」串成一条可执行的链路。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/skill-vasp--skill-blue.svg" alt="Skill">
  <img src="https://img.shields.io/badge/knowledge%20base-95%20articles-green.svg" alt="Knowledge base">
  <img src="https://img.shields.io/badge/workflows-40%20sections-important.svg" alt="Workflows">
  <img src="https://img.shields.io/badge/deps-pymatgen%20%7C%20matplotlib-orange.svg" alt="Deps">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</p>

<p align="center">
  如果它替你省下过一次通宵排查，欢迎把它分享给同组还在手写 INCAR 的人。
</p>

VASP 的坑很少写在参数表里，而是藏在「这一步为什么错、该看哪个文件的哪一行」。vasp.skill 不会只丢给你一段 INCAR：它先判断报错发生在哪个阶段，再告诉你改哪个文件的哪个参数、重跑之后怎么确认；要算新性质时给完整流程；拿到输出数据时直接把图交付。它不是另一个参数速查表，而是一套覆盖「诊断—计算—分析—沉淀」全周期、能解释结论来源的工作流助手。

它也不假装什么都知道：命中的知识库条目会说明出处，命不中的会说命不中，然后按「阶段定位 → 成因分类 → 排查」给出结构化方案，而不是硬套一个模板。

## 它能帮你解决什么

| 你遇到的问题 | vasp.skill 会怎么帮 |
| --- | --- |
| 粘来一段 OUTCAR / stdout 报错 | 先定位阶段（初始化 / SCF / 离子步 / 后处理 / 编译），再给成因和可执行的改法，并说明重跑后看什么确认 |
| 想算结构优化、能带、DOS、声子、热导率、热电…… | 给完整流程：先后步骤、每步关键参数表、KPOINTS 密度、POTCAR 元素、提交与验证方式 |
| 手上只有结构文件，要凑齐四个输入文件 | 直接生成 `INCAR` / `KPOINTS` / `POSCAR` / `POTCAR`，可按本机 POTCAR 库与 `map.json` 自动选势变体 |
| 有 `vasprun.xml` / `DOSCAR` / `OUTCAR` / `COHPCAR.lobster` 想看图 | 出 DOS / 能带 / 收敛曲线 / COHP / 热导率等高清图，坐标与单位标清 |
| 算完不知道体系是金属还是半导体 | 用 `EENTRO / 原子数` 判断，并给出该换的 `ISMEAR` 与 `SIGMA` |
| 论文算例参数看不出来、教程看完就忘 | 收录进知识库并提炼进 `errors.md` / `workflows.md`，之后关键词一搜就能命中 |
| 单位、常数、Linux 命令记不住 | `constants.md` 换算表与 `linux.md` 命令速查，写参数、做后处理时随手查 |

## 三大能力

### 一、报错诊断：先定位阶段，再谈改哪个参数

收到 OUTCAR 片段、stdout 或错误消息时，按 `references/errors.md` 的诊断流程走：确认版本与运行方式 → 判断报错阶段 → 区分致命错误与警告 → 用报错里的稳定关键词匹配错误分类。

- 覆盖 **8 大类**：读入与初始化、SCF 电子自洽、离子步、运行环境与编译、ALAMODE、LOBSTER/COHP、高频注意事项、社区错误集精选（SGRCON、PRICEL、NMAX_DEG、HSE NaN、LAPACK ZPOTRF/ZHEGV…）
- 目录里没直接命中时，先跑 `python scripts/search_kb.py "<关键词>"` 全库检索 —— 它同时查 `errors.md`、`workflows.md` 和 95 篇收录文章，返回命中文件、行号与上下文
- 输出固定包含：**定位 + 成因 + 可执行方案 + 改哪个文件哪个参数 + 重跑后如何确认**

### 二、流程与输入文件生成

说清想算的性质，按 `references/workflows.md` 的「流程选择」判断主流程（优化 → 静态自洽 → 属性），并给出到位的参数表，而不是一串默认值。

`gen_inputs.py` 支持 5 类流程：`opt`（结构优化）、`scf`（静态自洽）、`band`（能带，自动用原胞生成高对称 k 路径）、`dos`（态密度）、`mag`（磁性，含 `ISPIN`/`MAGMOM`/混合参数）。所有流程**默认共用 `ENCUT = 520 eV`** —— 中途改这个值会让 FFT 网格变化、上一步的 `CHGCAR` 维数对不上。

```text
python scripts/gen_inputs.py -s structure.cif -w opt --potcar-root /path/to/PBE --subdir
#  → structure_opt/{INCAR,KPOINTS,POSCAR,POTCAR}
```

### 三、输出数据画图

拿到输出文件就能出图，并按约定统一：能量轴单位 eV、费米面定为 0、COHP 常画 `-COHP`（成键朝右）、收敛图横轴为离子步/电子步、能带图标高对称点。

已覆盖：DOS / 分波 PDOS、能带、能量与力的收敛曲线、COHP / ICOHP、声子谱与晶格热导率、AIMD 轨迹分析（RDF / RMSD / VACF）、二维势能面与 MEP、应力应变曲线、外压迭代收敛、差分电荷与平面平均、形变势法迁移率、弹性矩阵与各向异性杨氏模量、STM 模拟、任意量的正则提取出图。

### 四、知识库与文章收录（支撑能力）

把文章、教程、报错记录沉淀成可检索的知识库：`add_article.py` 支持本地文件与 http(s) 链接（HTML 正文转 markdown 并抓题录，PDF 自动解析）。收录之后**必须回填**：把可复用的报错与参数经验提炼进 `errors.md` / `workflows.md`，别让知识只躺在文章里。

## 一套可检索的知识库

| 文档 | 内容 |
| --- | --- |
| `references/errors.md` | 报错分类与定位 + 诊断流程 + 高频注意事项 + 社区错误集精选 |
| `references/workflows.md` | **40 节**计算流程：opt/scf/band/dos/mag、声子、热导率、热电、COHP、AIMD、PES/MEP、应力应变、外压、电荷密度、迁移率、弹性、STM、波恩有效电荷、Wannier90、DFT+U、Berry phase、居里温度、SOC、约束磁矩、光学性质、TDEP、HSE06、U 值线性响应…… |
| `references/onboarding.md` | 入门地图：计算与实验的对应、三种运行环境、VASP 授权提醒、四个输入文件、起步参数 |
| `references/incar.md` / `potcar.md` | INCAR 参数速查（按全局/电子步/离子步分类）；POTCAR 组装规矩与按元素分区的选势建议 |
| `references/linux.md` / `performance.md` / `constants.md` | 命令速查；时间标度律与 `LREAL`/`ALGO`/`NPAR`/`KPAR` 取舍；单位换算集中备查 |
| `references/tools.md` | 外部脚本与工具功能速查（VASPKIT / VESTA / GROMACS、`idealdeform.sh`、`vaspeqstress.sh`、`chgdiff.pl`…） |
| `references/articles/` | **95 篇**收录文章，带来源 URL、抓取时间与题录 |

## 内置脚本

| 脚本 | 任务 | 依赖 |
| --- | --- | --- |
| `scripts/gen_inputs.py` | 生成 VASP 输入文件（opt/scf/band/dos/mag）；`--potcar-root` + `map.json` 自动选势变体；`--subdir` / `--same-dir` 控制落盘位置；已有文件需 `--force` 才覆盖 | L3 |
| `scripts/gen_lobsterin.py` | 生成 LOBSTER 的 `lobsterin`（COHP/COOP、统计键长） | L3 |
| `scripts/search_kb.py` | 全库关键词检索（报错定位、文章查阅） | L0 |
| `scripts/add_article.py` | 收录文章：本地文件或 http(s) 链接，PDF 需 `pypdf` | L0 |
| `scripts/parse/` | `OSZICAR` / `OUTCAR` / `COHPCAR.lobster` → CSV / JSON，机器可读优先 | L0 |
| `scripts/reference/` | 从文章里**原样收集**的 31 个参考脚本（未验证，仅供查阅） | — |

脚本库约定（命名、`--selftest`、依赖分级、退出码）见 [`scripts/README.md`](scripts/README.md)。

## 安装

把 `vasp-skill/` 整个目录放进 DSH 的技能根目录即可 —— 用户级 `~/.dsh/skills/`（对所有工作区生效），或项目级 `<项目根>/.dsh/skills/`（只在该项目生效，且优先级更高）。

装好后可以直接说：

```text
请使用 vasp.skill 帮我诊断下面这段报错：<粘贴 OUTCAR / stdout>
请使用 vasp.skill 给出 Ag3SbS3 的结构优化 → 能带 → DOS 完整流程和输入文件。
请使用 vasp.skill 把这批 vasprun.xml 画成 DOS 和能带图。
```

> ⚠️ **目录名与 frontmatter 的 `name` 必须是 kebab-case**（本 skill 用 `vasp-skill`）。
> 写成含点的 `vasp.skill` 会被 DSH 拒绝加载，skill 根本不会出现在会话的可用列表里。
> `vasp.skill` 是本项目的**对外展示名**，`vasp-skill` 是它的**技能标识符**。

**依赖**：Python 3.8+（`search_kb.py`、`add_article.py` 纯标准库）；`gen_inputs.py` 需要 pymatgen 或 ase；画图需要 matplotlib；可选 `pypdf`（PDF 收录）。外部工具 VASPKIT / VESTA / phonopy / ALAMODE / GROMACS 按需自备。

**先看 `example/`**：里面有一套可直接对照的最小样例 —— `Si.cif` / `Ag3SbS3.cif` 两个输入结构，以及用 `gen_inputs.py -w opt --subdir` 生成的 `Si_opt/`、`Ag3SbS3_opt/`。复现方式：

```text
python scripts/gen_inputs.py -s example/Si.cif -w opt --potcar-root <你的POTCAR库> --subdir
```

**关于 POTCAR**：样例目录里的 `POTCAR` 是在本机用 `--potcar-root` 从本地势库拼出来的。POTCAR 版权归 VASP 官方，**若要分享或上传本 skill，请先删掉这些 `POTCAR` 文件**，让使用者自己用 `--potcar-root` 重新生成。有本机势库时用 `--potcar-root` 指向它，并在库里或其上级放一份 `map.json`（`{"元素": "变体目录名"}`）。

## 一次典型请求是怎么走完的

```text
用户粘贴报错 / 描述要算的性质 / 上传输出文件
  → 判断请求类型（诊断 / 流程 / 画图 / 收录）
  → 只加载当前任务必需的 1~3 份资料，不整库灌入上下文
        · 报错 → references/errors.md；命不中 → search_kb.py 全库检索
        · 流程 → references/workflows.md 对应章节
        · 画图 → 对应输出文件的解析与绘图配方
  → 给出定位 / 参数表 / 图，并说明怎么验证
  → 有新知识就沉淀回 errors.md / workflows.md 与 scripts/
```

## 项目结构

```text
vasp-skill/
├── SKILL.md                     # 行为与路由内核：何时读哪个文件、何时跑哪个脚本
├── README.md                    # 本文件
├── LICENSE                      # MIT 许可证全文
├── example/                     # 开箱即用的最小样例
│   ├── Si.cif / Ag3SbS3.cif     # 输入结构
│   ├── Si_opt/                  # 对应的 opt 输入文件（INCAR/KPOINTS/POSCAR/POTCAR）
│   └── Ag3SbS3_opt/
├── references/
│   ├── errors.md                # 报错分类与定位（8 大类 + 诊断流程）
│   ├── workflows.md             # 40 节计算流程
│   ├── onboarding.md            # 入门地图（写给做实验、刚上手计算的人）
│   ├── incar.md / potcar.md     # 参数速查 / 选势指南
│   ├── linux.md / performance.md / constants.md / tools.md
│   └── articles/                # 文章知识库（95 篇，可检索）
└── scripts/
    ├── README.md                # 脚本库索引与编写约定
    ├── gen_inputs.py            # 生成 INCAR/KPOINTS/POSCAR/POTCAR     [L3]
    ├── gen_lobsterin.py         # 生成 LOBSTER 的 lobsterin            [L3]
    ├── search_kb.py             # 全库关键词检索                       [L0]
    ├── add_article.py           # 收录文章（本地文件 / http(s) 链接）  [L0]
    ├── parse/                   # OSZICAR / OUTCAR / COHPCAR 解析
    └── reference/               # 参考脚本库（31 个，未验证）
```

## 设计原则

1. **先定位阶段，再谈参数。** 「SCF 不收敛」和「离子步不收敛」是两类问题，给的方案完全不同。
2. **给可执行的下一步，不给参数堆砌。** 每条建议都要落到「改哪个文件哪个参数」和「重跑后看什么确认」。
3. **命不中就说命不中。** 知识库没有覆盖的场景按通用路径给结构化方案，不假装有出处。
4. **机器可读优先。** 解析脚本默认输出 CSV/JSON，画图脚本交付带单位的 PNG/SVG，便于二次处理和复现。
5. **不做隐式修改。** 脚本默认只读输入、只写自己的输出目录；不删除、不覆盖正在跑的计算文件。
6. **知识必须回填。** 收录文章不算完成，提炼进 `errors.md` / `workflows.md` 才算。
7. **谨慎对待「收敛」。** 弛豫要在一个离子步内收敛；给了固定原子就要把固定原子排除后再判力收敛；大体系 `0.02~0.05 eV/Å` 足矣。

## 版本记录

| 日期 | 类型 | 更新 | 用户价值 |
| --- | --- | --- | --- |
| 2026-10-01 | 更名与文档 | skill 由 `vasp-workflow` 更名为 `vasp-skill`（对外展示名 `vasp.skill`）；新增本 README，补齐能力、知识库、脚本与安装说明。 | 名称与文档对齐；新用户在安装前就能看清能力边界、脚本入口和 kebab-case 命名约束。 |
| 2026-10-01 | 协议 | 新增 `LICENSE`（标准 MIT 全文）与 README「开源协议」一节，并注明第三方收录内容不在 MIT 范围内。 | 明确授权范围：允许商业使用、修改与分发，分发时保留版权与许可声明。 |

## 使用边界

- 需要合法的 VASP 授权。本 skill **只负责生成输入文件、解读输出与出图**，不代替你对科学问题做判断。
- 报错诊断基于 `references/errors.md` 与 95 篇收录文章。VASP 各版本行为存在差异，命中的条目仍需结合你的实际输出现场核对。
- 本目录不含任何 VASP 官方文件（`POTCAR` 等），也不含计算数据。
- 参数建议是**起点而非结论**：`ENCUT`、k 点密度、`SIGMA` 等应针对你的体系做一次收敛性测试（见 `workflows.md` 第二十八节）。

## 参与共建

- **补文章**：`python scripts/add_article.py <URL 或本地文件> --tag "xx"`，收录后把可复用的经验回填进 `errors.md` / `workflows.md`。
- **补脚本**：先读 `scripts/README.md` 的编写约定（命名、`--selftest`、依赖分级、退出码），落地后在该文件的表格里登记一行。
- **纠错**：`errors.md` / `workflows.md` 里的条目若与你的实测不符，欢迎带着 `OUTCAR` 片段来改。

## 开源协议

本项目采用 [MIT License](LICENSE)，允许商业使用、修改与分发；分发时须保留版权与许可声明。

**适用范围**：MIT 仅覆盖本 skill 自身的代码与文档（`SKILL.md`、`README.md`、`scripts/` 下的自带脚本、`references/` 下的自撰文档）。`references/articles/` 收录的文章与 `scripts/reference/` 收集的第三方脚本**版权归各自原作者**，不在 MIT 范围内，对外分发前请自行核实其授权。

**免责声明**：本项目提供 VASP 计算工作流与报错诊断支持，不替代你对科学问题的独立判断；不附带任何 VASP 官方文件（`POTCAR` 等），使用者需自行取得合法的 VASP 授权与赝势。

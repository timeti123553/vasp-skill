# vasp.skill 脚本库

这里是本 skill 的**脚本库索引**：按任务族收录可复用的 VASP / LOBSTER 脚本。
`SKILL.md` 只回答「什么时候用哪个脚本」，具体参数、依赖、实现细节都在本文件与各脚本 docstring 里查。
**新增脚本前先读本文件，新增后必须在本文件的表格里登记一行。**

## 一、编写约定

1. **命名**：`<动词>_<对象>.py`，如 `gen_inputs.py`、`parse_oszicar.py`、`plot_dos.py`、`submit_slurm.py`。
2. **自解释**：必须有模块级 docstring（用途 / 输入 / 输出 / 依赖 / 示例命令），必须支持 `--help`。
3. **自带自检**：每个脚本必须支持 `--selftest`（内嵌合成样例 + 断言关键数值，退出码 0/1），便于任何机器上随时复验。
4. **机器可读优先**：解析类脚本默认输出 CSV 或 JSON（便于二次画图与批处理），用 `--out` 指定输出目录，默认当前目录。
5. **依赖分级**：docstring 首行标 `Deps: L0|L1|L2|L3`。
6. **退出码**：`0` 成功；`1` 运行正常但没有可解析内容 / 未命中（**不是崩溃**）；`2` 参数错误、文件不存在或依赖缺失。
7. **不做隐式修改**：脚本默认只读输入、只写自己的输出目录；不删除、不覆盖已有 VASP 输出文件。

## 二、依赖分级

| 级别 | 依赖 | 说明 |
| --- | --- | --- |
| `L0` | 仅 Python 标准库（3.8+） | 任何环境可跑，优先考虑 |
| `L1` | numpy | 数值汇总 |
| `L2` | numpy + matplotlib | 出图（交付 PNG/SVG，标注单位与费米面） |
| `L3` | pymatgen / ase / phonopy / pypdf | 结构读写、k 路径、声子、PDF 解析 |

## 三、目录结构

```text
scripts/
├── README.md          ← 本文件：索引 + 约定
├── gen_inputs.py      ← 生成 INCAR / KPOINTS / POSCAR(/POTCAR)，可读 map.json 选 POTCAR 变体 [L3]
├── map.json           ← POTCAR 选势映射（元素 → 变体目录名，83 项 PBE 口径），随技能分发 [数据]
├── gen_lobsterin.py   ← 生成 LOBSTER 的 lobsterin（COHP/COOP）      [L3]
├── search_kb.py       ← 全库关键词检索（errors/workflows/articles） [L0]
├── add_article.py     ← 收录文章（本地文件或 http(s) 链接）进 references/articles/ [L0]
├── reference/         ← **参考脚本库**：从文章里原样收集的脚本（未验证，仅供查阅）
├── parse/             ← 输出解析：已落地 OSZICAR / OUTCAR / COHPCAR
├── plot/              ← 画图（规划位）：DOS / 能带 / 收敛 / COHP / 热导率
├── submit/            ← 提交与批处理（规划位）：Slurm / PBS / 批量状态
└── post/              ← 后处理与衍生量（规划位）：键长配位、收敛判定、能垒
```

> ⚠️ **大文件画图不要内联**：`vasprun.xml`（几百 MB～数 GB）、`DOSCAR`、`CHGCAR` 不要用 read/grep 读进上下文——既撑爆上下文又取不全。`plot/` 里落库的是**可复用**的画图脚本；一次性需求直接**按需生成独立脚本**交给用户本地运行，脚本把 PNG/SVG 与中间 CSV 落盘，再据结果图解读。

## 四、已收录并跑通的脚本

`--selftest` 覆盖情况：`gen_inputs.py`、`search_kb.py`、`add_article.py` 与 `parse/` 三项均已支持；
**`gen_lobsterin.py` 尚未补 `--selftest`**。`parse/` 三项已用 **Python 3.12.14** 跑通自检（内嵌合成样例 + 端到端写出文件），
`gen_inputs.py --selftest` 的 L0 部分（map.json、POSCAR 元素序、POTCAR 拼接、覆盖守卫）任何环境可跑，端到端部分需 pymatgen；
合成样例验证的是解析逻辑与 CLI 契约，**真实输出的格式变体建议首次使用时复核一次**。

| 脚本 | 任务 | 依赖 | 典型命令 |
| --- | --- | --- | --- |
| `gen_inputs.py` | 生成 VASP 输入文件（opt/scf/band/dos/mag，默认 `ENCUT=520`）；`--potcar-root` + `map.json` 自动选 POTCAR 变体 | L3 | `python scripts/gen_inputs.py -s POSCAR -w opt --outdir opt_run` |
| `gen_lobsterin.py` | 生成 lobsterin（COHP/COOP、统计键长） | L3 | `python scripts/gen_lobsterin.py --struct POSCAR --list-bonds` |
| `search_kb.py` | 全库关键词检索（报错定位、文章查阅） | L0 | `python scripts/search_kb.py "ZPOTRF"` |
| `add_article.py` | 收录文章：本地文件（txt/md/log/py/rst/html/pdf）或 **http(s) 链接**（HTML 转正文并抓题录，PDF 链接自动下载解析） | L0（PDF 需 pypdf） | `python scripts/add_article.py https://example.org/post --tag COHP` |
| `parse/parse_oszicar.py` | OSZICAR → 离子步 / 电子步 / MD 步收敛数据（CSV，`--json` 另出 JSON） | L0 | `python scripts/parse/parse_oszicar.py OSZICAR --out results --json` |
| `parse/parse_outcar.py` | OUTCAR → 关键参数、最终能量、最大/平均受力、警告与致命行（JSON，`--forces` 出力 CSV） | L0 | `python scripts/parse/parse_outcar.py OUTCAR --out results --forces` |
| `parse/parse_cohpcar.py` | COHPCAR.lobster → 能量 / 平均 COHP / ICOHP（CSV，`--pairs` 出逐键列） | L0 | `python scripts/parse/parse_cohpcar.py COHPCAR.lobster --out results --pairs` |

### 各脚本输出的字段

- **`parse_oszicar.py`** → `oszicar.csv`：`kind`（electronic/ionic/md）、`ionic_step`、`elec_step`、`algo`、`E`、`dE`、`d_eps`、`ncg`、`rms`、`rms_c`、`F`、`E0`、`dE_ionic`、`mag`、`T`、`S`。**不做收敛判定**，只提取数值；收敛判断交给 `post/check_convergence.py` 或人。
- **`parse_outcar.py`** → `outcar_summary.json`：`version` / `prec` / `encut_ev` / `ediff` / `ediffg` / `ispin` / `nkpts` / `nbands` / `nions` / `nelect` / `potcar_titels` / `toten_ev`（取最后一次） / `energy_sigma0_ev` / `reached_required_accuracy` / `elapsed_sec` / `max_force_ev_ang` / `mean_force_ev_ang` / `total_drift` / `total_magnetization`（`tot` 行最后一个数） / `warnings` / `fatal_hint_lines`（LAPACK、VERY BAD NEWS、DENTET 等）。取不到的字段写 `null`，不猜。
- **`parse_cohpcar.py`** → `cohp.csv`：`energy` + 每个自旋的 `avg_cohp[_up|_dn]`、`avg_icohp[_up|_dn]`；加 `--pairs` 时追加 `pairNN_cohp*`、`pairNN_icohp*`。布局按表头 `No. of COHP pairs` / `No. of spins` 解析，表头缺失时由列数推导，**推导不出就在 stdout 明说 `unknown layout`，不硬套**。

### 用本机 POTCAR 库就地生成输入文件（`--potcar-root` + `map.json`）

适合「结构文件在一个目录、POTCAR 库在另一个目录、想直接在结构同级目录开算」的场景。**使用者只需提供两个路径**（结构文件 + POTCAR 库）——选势方案由技能自带的 `map.json` 决定：

```text
python scripts/gen_inputs.py -s <结构文件> -w <流程> --potcar-root <POTCAR库> [--map <map.json>] [--subdir [NAME] | --same-dir] [--force]
```

- `--potcar-root`：POTCAR 库根目录，其下每个变体一个子目录（`PBE/Si/POTCAR`、`PBE/Fe_pv/POTCAR`…）。
- `--map`：`{"元素": "变体目录名"}` 的 JSON。**技能自带 `scripts/map.json`**（83 项，PBE 口径，如 `Fe`→`Fe_pv`、`Yb`→`Yb_2`），所以一般不用给；探测顺序为「`<库>/map.json` → `<库的上级>/map.json` → **技能自带 `scripts/map.json`**」。要换自己的选势方案，把自写的 map.json 放在 POTCAR 库旁（优先级更高），或用 `--map` 显式指定——**只有显式传 `--map` 时才会把该路径写进 INCAR 头的注释行**，用技能自带或从库内探测到的 map.json 不写这一行。
- `--subdir`：在结构文件同级目录下建 `<结构文件名>_<流程>` 子目录（`Si.cif` + `-w opt` → `Si_opt/`；`POSCAR` → `POSCAR_opt/`），四个输入文件写进去。可跟自定义名：`--subdir my_run`。**多步流程（opt/scf/band）推荐用它分目录**，否则共用一个目录会互相覆盖。
- `--same-dir`：直接把 INCAR / KPOINTS / POSCAR / POTCAR 写在结构文件同级目录（不建子目录）。
- `--outdir`：显式指定任意输出目录。`--outdir` / `--same-dir` / `--subdir` **三者只能选一个**。
- `--force`：目标目录已有这四个文件时默认**报错拒绝**，加 `--force` 才覆盖（避免毁掉正在跑的计算）。
- `--encut`：**默认 520 eV**（脚本常量 `DEFAULT_ENCUT`），opt/scf/band/dos/mag 共用同一值——中途改动会让 FFT 网格变化、上一步的 `CHGCAR` 维数对不上（见 `errors.md` §8.24）。用 `--encut <值>` 覆盖；`--no-encut` 则完全不写该标签，由 VASP 取 POTCAR 的 `ENMAX`。
- POTCAR 按**写出的 POSCAR** 里的元素顺序拼接（不是按结构对象顺序），元素缺 map 条目或变体目录不存在都会明确报错并列出可用变体；所选 POTCAR 的 `LEXCH` 不一致时向 stderr 告警（混用 GGA 与 GW 势会静默算错）。
- 结构文件本身就是 `POSCAR` 且用 `--same-dir` 时，**不覆盖该输入文件**，只补 INCAR / KPOINTS / POTCAR。
- 路径都来自命令行，**不写死在脚本里**，换机器时由使用者自己给。

## 五、规划中的脚本（按任务族）

`planned` = 尚未编写；`ready` = 已跑通。

| 族 | 脚本 | 任务 | 依赖 | 状态 |
| --- | --- | --- | --- | --- |
| parse | `parse_doscar.py` | DOSCAR → 总 DOS / 分波 PDOS CSV（含 E_F） | L0 | planned（最好先有真实 DOSCAR 样例） |
| parse | `parse_vasprun.py` | vasprun.xml → 能量、费米能、带隙、DOS 摘要（iterparse，抗大文件） | L0 | planned（最好先有真实 vasprun.xml 样例） |
| parse | `parse_eigenval.py` | EIGENVAL → 能带数据（无 pymatgen 时的兜底） | L0 | planned（最好先有真实 EIGENVAL 样例） |
| plot | `plot_convergence.py` | OSZICAR / CSV → 能量、力收敛曲线 | L2 | planned |
| plot | `plot_dos.py` | DOSCAR / vasprun.xml → DOS / PDOS 图（费米面归零） | L2 | planned |
| plot | `plot_band.py` | vasprun.xml / EIGENVAL → 能带图，标注高对称点与带隙 | L2 | planned |
| plot | `plot_cohp.py` | COHPCAR.lobster → −COHP 图（成键朝右） | L2 | planned |
| plot | `plot_thermal.py` | ALAMODE / phonopy 输出 → 热导率 vs 温度 | L2 | planned |
| plot | `plot_pes.py` | 三列数据（x, y, E）→ 二维势能面热图，可叠加初始路径与 MEP | L2 | planned |
| post | `check_convergence.py` | 批量扫描目录：作业是否完成、是否收敛、给出理由 | L0 | planned |
| post | `bond_lengths.py` | POSCAR/CONTCAR → 键长与配位统计 | L3 | planned |
| post | `neb_barrier.py` | NEB / CI-NEB 能垒提取 | L0 | planned |
| submit | `submit_slurm.py` | 生成 Slurm 提交脚本（module / conda / vasp_std / 核数） | L0 | planned |
| submit | `submit_pbs.py` | 生成 PBS 提交脚本 | L0 | planned |
| submit | `ideal_deform.py` | 生成准静态应变序列（应变矩阵 POSCAR + `ISIF=4`/`OPTCELL` + 提交脚本） | L3 | planned |
| submit | `eq_stress.py` | 迭代施加任意外压（读 `OUTCAR` 应力 → 胡克定律更新 POSCAR → 重提交） | L0 | planned |
| post | `stress_strain.py` | 各应变步的 OUTCAR 应力 → 工程/真实应力应变曲线 CSV（作图另需 matplotlib） | L0 | planned |
| post | `chgdiff.py` | `CHGCAR` 差分（`Δρ = AB − A − B`）+ 平面平均曲线，替代 `chgdiff.pl` + `vtotav.f`（无需 Perl/Fortran） | L0 | planned |
| post | `effmass.py` | 能带数据 → 沿指定路径二次拟合有效质量 `m*`（以 m₀ 为单位） | L0 | planned |
| post | `mobility_dp.py` | 形变势法二维迁移率：`m*`、`E₁`、`C₂D` → μ（含 Hartree 单位换算） | L0 | planned |
| post | `elastic.py` | 读 `OUTCAR` 弹性矩阵 → 下标重排 + kBar/GPa 与 2D(N/m) 换算 → 各向异性 `E`/`ν`（3D 曲面 / 2D 极坐标；重排与换算为 L0，出图需 matplotlib） | L2 | planned |
| post | `stm_frames.py` | 裁剪 `vaspkit` 输出的 `STM_*.jpg` 白边，并按高度标注合成 `STM_animation.gif` | L2（Pillow） | planned |
| post | `outcar_grep.py` | 按用户给的正则从 `OUTCAR`/`OSZICAR` 批量提取任意量 → CSV（可选出图） | L0（出图需 matplotlib） | planned |
| post | `snap_dataset.py` | 从多帧 `vasprun.xml` 逐帧导出 ML 势数据集（能量/晶格/位置/受力/应力 → SNAP JSON，含单位声明；用 iterparse 而非行偏移） | L0 | planned |
| submit | `batch_status.py` | 批量目录的作业状态与收敛总览 | L0 | planned |

## 六、收录外部链接（文章 / 教程 / 报错记录）

```text
python scripts/add_article.py <URL> [--tag "xx"] [--proxy http://127.0.0.1:7890] [--timeout 30]
```

- **HTML 页面**：用标准库 `html.parser` 转成 markdown 风格正文（丢弃 script/style/nav/header/footer/form），并抓取 `citation_*` / `description` 等 meta 作为题录（标题、作者、期刊、年份、DOI）。
- **PDF 链接**：先下载到临时文件，再用 `pypdf` 抽取文字；缺 `pypdf` 时给出安装提示。
- **代理**：默认走环境变量 `http_proxy` / `https_proxy` / `all_proxy`，`--proxy` 显式覆盖（走 Clash 一类客户端时通常是 `http://127.0.0.1:7890`）。
- **落盘**：`references/articles/<日期>-<slug>.md`；文件头记录真实来源 URL、抓取时间与题录，便于日后追溯与引用；同名不覆盖，自动加 `_2`、`_3`。
- **收录之后必须沉淀**：通读正文，把可复用的报错与参数经验补进 `references/errors.md` 或 `references/workflows.md`（保持既有条目格式），别让知识只躺在文章里。
- **抓不到正文时**：改用原文 PDF、arXiv 摘要页，或手工另存为 txt/md 再收录——登录墙、Cloudflare、纯 JS 渲染的页面拿不到正文。
- 收录后立刻可检索：`python scripts/search_kb.py "<关键词>"`。

## 七、与其它部分的关系

- **`SKILL.md`**：只做"何时读哪个文件、何时跑哪个脚本"的路由；脚本的参数细节走本文件。
- **`search_kb.py`**：会扫描 `scripts/**/*.py`（含子目录），所以**脚本的 docstring 也是可检索知识**——报错诊断时用关键词能直接搜到相关脚本的做法与参数经验。
- **`references/errors.md` / `references/workflows.md`**：报错与流程正文；脚本是它们的可执行落点。
- **知识沉淀**：从文章里提炼出的"某任务该跑什么脚本、参数怎么给"，应同时更新本节表格与 `references/*.md` 对应条目，避免只埋在文章里。

## 八、新增脚本清单（自查）

- [ ] 文件名符合 `<动词>_<对象>.py`，docstring 含 `Deps:` 与示例命令
- [ ] `--help` 可用，`--out` 生效，退出码符合约定
- [ ] `--selftest` 存在且通过；条件允许时再补一次真实数据端到端运行，并写明验证所用文件
- [ ] 在**第四节**登记一行（已跑通）或在**第五节**登记（未跑通）
- [ ] 若脚本对应某个 SKILL.md 能力，在 `SKILL.md` 的资源节加一行指路

## 九、参考脚本库（`reference/`）

`reference/` 与上面的自带脚本**定位不同**，别混用：

| | 自带脚本（本 README 第四/五节） | 参考脚本库（`reference/`） |
| --- | --- | --- |
| 来源 | 自己写 | **从文章里收集**（保留原作者与出处） |
| 要求 | 必须带 `--selftest` 且跑通 | **不验证、不保证可运行** |
| 用途 | 直接调用 | 查逻辑、查参数、看别人怎么做 |
| 索引 | 本文第四节 / 第五节 | `reference/README.md` |

收录规则与完整索引见 [`reference/README.md`](reference/README.md)；脚本的**功能说明**统一登记在 `references/tools.md`，这里只放源码文本。

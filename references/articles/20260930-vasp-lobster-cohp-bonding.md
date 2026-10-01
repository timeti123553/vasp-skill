# VASP+LOBSTER 计算晶体轨道布居 COHP 定量衡量成键强度

- 来源文件: `zhuanlan.zhihu.com/p/668003243`（知乎专栏，作者 ma-yuan-94-83，218 赞同）
- 收录日期: 2026-09-30
- 标签: COHP, COOP, LOBSTER, 成键分析, 晶体轨道, ICOHP

---

## 背景

在做高压结构预测等研究时，新结构需要分析成键方式，除 ELF（电子局域函数）外，常用 COHP（晶体轨道哈密顿布居数，Crystal Orbital Hamilton Populations）定量衡量成键强度。本文给出 VASP+LOBSTER 的完整流程。

## 原理要点

- **COOP**（Crystal Orbital Overlap Population）：用重叠函数对 DOS 加权。**成键态为正、反键态为负**。
- **COHP**（Crystal Orbital Hamilton Populations）：用哈密顿矩阵的非对角元（hopping）对 DOS 加权。**成键态为负、反键态为正**。
- 因此文献常把横坐标画成 **-COHP**，使成键态（正）朝右、反键态（负）朝左，观感与 COOP 一致。注意 COOP 与 -COHP 之间**没有直接的等价关系**。
- 成键/反键态在费米能级处的分布可解释结构稳定性：费米能级落在反键区意味着电子结构不稳定（如立方 Te 的 Peierls 不稳定性、bcc-Fe 非磁性相的磁性驱动电子相变），是判断键合与相变的直观工具。

## COHP 计算流程

### 1. VASP 结构优化
标准几何优化即可（见 `workflows.md` 的 opt 流程）。

### 2. COHP 计算（VASP 单点，为 LOBSTER 准备波函数）
关键 INCAR 要求：

```text
ISTART = 0        ICHARG = 2        ISYM = -1   # 一定要 -1 或 0
PREC = Accurate   ENCUT = <收敛测试值>
ISMEAR = -5       # 若用 0/1，则 lobsterin 需加 gaussianSmearingWidth
NELM = 100        NELMIN = 2        EDIFF = 1e-8
IBRION = -1       ISIF = 0          NSW = 0
ISPIN = 1         # 算自旋用 2
LREAL = .FALSE.   NBANDS = 200      # 尽量大，太小则 lobster 可能无输出/报错
LWAVE = .TRUE.    NPAR = 4          NEDOS = 2000
LORBIT = 12       # 官方示例用 12，尽量别用 11
```

要点：**必须输出 WAVECAR**（LOBSTER 从平面波波函数投影）；`LORBIT=12`；`ISYM=-1/0`；`NBANDS` 充足。

### 3. 准备 lobsterin
推荐**按元素 + 键长**（`cohpGenerator`）而非逐原子对生成（LOBSTER 把指定的原子对视为非周期，pymatgen 算的周期性距离它会认错）。`lobsterin` 示例：

```text
COHPstartEnergy  -10
COHPendEnergy     5
usebasisset pbeVaspFit2015
gaussianSmearingWidth 0.05     # 仅当 INCAR 里 ISMEAR=0 或 1 时需要
basisfunctions Ga   4s 4p 4d
basisfunctions As   4s 4p 4d
cohpGenerator from 2.483 to 2.485 type Ga type As
```

- **基函数（basisfunctions）** 参考伪势 POTCAR 中价电子轨道填写，基组选择对结果影响很大。
- 生成脚本见 `scripts/gen_lobsterin.py`（含 `get_bond_total.py` 的功能：先统计各键长的原子对，再据此写 `lobsterin`）。
- 运行：`lobster-4.1.0`（在含 WAVECAR/CONTCAR/KPOINTS/OUTCAR/POTCAR/vasprun.xml 及 lobsterin 的目录）。

### 4. 结果分析
- **核对原子对数量**：确认 `lobsterin` 指定键长范围产生的原子对数量与 `distance.dat` 一致——多了/少了都会改变 COHP/ICOHP 值。
- **画 COHPCAR.lobster**：第 1 列能量（费米能级在 0 eV），第 2 列所有原子对平均 COHP，第 3 列平均 ICOHP；之后每两列对应一个原子对的 COHP/ICOHP。
- **ICOHP 的意义**：对单个体系求"整体 ICOHP 平均"意义不大（掩盖原子对差异），更关注**特定原子对**的 ICOHP——从最低能级积分到费米面，**越负表示成键越强**（定性）。

## 常见问题（来自原文评论区）

- **lobster 不报错但没输出 COHP/ICOHP** → `NBANDS` 太少。
- **COHPCAR.lobster 只有正值** → 多半是元素/键长指定或轨道设置问题，需复查。
- **COHP 图像毛刺多** → k 点不够密，或插值/画图点太少。
- **报错涉及元素名** → 检查 `lobsterin` 中元素名/原子编号是否写对。
- **能量范围在哪看** → 在 `lobsterin` 里用 `COHPstartEnergy/COHPendEnergy` 设置。

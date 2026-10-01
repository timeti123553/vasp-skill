# LAPACK: Routine ZPOTRF failed / call to ZHEGV failed（EDDRMM）

- 来源文件: `researchgate-post-lapack-zpotrf-zhegv-failed`（网页，2015 年提问，含后续热门回复）
- 收录日期: 2026-09-30
- 标签: LAPACK, ZPOTRF, ZHEGV, EDDRMM, 数值发散, 收敛

---

## 报错现象

运行 VASP 时（示例体系 Al47CrO72，`ALGO=Fast`、`ISMEAR=0`、`SIGMA=0.05`、`PREC=Accurate`、`ENCUT=520`、`ISPIN=2`、`IBRION=2`），反复出现：

```text
WARNING in EDDRMM: call to ZHEGV failed, returncode = 3 2 1
WARNING in EDDRMM: call to ZHEGV failed, returncode = 3 2 99
LAPACK: Routine ZPOTRF failed! 1 1 1
LAPACK: Routine ZPOTRF failed!
```

`EDDRMM` 的 `returncode` 末尾从 1 数到 99 后循环（即每个 SCF 步都触发），属于**周期性出现的警告+致命报错**。

## 含义与成因

两条报错通常指向同一个根因：**数值发散 / 数值崩溃**。VASP 在对某个（非正定或病态的）矩阵做 Cholesky 分解（`ZPOTRF`）或求解广义本征问题（`ZHEGV`）时失败，常见于：

1. SCF 不稳定、电荷混合发散（矩阵不正定）。
2. 输入不一致或初值不当（如旧的 `WAVECAR`/`CHGCAR`、磁性 `MAGMOM` 初猜不合理）。
3. RMM-DIIS 电子最小化算法失败（`ALGO=Fast` 使用 RMM-DIIS；换 `ALGO=Normal` 即不调用它）。
4. 并行/内存设置不当（`KPAR*NCORE` 分配问题、`NCORE` 过大）。
5. 精度不够、实空间投影、POTCAR 混用、k 网格过疏等。

## 解决方案（按顺序排查）

1. **从头干净起算**：删除 `WAVECAR` 与 `CHGCAR`，`ISTART=0`、`ICHARG=2`；若此前在做 SOC 或 DFPT，先收敛一个普通 SCF。
2. **稳定对角化**：`ALGO=Normal`（仍不稳则 `ALGO=All`；非常顽固用 `ALGO=Damped` 配 `TIME=0.3–0.6`）。这是针对 RMM-DIIS 失败的直接手段。
3. **提高数值质量**：`PREC=Accurate`；`ENCUT` 取 `max(POTCAR)` 的 +20–30%；`ADDGRID=.TRUE.`（必要时 `NG(X,Y,Z)` 设为默认的 ~1.3 倍）；金属/大体系把 `LREAL=.FALSE.`。
4. **调混合器**：从保守默认起：`AMIX=0.2 BMIX=0.0001 AMIX_MAG=0.2 BMIX_MAG=0.0001`；金属难收敛时 `AMIX(_MAG)` 降到 0.05–0.1；电荷 sloshing 时加强 Kerker：`BMIX(_MAG)=0.001`。
5. **合理展宽**：金属 `ISMEAR=1, SIGMA=0.2`（稳定后可降到 0.1）；绝缘体 `ISMEAR=0, SIGMA=0.05`。
6. **对称与磁性**：给每种磁性元素设合理初始 `MAGMOM`；对称引发问题时 `ISYM=0`（SOC、Janus、偏心结构常见）。
7. **并行设置**：确保 `KPAR * NCORE ≤ 总核数` 且整除；`NCORE` 过大就降到 4–8 再试；可用单 k 点（Γ only）做诊断测试。
8. **能带数**：`NBANDS` 比默认再 +10–20%，尤其 SOC 或金属体系。
9. **POTCAR / KPOINTS 检查**：所有 POTCAR 来自同一套（如全 PBE，勿 PBE+LDA 混用）；k 网格别过疏，可加密或 `KSPACING≈0.2–0.3`。
10. **SOC 专项**：先不带 SOC 收敛；再开 `LSORBIT=.TRUE.`（需要时配 `LNONCOLLINEAR=.TRUE.`）；SOC 下保持 `ISYM=0`、`LREAL=.FALSE.`、`NBANDS` 略高。

## 附：自动化修复工具

- **custodian**（Materials Project）：`http://pythonhosted.org/custodian/`，可自动处理多种常见 VASP 报错；其 `vasp/handlers.py` 源码里对每条报错标注了它尝试的修复方式，可用来核对本类报错的处置。
- **aflow**（Curtarolo 组）：`http://materials.duke.edu/aflow.html`，同样会自动尝试修正常见 VASP 报错，文档中可查对应处置逻辑。

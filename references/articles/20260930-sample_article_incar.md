# sample_article_incar

- 来源文件: `sample_article_incar.txt`
- 收录日期: 2026-09-30
- 标签: 收敛, INCAR

---
# VASP 收敛参数速查（示例文章）

## 电子步不收敛
- 若 SCF 震荡不收敛，常见是电荷混合不当。金属体系建议 `AMIX=0.1`、`BMIX=0.0001`。
- 磁性体系出现 `Sub-Space-Matrix is not hermitian in DAV` 时，往往要调低 `AMIX_MAG`、`BMIX_MAG`，并检查 `MAGMOM` 初猜。
- 增大 `NELM` 到 120–200 并放慢混合，通常能收敛。

## 力收敛
- `EDIFFG` 为负值时按力判据（如 -0.02），为正值时按能量判据。
- 声子计算前建议 `EDIFFG=-1E-3` 或更严，避免虚频。

## 注意
- `ISMEAR` 选错（金属用 1/-5、绝缘体用 0）会导致能量不收敛或虚频。

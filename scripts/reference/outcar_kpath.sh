# =============================================================================
# 参考脚本（用户粘贴的知乎文章收集 · 未运行验证）
# 来源文章: articles/20261001-提取OUTCAR中的能带数据.md
# 原作者  : 郭麒麟（知乎；用户粘贴正文，未提供链接）
# 用途    : 导出 k 路径的两种单位：kpath_1.dat 为倒格矢（分数）坐标；kpath_2.dat 为 2π/SCALE 单位
# 依赖    : bash + awk + grep + sort（POSIX 工具，无需额外安装）
# 使用    : 同上，`bash outcar_kpath.sh`（生成 `kpath_1.dat`、`kpath_2.dat`）
# 注意    : ① 两套单位**含义不同**，画能带图时要与原子的本征值文件配套使用（细节见 `workflows.md` §二十）；② 原脚本用 `>>` 追加，**重复运行会把内容叠起来** → 建议首次用 `>` 或先删旧文件。
# =============================================================================

#!/bin/bash
NKPTS=$(awk '/NKPTS/ {print($4)}' OUTCAR)
echo "# k-points in reciprocal lattice" >> kpath_1.dat
grep -A $NKPTS "k-points in reciprocal lattice and weights" OUTCAR | awk '{print($1 "  " $2 "  " $3)}'| tail -$NKPTS >> kpath_1.dat

echo "# k-points in units of 2pi/SCALE" >> kpath_2.dat
grep -A $NKPTS "k-points in units of 2pi/SCALE and weight" OUTCAR | awk '{print($1 "  " $2 "  " $3)}' | tail -$NKPTS >> kpath_2.dat

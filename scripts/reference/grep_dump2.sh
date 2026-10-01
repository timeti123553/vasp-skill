# =============================================================================
# 参考脚本（从文章收集）
# 来源文章: 20261001-TDEP计算高温声子谱_天帝君豪的个人博客.md
# 原文链接: https://tiandijunhao.github.io/2020/06/28/tdep-ji-suan-sheng-zi-pu/
# 用途    : 同上，改用 gawk/tail 处理并排除第一帧
# 依赖    : bash + gawk
# 抓取质量: ⚠️ 原文代码块导出时**丢失了空格与换行**；本文件是**本库重排**版本，
#           只补空白、未改动逻辑，**未运行验证**；原文形态保留在来源文章的 md 里。
# =============================================================================

#!/bin/bash
# grep_dump2.sh —— 与 grep_dump.sh 等价，但用 gawk/tail 处理，并**排除第一帧**

# number of atoms
Nat=$(head -n 4 dump.forces | tail -n 1)

# copy dump.stat to infile.stat
grep -v '^#' dump.stat > infile.stat

# number of timesteps
Nt=$(gawk 'END{print FNR}' infile.stat)

# create the positions and forces files
[ -f infile.forces ] && rm infile.forces
[ -f infile.positions ] && rm infile.positions

# prepare input files. Mind that first configuration in dump.forces and
# dump.positions should be excluded
((Nl=$Nt*($Nat+9)))
tail -n $Nl dump.forces    | grep -A $Nat 'ITEM: ATOM' | grep -v 'ITEM: ATOM' | grep -v '^--$' >> infile.forces
tail -n $Nl dump.positions | grep -A $Nat 'ITEM: ATOM' | grep -v 'ITEM: ATOM' | grep -v '^--$' >> infile.positions

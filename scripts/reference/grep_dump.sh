# =============================================================================
# 参考脚本（从文章收集）
# 来源文章: 20261001-TDEP计算高温声子谱_天帝君豪的个人博客.md
# 原文链接: https://tiandijunhao.github.io/2020/06/28/tdep-ji-suan-sheng-zi-pu/
# 用途    : 把 LAMMPS 的 dump.positions/dump.forces 转成 TDEP 需要的 infile.positions/forces/stat
# 依赖    : bash（head/tail/awk/seq）
# 抓取质量: ⚠️ 原文代码块导出时**丢失了空格与换行**；本文件是**本库重排**版本，
#           只补空白、未改动逻辑，**未运行验证**；原文形态保留在来源文章的 md 里。
# =============================================================================

#!/bin/bash
# 把 LAMMPS 的 dump.positions / dump.forces 转成 TDEP 需要的
# infile.positions / infile.forces / infile.stat

# figure out how many atoms there are
na=`head -n 4 dump.forces | tail -n 1`

# remove the header from the stat file
grep -v '^#' dump.stat > infile.stat

# figure out how many timesteps there are
nt=`wc -l infile.stat | awk '{print $1}'`

# create the positions and force files
[ -f infile.forces ] && rm infile.forces
[ -f infile.positions ] && rm infile.positions

for t in `seq 1 ${nt}`
do
  nl=$(( ${na} + 9 ))
  nll=$(( ${nl} * ${t} ))
  echo "t ${t} ${nl} ${nll}"
  head -n ${nll} dump.forces    | tail -n ${na} >> infile.forces
  head -n ${nll} dump.positions | tail -n ${na} >> infile.positions
done

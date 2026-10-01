# =============================================================================
# 参考脚本（用户粘贴的知乎文章收集 · 未运行验证）
# 来源文章: articles/20261001-提取OUTCAR中的能带数据.md
# 原作者  : 郭麒麟（知乎；用户粘贴正文，未提供链接）
# 用途    : 按带号把 OUTCAR 里的本征值逐个导出为 bands_<i>.dat（每行一个 k 点上的该带能量）
# 依赖    : bash + awk + grep + sort（POSIX 工具，无需额外安装）
# 使用    : 把脚本放到含 `OUTCAR` 的目录里执行：`bash outcar_bands.sh`（生成 `bands_1.dat` …）
# 注意    : ① `NBANDS` 在 OUTCAR 中可能有多行匹配，`$(awk '/NBANDS/{print $NF}')` 会拿到多行 → 建议 `| tail -1`；② 内层 `grep "    $i    "` 依赖本征值行的**固定列宽**，带序号超过 1 位（≥10）后空格数变化会漏匹配 → 大体系改用 `awk -v b=$i '$1==b {print $2}'`；③ 需要 `OUTCAR` 与脚本在同一目录（脚本里写死了文件名）。
# =============================================================================

#!/bin/bash
NBANDS=$(awk '/NBANDS/ {print($NF)}' OUTCAR)
NKPTS=$(awk '/NKPTS/ {print($4)}' OUTCAR)
echo $NBANDS  $NKPTS
for i in $(seq 1 1 $NBANDS); do
grep -A $NBANDS 'band No.' OUTCAR | grep "    $i    " | awk '{print($2)}' > bands_$i.dat
done

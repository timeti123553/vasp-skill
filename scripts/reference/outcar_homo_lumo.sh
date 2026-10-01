# =============================================================================
# 参考脚本（用户粘贴的知乎文章收集 · 未运行验证）
# 来源文章: articles/20261001-提取OUTCAR中的能带数据.md
# 原作者  : 郭麒麟（知乎；用户粘贴正文，未提供链接）
# 用途    : 用 NELECT 推出 HOMO/LUMO 的带序号，再取该带在所有 k 点上的最大/最小能量，打印 HOMO/LUMO（可算带隙）
# 依赖    : bash + awk + grep + sort（POSIX 工具，无需额外安装）
# 使用    : `bash outcar_homo_lumo.sh OUTCAR`（脚本用 `$1` 接收 OUTCAR 路径）
# 注意    : ① 用法：`bash outcar_homo_lumo.sh OUTCAR`（脚本用 `$1` 接收文件名）；② `NELECT/2` 推带序号**仅适用于非自旋极化体系**，`ISPIN=2` 或带电体系不适用；③ 同样的固定列宽问题；④ 原文写作 LOMO，通行为 LUMO。
# =============================================================================

#!/bin/bash
homo=$(awk '/NELECT/ {print $3/2}' $1)
lumo=$(awk '/NELECT/ {print $3/2+1}' $1)
nkpt=$(awk '/NKPTS/ {print $4}' $1)

e1=$(grep "     $homo     " $1 | head -$nkpt | sort -n -k 2 | tail -1 | awk '{print $2}')
e2=$(grep "     $lumo     " $1 | head -$nkpt | sort -n -k 2 | head -1 | awk '{print $2}')

echo "HOMO: band index:" $homo " E=" $e1
echo "LUMO: band index:" $lumo " E=" $e2

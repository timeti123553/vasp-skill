# =============================================================================
# 参考脚本（从文章收集 · 未运行验证）
# 来源文章: 20261001-vasp计算光学性质教程.md
# 原文链接: https://mp.weixin.qq.com/s/waTzUdwZZUqbe1e9VtDX_g
#            （作者 贺勇，个人博客 https://yh-phys.github.io）
# 用途    : 从 vasprun.xml 中抽取介电函数的虚部/实部，写成 VASPKIT 老版本所需的
#           IMAG.in / REAL.in（两列以上：能量 + 各分量）。
# 依赖    : awk（无需 Python）
# 注意    : ⚠️ VASPKIT 1.0 及以上**不再需要**这一步（直接运行 711 即可）；
#           本脚本按「原样收集、未验证」的约定附在下面。
# =============================================================================

# extract image and real parts of dielectric function from vasprun.xmlawk 'BEGIN{i=1} /<imag>/,\ /<\/imag>/ \ {a[i]=$2 ; b[i]=$3 ; c[i]=$4; d[i]=$5 ; e[i]=$6 ; f[i]=$7; g[i]=$8; i=i+1} \ END{for (j=12;j<i-3;j++) print a[j],b[j],c[j],d[j],e[j],f[j],g[j]}' vasprun.xml > IMAG.in#awk 'BEGIN{i=1} /imag/,\# /\/imag/ \# {a[i]=$2 ; b[i]=$3 ; c[i]=$4; d[i]=$5 ; e[i]=$6 ; f[i]=$7; g[i]=$8; i=i+1} \# END{for (j=12;j<i-3;j++) print a[j],b[j],c[j],d[j],e[j],f[j],g[j]}' vasprun.xml > IMAG.inawk 'BEGIN{i=1} /<real>/,\ /<\/real>/ \ {a[i]=$2 ; b[i]=$3 ; c[i]=$4; d[i]=$5 ; e[i]=$6 ; f[i]=$7; g[i]=$8; i=i+1} \ END{for (j=12;j<i-3;j++) print a[j],b[j],c[j],d[j],e[j],f[j],g[j]}' vasprun.xml > REAL.in

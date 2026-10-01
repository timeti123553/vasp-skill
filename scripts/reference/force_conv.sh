# =============================================================================
# 参考脚本（从知乎文章收集 · 未运行验证）
# 名称    : force_conv.sh（原作者 @叠加态 / lipai，lipai@mail.ustc.edu.cn）
# 来源文章: articles/20261001-VASP结构优化计算中查看能量和力收敛情况.md
# 原文链接: https://zhuanlan.zhihu.com/p/376360440
# 用途    : 从 OSZICAR + OUTCAR + CONTCAR 汇总出**每个离子步的总能量与「非固定原子」的最大受力**，
#           写到 force.conv，并用 gnuplot 的 `set term dumb` **直接在终端画出 ASCII 曲线**
#           （步数 > 8 时额外画最后 5 步的放大图）。用法：`bash force_conv.sh [起始离子步]`。
# 依赖    : bash + awk + gnuplot（**系统里没有 gnuplot 会报 command not found**）
# 关键设计: 它从 **CONTCAR 的第 4/5/6 列**读取 `T`/`F` 标志来识别**固定原子**，把这些原子的受力置 0 后再求最大力
#           ——因为 **`EDIFFG` 的力判据只约束非固定原子**，不排除固定原子就会误判收敛。
# 抓取质量: 原网页把整个脚本**压成了一行**（换行与缩进全丢）：逻辑可读，但**不能直接复制运行**，
#           需要按 shell 语法重新断行缩进（文中 if/for/fi 等结构清晰）。
# =============================================================================

#!/bin/sh #lipai@mail.ustc.edu.cnbegin=$1if[$begin==''];thenbegin=0;fi awk -v begin=$begin'/E0/{if ( i<begin ) i++;else print $0 }'OSZICAR >temp.e awk '/POSITION/,/drift/{ if(NF==6) print $4,$5,$6; else if($1=="total") print $1 }' OUTCAR >temp.f awk '{if($4=="F"||$4=="T") print $4,$5,$6}'CONTCAR >temp.fix flag=`wc temp.fix|awk '{print $1}'`steps=`grep E0 OSZICAR |tail -1 |awk '{print $1}'`if[ flag !='0'];thenif[ -f temp.fixx ];then rm temp.fixx ;fifor i in `seq $steps`;do cat temp.fix >>temp.fixx echo >>temp.fixx done paste temp.f temp.fixx >temp.ff fi awk '{ if($1=="total") {print ++i,a;a=0} else { if($4=="F") x=0; else x=$1; if($5=="F") y=0; else y=$2; if($6=="F") z=0; else z=$3; force=sqrt(x^2+y^2+z^2); if(a<force) a=force} }' temp.ff >force.conv gnuplot<<EOF set term dumb set title 'Energy of each ionic step' set xlabel 'Ionic steps' set ylabel 'Energy(eV)' plot 'temp.e' u 1:5 w l t "Energy in eV" set title 'Max Force of each ionic step' set xlabel 'Ionic steps' set ylabel 'Force (eV/Angstrom)' plot 'force.conv' w l t "Force in eV/Angstrom" EOFif[$steps -gt 8];then tail -5 force.conv >temp.fff tail -5 temp.e >temp.ee gnuplot <<EOF set term dumb set title 'Energy of each ionic step for the last few steps' set xlabel 'Ionic steps' set ylabel 'Energy(eV)' plot 'temp.ee' u 1:5 w l t "Energy in eV" set title 'Max Force of each ionic step for the last few steps' set xlabel 'Ionic steps' set ylabel 'Force (eV/Angstrom)' plot 'temp.fff' w l t "Force in eV/Angstrom" EOF rm temp.fff temp.ee fi rm temp.e temp.f temp.ff temp.fix temp.fixx

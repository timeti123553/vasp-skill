#===============================================================================
# 参考脚本（原样收集 · 未验证 · 未运行）
# 来源文章: articles/20260930-VASP计算二维材料的载流子迁移率.md
# 原文链接: https://mp.weixin.qq.com/s/_d4hx-QO3nqNeRe9M4MUPA
# 用途    : 批量生成 −2%~+2% 应变目录：复制基准 IS/ 目录并用 sed 改 POSCAR 晶格常数（x 改第 3 行、y 改第 4 行）
# 依赖    : bash + sed + bc（qsub 行默认被注释）
# 功能说明: references/tools.md 三.3（本目录只放源码文本，说明以那里为准）
# 抓取质量: 原网页代码块**丢失换行与缩进** —— 下面正文是原样保存的文本，
#           只能读逻辑，不能直接执行。
#===============================================================================

#!/bin/bash#3 November, 2018#To use it: bash mobility.shmkdir mobility-xcd mobility-xx=4.083622259999999 #"x" stands for the lattice constant in x directionfor i in $(seq 0.98 0.005 1.02) #"i" defines the range of straindocp -r ../IS ./$i #"IS" stands for the origin file sed -i "3s/$x/$(echo "$x*$i"|bc)/g" $i/POSCARcd $i#qsub ./pbscd $OLDPWDdonecd ../mkdir mobility-ycd mobility-yy=7.073041233239241 #"y" stands for the lattice constant in y directionfor j in $(seq 0.98 0.005 1.02) #"j" defines the range of straindocp -r ../IS ./$j #"IS" stands for the origin file sed -i "4s/$y/$(echo "$y*$j"|bc)/g" $j/POSCARcd $j#qsub ./pbscd $OLDPWDdone

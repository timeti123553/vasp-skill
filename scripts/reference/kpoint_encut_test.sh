# =============================================================================
# 参考脚本（从博客原文收集 · 未运行验证 · **已做最小修复**）
# 来源文章: articles/20261001-自动进行K点和ENCUT测试bash脚本.md
# 原文链接: https://www.jun997.xyz/2021/10/19/fa8688fdb49b.html
# 作者    : June976 (jun997.xyz)
# 用途    : 根据 POSCAR/POTCAR 自动跑 k 点与 ENCUT 的收敛性测试，输出能量与耗时
# 依赖    : vaspkit（生成 KPOINTS）、bc、VASP、LSF 作业系统（脚本头是 #BSUB）
# 抓取修复: 网页把代码渲染成「行号单独成行 + 每行之间空一行」，且**丢了几处空格**。
#           本文件已：① 删除行号栏与多余空行；② 修回下列空格（这是原文抓取丢失的，
#           原文语义应为带空格）：
#             - ENCUT0=$(echo"$MAXEN_*1.3"|bc)        → echo "$MAXEN_*1.3"
#             - for encut in$ENCUT0 $(echo"$ENCUT0...") → in $ENCUT0 $(echo "$ENCUT0..."
#             - cd$encut                              → cd $encut
#             - echo$i$E$T >> ...                     → echo $i $E $T >>
#             - echo$encut$E$T >> ...                 → echo $encut $E $T >>
#           **其余内容与原文一致**（含 heredoc 不缩进、硬编码路径等）。
# 用前必改: ① 作业脚本头（#BSUB 是 LSF 的写法）；
#           ② mpirun 那行的 VASP 绝对路径 /gpfs/software/vasp/vasp.5.3-20181107；
#           ③ MAXEN_（原文硬编码 300，应改成 `grep ENMAX POTCAR` 得到的真实最大值，
#              或取消注释上面那行 read 手动输入）。
# =============================================================================

##################自动进行k点和encut测试#################
#要求：安装了vaspkit,同级目录下存放POTCAR和POSCAR文件
#!/bin/bash
#BSUB -J luojun
#BSUB -e %J.err
#BSUB -o %J.out
#BSUB -q inspur-1
#BSUB -n 24
#BSUB -R "span[ptile=24]"
##BSUB -R "span[host=1]"
grep ENMAX POTCAR
#read -p "input max_enmax:" MAXEN_
MAXEN_=300
ENCUT0=$(echo "$MAXEN_*1.3"|bc)
mkdir k-test
mkdir encut-test
cd k-test
for i in 0.05 0.04 0.03 0.025 0.02 0.01
do
mkdir ./$i
cp ../POTCAR ./$i/
cp ../POSCAR ./$i/
cd ./$i
cat >./INCAR <<!
SYSTEM = AUTO TEST K POINTS
ISTART = 0
ICHARG = 2
ENCUT = $ENCUT0
LREAL = A
PREC = A
LWAVE = F
LCHARG = F
NCORE = 4
ISMEAR = 0
SIGMA = 0.01
NSW = 0
IBRION = -1
NELMIN = 6
NELM = 400
EDIFF = 1E-8
ALGO = VeryFast
!
echo -e "102\n2\n$i\n"| vaspkit #1:Monkhorst Pack grid 2:Gamma center
mpirun -bootstrap lsf /gpfs/software/vasp/vasp.5.3-20181107 > result.log
E=`grep "energy without" OUTCAR|tail -1|awk '{print $7}'`
T=`grep "Total CPU time" OUTCAR|awk '{print $6}'`
echo $i $E $T >> ../k-test-result.txt
cd ..
done
cd ..
cd encut-test
for encut in $ENCUT0 $(echo "$ENCUT0+100"|bc) $(echo "$ENCUT0+200"|bc) $(echo "$ENCUT0+300"|bc)
do
mkdir $encut
cp ../POTCAR ./$encut/
cp ../POSCAR ./$encut/
cd $encut
cat >./INCAR <<!
SYSTEM = AUTO TEST K POINTS
ISTART = 0
ICHARG = 2
ENCUT = $encut
LREAL = A
PREC = A
LWAVE = F
LCHARG = F
NCORE = 4
ISMEAR = 0
SIGMA = 0.01
NSW = 0
IBRION = -1
NELMIN = 6
NELM = 400
EDIFF = 1E-8
ALGO = VeryFast
!
echo -e "102\n2\n0.03\n"| vaspkit #1:Monkhorst Pack grid 2:Gamma center
mpirun -bootstrap lsf /gpfs/software/vasp/vasp.5.3-20181107 > result.log
E=`grep "energy without" OUTCAR|tail -1|awk '{print $7}'`
T=`grep "Total CPU time" OUTCAR|awk '{print $6}'`
echo $encut $E $T >> ../encut-test-result.txt
cd ..
done
cd ..


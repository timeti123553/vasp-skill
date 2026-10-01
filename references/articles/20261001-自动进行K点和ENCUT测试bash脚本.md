# 自动进行K点和ENCUT测试bash脚本

- 来源: `https://www.jun997.xyz/2021/10/19/fa8688fdb49b.html`
- 类型: html (url)
- 抓取时间: 2026-10-01 12:42:35
- 作者: June976（jun997.xyz）
- 类型: html (url)
- 标签: 博客, 收敛性测试, KPOINTS, ENCUT, bash 脚本
- ⚠️ 抓取说明：正文几乎全是代码，网页渲染为「行号单独成行 + 每行之间空一行」，且**丢失了若干空格**；本文件已删除纯数字行号行，脚本的清理版与修复清单见 `scripts/reference/kpoint_encut_test.sh`。
- 正文字数: 2797

---
分享一个自己写的根据POSCAR和POTCAR自动进行K点和ENCUT收敛性测试的脚本。

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

32

33

34

35

36

37

38

39

40

41

42

43

44

45

46

47

48

49

50

51

52

53

54

55

56

57

58

59

60

61

62

63

64

65

66

67

68

69

70

71

72

73

74

75

76

77

78

79

80

81

82

83

84

85

86

87

88

89

90

91

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

ENCUT0=$(echo"$MAXEN_*1.3"|bc)

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

echo$i$E$T >> ../k-test-result.txt

cd ..

done

cd ..

cd encut-test

for encut in$ENCUT0 $(echo"$ENCUT0+100"|bc) $(echo"$ENCUT0+200"|bc) $(echo"$ENCUT0+300"|bc)

do

mkdir $encut

cp ../POTCAR ./$encut/

cp ../POSCAR ./$encut/

cd$encut

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

echo$encut$E$T >> ../encut-test-result.txt

cd ..

done

cd ..


---

> ✂️ 已裁掉站点 UI 尾部（归档/标签/订阅/CC 声明等），并删除网页代码块的行号行。
> 脚本的**清理 + 空格修复版**收在 `scripts/reference/kpoint_encut_test.sh`，流程说明见 `workflows.md` 第二十八节。

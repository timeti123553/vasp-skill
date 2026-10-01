# 本机环境

> 只记「换一台机器就会变」的事实。用不到的项留空或删掉，**不要猜着填**。
> 写错的本机信息比空白更有害——后续会话会把它当事实直接用。

## 计算资源

- VASP 可执行文件：<!-- 如 /opt/vasp/bin/vasp_std；是否 VTST 版（能算 NEB）？ -->
- 提交方式：<!-- Slurm / PBS / 本地 mpirun -->
- 典型并行规模：<!-- 如 32 核，NCORE=4；KPAR 是否可用 -->
- 其他可用程序：<!-- VASPKIT / phonopy / ALAMODE / VESTA / GROMACS 版本与路径 -->

## POTCAR

- 势库路径：<!-- 如 C:\Users\Administrator\Desktop\PBE -->
- map.json 位置：<!-- 默认用技能自带的 scripts/map.json；自定义的写在这里 -->
- 选势口径：<!-- 如 Fe→Fe_pv，Ag→Ag，S→S -->
- 已知的选势坑：<!-- 如某元素的 _pv 势与实验晶格常数系统性偏差 -->

## 这台机器上反复踩的坑

<!-- 如：某目录会被杀软锁住导致文件替换失败；某节点内存不足需降 ENCUT -->

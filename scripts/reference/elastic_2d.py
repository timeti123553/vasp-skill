#===============================================================================
# 参考脚本（原样收集 · 未验证 · 未运行）
# 来源文章: articles/20261001-VASP计算材料的弹性矩阵和杨氏模量.md
# 原文链接: https://www.jun997.xyz/2023/03/09/a931fd747c09.html
# 用途    : 二维材料：单位换成 N/m 后画极坐标 E(φ) 与 ν(φ)（含文档里硬编码的验证用例）
# 依赖    : Python + numpy + pandas + matplotlib
# 功能说明: workflows.md 第十八节 / references/tools.md 三.6（本目录只放源码文本，说明以那里为准）
# 抓取质量: 原网页代码块丢失缩进（行号单独成行，已去除）；含作者用于对文献的硬编码数据段。
#===============================================================================
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
### 读取弹性矩阵
os.system('grep -A 8 "TOTAL ELASTIC" OUTCAR | tail -6 > ecs.dat')
str_c = os.popen("grep -A 3 'lattice vectors' OUTCAR | tail -1 | awk '{print $3}'")
lat_c = float(str_c[0])
# lat_c = 16.0
df_ecs = pd.read_csv('ecs.dat', header=None, index_col=0, delimiter=r"\s+")
dat_ecs = df_ecs.values ### 得到弹性矩阵
### 将vasp给出的弹性矩阵转换成满足Voigt下标的矩阵形式并将单位转换为GPa
dat_c = np.zeros(dat_ecs.shape)
for m inrange(6):
if m <= 2:
m_ = m
elif m == 3or m == 4:
m_ = m + 1
elif m == 5:
m_ = 3
for n inrange(6):
if n <= 2:
n_ = n
elif n == 3or n == 4:
n_ = n + 1
elif n == 5:
n_ = 3
dat_c[m, n] = dat_ecs[m_, n_]*0.01*lat_c
# print(dat_c)
################################### 改动部分 ########################################
dat_c = np.zeros((6, 6)) #
dat_c[0, 0] = 105.2#
dat_c[0, 1] = 18.4#
dat_c[1, 0] = dat_c[0, 1] #
dat_c[1, 1] = 26.2#
dat_c[2, 2] = 1.0#
dat_c[3, 3] = 1.0#
dat_c[4, 4] = 1.0#
dat_c[5, 5] = 22.4#
################################### 改动部分 ########################################
### 计算柔度矩阵
dat_s = np.linalg.inv(dat_c)
### 将二维柔度矩阵转换成四维柔度矩阵
deftranS_ijkl(dat_s):
'''
将6x6的二维柔度矩阵转换成2x2x2x2的柔度矩阵
'''
S_ijkl = np.zeros((2, 2, 2, 2))
for i inrange(2):
for j inrange(2):
if i==j:
s_m = i
ij_eq = True
elif i+j == 1:
s_m = 5
ij_eq = False
for k inrange(2):
for l inrange(2):
if k==l:
s_n = k
kl_eq = True
elif k+l == 1:
s_n = 5
kl_eq = False
if ij_eq and kl_eq:
S_ijkl[i, j, k, l] = dat_s[s_m, s_n]
elifnot ij_eq andnot kl_eq:
S_ijkl[i, j, k, l] = dat_s[s_m, s_n]/4.0
else:
S_ijkl[i, j, k, l] = dat_s[s_m, s_n]/2.0
return S_ijkl
S_ijkl = tranS_ijkl(dat_s)
sample_count = 1000### 网格数量
### 在空间球面上均匀采样
v_phi = np.linspace(0, 2.0*np.pi, sample_count)
a_x = np.cos(v_phi)
a_y = np.sin(v_phi)
v_A = [a_x, a_y]
v_B = [-1.0*a_y, a_x]
E_a_1 = np.zeros(sample_count)
v_ab_1 = np.zeros(sample_count)
for i inrange(2):
for j inrange(2):
for k inrange(2):
for l inrange(2):
E_a_1 = E_a_1 + v_A[i]*v_A[j]*v_A[k]*v_A[l]*S_ijkl[i, j, k, l]
v_ab_1 = v_ab_1 + v_A[i]*v_A[j]*v_B[k]*v_B[l]*S_ijkl[i, j, k, l]
E_a = 1.0/E_a_1 ### 取倒数得到杨氏模量，单位从为GPa
v_ab = -1.0*v_ab_1/E_a_1
plt.figure(dpi=200)
ax_E = plt.subplot(121, projection='polar')
ax_E.set_title("Young's Modulus(N/m)")
ax_E.plot(v_phi,E_a,'-',lw=1.5,color='r')
ax_E.fill(v_phi,E_a,'r',alpha=0.2)
ax_E.set_rgrids(np.arange(0, 1.2*np.max(E_a), 20))
ax_v = plt.subplot(122, projection='polar')
ax_v.set_title("Poisson's Ratio")
ax_v.plot(v_phi,v_ab,'-',lw=1.5,color='g')
ax_v.fill(v_phi,v_ab,'g',alpha=0.2)
ax_v.set_rgrids(np.arange(0, 1.2*np.max(v_ab), 0.1))
plt.savefig('young2D.jpg')

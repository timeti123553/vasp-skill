# =============================================================================
# 参考脚本（从博客原文收集 · 未运行验证 · 原文代码块被压成单行）
# 来源文章: articles/20261001-晶胞转换_天帝君豪的个人博客.md
# 原文链接: https://tiandijunhao.github.io/2020/04/25/jing-bao-zhuan-huan/
# 作者    : 天帝君豪
# 用途    : 读 POSCAR（名字/缩放系数/3 行晶格/元素名/元素数/坐标类型/坐标），并用 spglib.get_symmetry_dataset 取空间群号
# 依赖    : Python + spglib + numpy
# 抓取质量: 原网页代码块**丢失换行与缩进**（整段挤成一行），逻辑可读但**不能直接复制运行**；
#           如需使用请按 Python 语法重新缩进。
# 注意    : ⚠️ **已知限制**：构造 `atom_numbers` 的那行只按**第一种元素的原子数**生成序号（`[1,]*(int(self.atomnum[0]))`），因此对**多元素体系**长度不匹配、取空间群号这一步会出错（文中 ThO₂ 这类例子请自行按元素补齐序号）。注意该值只用于报告空间群号，**不算数地影响后面的换胞**（换胞用的是 reposcar 里按元素生成的序号）。
# =============================================================================

import spglib import numpy as np import os import linecache classread_poscar(object):def__init__( self, struct=None, pos_name=None, lattice_index=None, lat=None, lat_recell=None, atomname=None, atomnum=None, postype=None, pos=None, spg_number=None,): self.struct = linecache.getlines("POSCAR")# read POSCAR to get some paramatrics: sys_name; lattice; atom_name; atom_number; atom_position# and get spacegroup_number poscar =[line.strip()for line in self.struct] num = len(poscar) self.pos_name = poscar[0].split() self.lat_index = poscar[1].split() self.lattice_index = float(self.lat_index[0])# matrics of lattice vector lat_vector = np.zeros((3,3)) index =0for latt in poscar[2:5]: latt = latt.split() lat_vector[index,:]= latt[0:3] index +=1 self.lattice = lat_vector self.atomname = poscar[5].split() self.atomnum = poscar[6].split() self.postype = poscar[7].split() atom_len=len(self.atomname)# matrics of atom position i = num -8 position_vector = np.zeros((i,3)) index =0for poss in poscar[8:num]: poss = poss.split()#position_vector[index, 0:3] = poss[0:3] position_vector[index,0]= poss[0] position_vector[index,1]= poss[1] position_vector[index,2]= poss[2] index +=1 self.lat = lat_vector * self.lattice_index self.pos = position_vector atom_numbers =[1,]*(int(self.atomnum[0]))#+int(self.atomnum[1])) cell =(self.lat, self.pos, atom_numbers) database = spglib.get_symmetry_dataset( cell, symprec=1e-3) self.spg_number = database["number"]defsystem_name(self):return self.pos_name deflatt_index(self):return self.lattice_index deflatti(self):return self.lattice defatom_name(self):return self.atomname defatom_number(self):return self.atomnum defposition_type(self):return self.postype defpositions(self):return self.pos defspacegroup_num(self):return self.spg_number

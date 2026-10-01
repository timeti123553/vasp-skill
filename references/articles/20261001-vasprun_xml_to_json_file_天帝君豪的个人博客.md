# vasprun.xml to json file | 天帝君豪的个人博客

- 来源: `https://tiandijunhao.github.io/2020/07/10/grep-config-to-json-from-vasprunxml/`
- 类型: html (url)
- 抓取时间: 2026-10-01 11:28:16
- 标签: 博客, 机器学习势, FitSNAP, vasprun.xml, 数据集
- ⚠️ 抓取说明：本文脚本来自网页代码块，**空格与换行在抓取时被压扁**（整段代码挤成一行），逻辑可读但**不能直接复制运行**。
- 正文字数: 4172

---
# vasprun.xml to json file

[计算脚本](https://tiandijunhao.github.io/tags/%E8%AE%A1%E7%AE%97%E8%84%9A%E6%9C%AC/)

[机器学习](https://tiandijunhao.github.io/categories/%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0/)

发布日期: 2020-07-10

文章字数: 455

## 将vasprun.xml 的configuration 转为 json file

主要用于FitSNAP程序的前期数据集的获取

import json import numpy as np #read energy lattice pos force stress from vasprun i=0 j=0 k=0 num_atom=0 force=[] s_step=1#int(input("starting step:\n")) d_step=1#int(input("interval of steps:\n"))#Dataset-->struc_inf-->data Dataset={} struc_inf={} struc_data={} struc_inf["Label:"]="SNAP dataset" struc_inf["LatticeStyle"]="angstrom" struc_inf["EnergyStyle"]="electronvolt" struc_inf["StressStyle"]="bar" struc_inf["AtomTypeStyle"]="chemicalsymbol" struc_inf["PositionsStyle"]="bar" struc_inf["ForcesStyle"]="electronvoltperangstrom"with open('PPOSCAR','r')as pposcar: text=pposcar.readlines() atom_list=[] atom_dict=[] one_list=['one']if text[5].strip()< text[6].strip():print('please check the input format of PPOSCAR')# for n in range(num_atom):# position0.append(text[n+7].split())else: num_class=text[5].strip().split(' ')print(num_class)for c in range(len(num_class)): num_atom=num_atom+int(text[6].strip().split(' ')[c])print(int(text[6].strip().split(' ')[c])) one_list[0]=num_class[c] atom_dict=one_list*(int(text[6].strip().split(' ')[c])) atom_list=atom_list+atom_dict # for n in range(num_atom):# position0.append(text[n+8].split())# print(num_atom)with open('vasprun.xml','r')as vasprun: text=vasprun.readlines() num_lines=len(text)for n in range(num_lines):# the original positions of atoms# if text[n] == " <varray name=\"positions\" >\n":# for m in range(num_atom):# position0.append(text[n+m+1].split())if text[n]==" <varray name=\"forces\" >\n": lattice=np.mat(np.zeros((3,3))) position=np.mat(np.zeros((num_atom,3))) force=np.mat(np.zeros((num_atom,3))) stress=np.mat(np.zeros((3,3))) i=i+1if i > s_step-1: j=j+1if((j-1)-d_step*((j-1)//d_step))==0: k=k+1#force.append(i)for lindex in np.arange(0,3,1): lattice_str=[float(lat)for lat in text[n-num_atom-14+lindex].split()[1:4]] lattice[lindex,:]=np.array(lattice_str) stress_str=[float(stre)for stre in text[n+num_atom+3+lindex].split()[1:4]]#print(stress_str) stress[lindex,:]=np.array(stress_str)*1000for m in range(num_atom): force_str=[float(f)for f in text[n+m+1].split()[1:4]] force[m,:]=np.array(force_str) position_str=[float(postr)for postr in text[n+m-num_atom-2].split()[1:4]] position_frac=np.array(position_str) position_cart=np.dot(lattice,position_frac.T) position[m,:]=position_cart struc_data["NumAtoms"]=num_atom struc_data["Lattice"]=lattice.tolist() struc_data["Energy"]=float(text[n+num_atom+9].split()[2]) struc_data["Stress"]=stress.tolist() struc_data["AtomTypes"]=atom_list struc_data["Positions"]=position.tolist() struc_data["Forces"]=force.tolist() struc_inf["Data"]=[struc_data] Dataset["Dataset"]=struc_inf config=json.dumps(Dataset) config_json=open("MD_{}.json".format(i),mode="w")print('# SNAP datasets',file=config_json)print(config, file=config_json)print("total_steps=",i)#print(j)print("output_steps=",k)

文章作者: [天帝君豪](http://tiandijunhao.github.io)

文章链接: [http://tiandijunhao.github.io/2020/07/10/grep-config-to-json-from-vasprunxml/](http://tiandijunhao.github.io/2020/07/10/grep-config-to-json-from-vasprunxml/)

版权声明: 本博客所有文章除特別声明外，均采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.zh) 许可协议。转载请注明来源 [天帝君豪](http://tiandijunhao.github.io) !

[计算脚本](https://tiandijunhao.github.io/tags/%E8%AE%A1%E7%AE%97%E8%84%9A%E6%9C%AC/)

上一篇

常用物理单位与物理常数

https://tiandijunhao.github.io/2020/07/12/chang-yong-wu-li-dan-wei-yu-wu-li-chang-shu/

MathJax.Hub.Config({ tex2jax: {inlineMath: [['$', '$']]}, messageStyle: "none" }); 计算中常见单位换算及部分物理常数物理常数普朗克常数： $h

2020-07-12 天帝君豪

下一篇

alamode_scph计算高温声子谱

https://tiandijunhao.github.io/2020/07/04/alamode-scph/

Alamode计算高温声子色散Anharmonic Phonons (self-consistent phonon theory)主要使用alamode软件。 版本：alamode-1.1.0 输入文件 vasprun.xml #分子动力学

2020-07-04 [计算笔记](https://tiandijunhao.github.io/categories/%E8%AE%A1%E7%AE%97%E7%AC%94%E8%AE%B0/)

[Anharmonic phonon](https://tiandijunhao.github.io/tags/Anharmonic-phonon/)

目录

搜索

# =============================================================================
# 参考脚本（从知乎问答收集 · 未运行验证）
# 名称    : 二维正方 Ising 模型的蒙特卡洛模拟（作者：Wang Suyun）
# 来源页面: articles/20261001-VASP如何计算居里温度_-_知乎.md
# 原文链接: https://www.zhihu.com/question/386477636（回答 /answer/2827745773）
# 用途    : 教学示例——用 Metropolis 蒙特卡洛扫描温度，统计 <E>、<E^2>、<M>、<M^2>、<|M|>、<M^4>，
#           由此得到热容 C 与磁化率 χ，用它们的峰值定位相变温度（Ising 的 Tc）。
# 依赖    : Python + numpy + matplotlib
# 抓取质量: ⚠️ 原网页把代码**压成了单行且丢掉了几乎所有空格/缩进**（`importnumpyasnp` 这种），
#           **不能直接运行**——使用时必须按 Python 语法重新断行缩进，并补齐被吞掉的空格。
#           （本库按"原样收集、未验证"的约定附在下面，不做改写。）
# 关键提示: ① 开尔文温度从高温往低温扫，可避免低温卡在局域态；
#           ② 每个温度点先跑 transient 步再统计（"瞬态"）；
#           ③ 计算总能量时要注意"每对相互作用被数了两次"，需除以 2。
# =============================================================================

#### 4 个回答
##################################################Author：Wang Suyun#################################################importnumpyasnpimportmatplotlib.pyplotaspltimportmath#计算函数# create postion:classpostion:x=Noney=Nonez=None
definitialize_lat(sizes):lat=np.zeros((sizes,sizes))# 定义晶格位置自旋量forxinrange(0,sizes,1):foryinrange(0,sizes):if(np.random.random()<0.5):lat[x,y]=1else:lat[x,y]=-1returnlat
defoutput(lat):sizes=lat.shape[0]forxinrange(0,sizes,1):foryinrange(0,sizes,1):if(lat[x,y]==1):print('+ ',end='')else:print('- ',end='')print(' ')
defchoose_random_pos_lat(lat):sizes=lat.shape[1]pos=postion()pos.x=np.random.randint(0,sizes)pos.y=np.random.randint(0,sizes)returnpos
deftest_flip(pos,lat,J,T):de=-2*energy_at_pos(pos,lat,J)# de为pos位置处的能量翻转之后的增量，pos是原位置if(de<0):returnTrue# 如果能量变化小于0，翻转else:# 如果能量变化大于0，按照概率翻转,概率为np.exp(-de/T)if(np.random.random()<np.exp(-de/(kb*T))):returnTrueelse:returnFalse
defflip(pos,lat):lat[pos.x,pos.y]=-lat[pos.x,pos.y]
deftransient_results(lat,J,T,transient=1000):foriinrange(0,transient):pos=choose_random_pos_lat(lat)if(test_flip(pos,lat,J,T)):flip(pos,lat)
deftotal_magnetization(lat):m=0.0sizes=lat.shape[0]foryinrange(0,sizes):forxinrange(0,sizes):m+=lat[x,y]returnm
deftotal_energy(lat):sizes=lat.shape[0]e=0.0foryinrange(0,sizes):forxinrange(0,sizes):pos=postion()pos.x=xpos.y=ye+=energy_at_pos(pos,lat)returnedefinitialize_value():# 初始化数据集x=np.array([])y1=np.array([])y2=np.array([])y3=np.array([])y4=np.array([])y5=np.array([])y6=np.array([])y7=np.array([])y8=np.array([])returnx,y1,y2,y3,y4,y5,y6,y7,y8
defenergy_at_pos(pos,lat,J=1.0):sizes=lat.shape[0]ifpos.y==(sizes-1):# 如果在最右边一列，那么右边的位置就是第一列right=0else:right=pos.y+1ifpos.y==0:# 如果在最左边一列，那么左边的位置就是最后一列left=sizes-1else:left=pos.y-1ifpos.x==(sizes-1):# 如果在最下面一行，那么下面的位置就是第一行down=0else:down=pos.x+1ifpos.x==0:# 如果在最上面一行，那么上面的位置就是最后一行up=sizes-1else:up=pos.x-1# 这个位置的能量就是这个点和最近邻点之间的相互作用能e=-J*lat[pos.x,pos.y]*(lat[up,pos.y]+lat[down,pos.y]+lat[pos.x,right]+lat[pos.x,left])returne
defcalculate(Tmin,Tmax,dT,J,sizes=10,mcs=2000,transient=1000):# 初始化数据lat=initialize_lat(sizes)n=lat.sizenorm=1.0/(mcs*n)#归一化因子x,y1,y2,y3,y4,y5,y6,y7,y8=initialize_value()print('初始结构：')output(lat)#-------------------------------------------------------------------# 计算# 温度从高到低进行降温，每次降温0.1，而不是从低到高。这样可以防止低温时出现局域化forTinnp.arange(Tmax,Tmin-dT,-dT):print(f'Calculating: T={T:.2f}K.....')# 先进行初步的瞬态transient_results(lat,J,T,transient)#output(lat)M=total_magnetization(lat)E=total_energy(lat)#initializeetot=0;etotsq=0;mtot=0mtotsq=0;mabstot=0;mqtot=0foriinrange(0,mcs):#mcs磁化步数forjinrange(0,n):#n是晶格总数pos=choose_random_pos_lat(lat)if(test_flip(pos,lat,J,T)):flip(pos,lat)# 如果翻转，翻转后能量的增量为2*energy_at_pos(pos)# 注意 这里的pos已经翻转了所以de和80行不一样de=2*energy_at_pos(pos,lat,J)# 这里乘2是因为总能量是每个能量都被计算了两次，所有能量都要乘2倍算入E+=2*de# 如果翻转，磁化强度变化为2*lat[pos.x,pos.y]M+=2*lat[pos.x,pos.y]# 如果翻转，绝对磁化强度变化为2*abs(lat[pos.x,pos.y])# Mab+=abs(lat[pos.x,pos.y])etot+=E/2# 求和etotsq+=E*E/4mtot+=Mmtotsq+=M*Mmqtot+=M*M*M*Mmabstot+=(math.sqrt(M*M))# 平均值 即MC模拟的结果E_avg=etot*norm# 能量平均值Esq_avg=etotsq*norm# 能量平方平均值M_avg=mtot*norm# 磁化强度平均值Msq_avg=mtotsq*norm# 磁化强度平方平均值Mabs_avg=mabstot*norm# 绝对磁化强度平均值Mq_avg=mqtot*norm# 磁化强度的四次方平均值C=(Esq_avg-E_avg*E_avg)/kb*T**2# 热容X=(Msq_avg-M_avg*M_avg)/kb*T# 磁化热力学性质# 记录每个温度下的绝对磁化强度平均值y1=np.append(y1,E_avg)y2=np.append(y2,Esq_avg)y3=np.append(y3,M_avg)y4=np.append(y4,Msq_avg)y5=np.append(y5,Mabs_avg)y6=np.append(y6,Mq_avg)y7=np.append(y7,C)y8=np.append(y8,X)x=np.append(x,T)print(f'末态结构(T={T:.2f}K)')output(lat)returnx,y1,y2,y3,y4,y5,y6,y7,y8
if__name__=='__main__':# 物理量kb=1.0# 初始化数据sizes=10# 晶格大小n=sizes*sizes# 晶格总数Tmin=0.5# 最低温度Tmax=5# 最高温度dT=0.1# 温度变化量lat=np.zeros((sizes,sizes))# 定义晶格位置自旋量mcs=5000# 磁化步数transient=5000# 磁相互作用强度：J=1.0x,y1,y2,y3,y4,y5,y6,y7,y8=calculate(Tmin,Tmax,dT,J,sizes=sizes,mcs=mcs,transient=transient)# 画图plotshow(x,y1,y2,y3,y4,y5,y6,y7,y8)

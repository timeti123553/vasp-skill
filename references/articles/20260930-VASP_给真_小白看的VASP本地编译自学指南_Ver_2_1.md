# 【VASP】给真·小白看的VASP本地编译自学指南 Ver 2.1

- 来源: `https://mp.weixin.qq.com/s/WD4xVA8BsXSXT-IWiumgkw`
- 类型: html (url)
- 抓取时间: 2026-09-30 23:23:51
- 作者: 徐张满仓
- 标签: 编译, 环境配置, 微信文章
- 正文字数: 18261

---
# 【VASP】给真·小白看的VASP本地编译自学指南 Ver 2.1

Original徐张满仓徐张满仓 学术之友

在小说阅读器读本章

去阅读

在公众号小说中沉浸阅读

[最近更新日期：2018年11月25日]

By：武汉理工大学-徐张满仓 欢迎转载

微信端显示效果有限，建议大家阅读原文，到他的个人主页中查看

本人水平有限，如有错误还望大家批评指正

致谢

想了一下，把致谢放在前面，当一个幸福的舔狗。

感谢北京理工大学的唐刚博士，在本人学习、编译VASP过程中给予的悉心指导。

感谢清华大学的刘锦程博士，提供了使用intel动态库进行VASP编译的简单方法。

感谢《Learn VASP The Hard Way》的作者李强博士。是他帮助和指导我们无数科研小白开启了VASP量化计算学习的大门。也正是因为强哥教程的启发，才有了本指南的写作。

微信公众号： BigBroScience （大师兄科研网）

大师兄QQ群：2674006510 进群

1）看群公告，了解群里的基本要求 2）修改自己的群名片。

同时也要感谢大师兄群内的许多师兄、师姐在本文写作中给于的帮助。

对于老鸟和时间较为紧张的选手，建议大家直接拖到最后：光速VASP编译指南

对于希望从头了解linux系统和vasp的同学，建议大家根据目录自行学习。

前言

首先自爆一下家门，我是来自武汉理工大学信息功能材料研究室直博一年级的计算小白，研究方向未定。根据笔者的个人观察，近一年来国内想要进行计算的课题组如雨后春笋般不断冒出，很多像我这样的计算新人初出茅庐，很多时候或是一腔热血或者”被计算“都正在或者即将走上量化计算这条道路。

大概6个月前，曾经写过一篇《给真·小白看的VASP本地编译及计算指南》，发布在个人的主页上。如今时隔半年时间，自己想在租用的云主机上重新编译VASP的时候发现依旧困难重重。

考虑到可能是自己对于LInux系统、编译原理等等知识都有所欠缺，这里打算进行一个较为详细的整理，关于一些Linux系统的基础知识、编译所需要的一些环境和库的知识以及一些解决问题的方法。

写作本指南的初衷：

网上如今流传的很多编译教程所针对的VASP版本均较为古老，一些教程写作也较为简略。很多时候能否编译成功都是瞎猫碰上死耗子。相信对于许多VASP初学来说，了解Linux的运行机制和编译VASP都是初学VASP的第一大门槛。

这个指南也是对自己在VASP学习过程中遇到的一系列问题进行的系统总结。

不指望自己的这份指南有多么专业、详细，只是希望能尽量帮助和我一样，初入计算领域，茫然无措又鲜有老师或师兄师姐能够求助的初学者，尽量多节省一些无畏的检索和试错时间；

这里想引述大师兄在书中的一段话：

如果你是看了本文去搜索并学习的小决窍，请记得分享给周围的人。

大师兄希望本文的读者都有一股乐于分享的精神，而不是自己学到了什么东西，偷偷揣在怀里。

如果你这么想:我自己学到的东西，凭什么教给别人。那么请:立即滚蛋，并立即停止阅读本书!大师兄自己学到的东西，辛苦总结的经验。凭什么让你这种人看。

如果你继续阅读本书，那么后面书中的每一个字， 每一个标点符号,空格,空行都时时刻刻代表着我向您致以最鄙视的敬意。直至你学会分享的精神为止。

本人无法阻止别人看我写的东西，但我可以通过写几句严厉的话把那些自私的人排除在读者之外。

我知道出于很多客观原因，大家各自都有一块属于自己的“实验田”，很多时候不愿意分享或者懒得分享自己的学习经验和感受。但我希望能够启发更多的人，互相分享学习心得和体会，共同进步与成长。

本教程适宜人群：

对于理论计算感兴趣，希望进行自主学习和尝试，但还没有进组的本科生或者是组内没有集群或机时的科研萌新；

课题组有相应集群或机时，但苦于组内资源有限，不便于或不愿意在集群上进行初步学习和实践的科研人员；

# 引言

编译VASP，到底是在做什么？

回答这个问题之前，我们首先要知道VASP到底是个什么东东。简而言之VASP是一款用高级语言（具体不清楚，也许是C + fortan）编写的量子化学计算软件。

这和我们平常接触到的带图形化界面的软件不同，在使用之前，我们需要使用相应的编译器，比如Intel® Parallel Studio XE（包含C、fortan语言的编译器），把高级语言“翻译”成机器能够理解的机器语言，得到一个vasp的可执行程序。

（关于编译器的详细解释，可以点击编译器）

根据vasp官方网站的介绍，我们可以知道，vasp就是一款通过近似求解Schrödinger方程得到体系的电子态和能量的程序。其既可以在密度泛函理论（DFT）框架内求解Kohn-Sham方程，也可以在Hartree-Fock（HF）的近似下求解Roothaan方程。其运行本质是一个矩阵的对角化运算。

From VASP官网 :（需要科学上网）

VASP computes an approximate solution to the many-body Schrödinger equation, either within density functional theory (DFT), solving the Kohn-Sham equations, or within the Hartree-Fock (HF) approximation, solving the Roothaan equations.

To determine the electronic groundstate, VASP makes use of efficient iterative matrix diagonalisation techniques, like the residual minimisation method with direct inversion of the iterative subspace (RMM-DIIS) or blocked Davidson algorithms. These are coupled to highly efficient Broyden and Pulay density mixing schemes to speed up the self-consistency cycle.

与此同时，我们为了提高计算效率，会希望vasp程序可以运行在服务器或大型集群上，这就要求我们可以在各节点之间进行通信，这是就需要相应的协议进行串联，比如mpi协议。

编译并行版的vasp需要并行编译器，例如MPI并行的程序需要MPI编译器，常用的MPI例如Intel MPI 、MPICH 、OPENMPI等。不同的机器可能针对自身硬件进行MPI优化，天河系统的MPI是基于开源MPICH进行的二次开发优化，进而支持性能卓越的天河自主高速互联网络。

from ：vasp 编译安装测试说明，author：MrZhengGang

除此之外，当vasp进行到空间傅里叶变换时还需要使用fftw等相应的数学库。

综合以上我们的介绍，似乎想要得到vasp的可执行程序还是比较繁琐的。但是好在如今的工具集非常齐全。我们只需要一个Intel® Parallel Studio XE 的并行工具集，既可以完成vasp的编译工作。因为该并行工具集下有vasp所需的编译器、并行协议和各种数学变换库。

只是intel的这套并行工具集并不开源而且收费，但是好在我们广大学子可以用edu邮箱申请免费试用版。（具体流程后文介绍）

# 使用指南

熟悉Linux和Vim基本操作的同志可以直接从第三章开始看起；

完全的新手建议大家从第一章开始看起，并百度or谷歌对自己不熟悉的名词，并且多多在linux环境下熟悉命令行的交互模式；

# 第1章 基础介绍

## 1.1 VASP版本选择

根据@刘锦程|THU同学在B站课程中的推荐，建议大家安装并使用最新版本5.4.4的VASP，编译难度低。使用超算需要编译vasp的同学可以直接看刘博士的视频。超算中的编译环境都已经安装好了，配置一下路径修改一下makefile即可直接编译。

固体与表面，番外篇3-五分钟搞定VASP编译

## 1.2 LInux版本选择

根据个人喜好，大家可以选择ubuntu或者centos的稳定版本即可。（ubuntu 16.04 or 18.04 ；Centos 7.4）

以下内容被强哥点评为XJBC。大家看看就好

具体怎么在本地安装linux系统建议大家自行百度解决。如果不会安装双系统、不方便安装双系统或者是电脑性能有限的同学，这里提供一个阿里云服务器的思路：

这个思路的优点在于：

不会因为重装系统对自己原本的系统造成损害；

1个月的服务器时长足够一时兴起的同学进行linux的学习和vasp的简单尝试与体验，来仔细考虑自己是否适合类似的科研方向和工作内容；

云上各种系统环境配置都比较容易，出现问题回滚和修复都较为方便；

随时随地可以用ipad等设备进行学习；

当然这个思路的缺点在于一个月的服务器价格大概在100-200元之间，还算是一笔不小的花销。这里建议大家至少选购2个cpu核心的服务器。

能够用100-200块钱提前尝试一下自己是否适合理论计算的操作环境和工作方式我觉得还是很值得的。当我们对vasp和理论计算有了一定的了解之后，可以再根据自己的需求进行设备的选择。

## 1.3 编译环境选择

网上很多编译教程因为种种原因，编译环境较为复杂，有很多引入openmpi等辅助，在本指南正建议大家直接使用较新版本的Intel® Parallel Studio XE工具集直接进行编译。其中含有vasp所需的各种库。并且据说运行效率还会更高。

# 第2章 基本操作

## 2.1 连接软件

这里主要介绍利用终端与服务器连接或者与自己的虚拟机交互；

当然利用虚拟机的同志也可以直接利用ubuntu等带图形界面的linux发行版；

租用服务器的同学可以考虑了解VNC的配置和使用；

阿里云轻量应用服务器-Ubuntu16-图形界面-VNC远程连接

### 2.1.1 Win生态系统

win下建议大家首先学会使用：winscp + putty，或xshell + xftp；

后续根据自己的需求使用其他更高级的终端：例如支持x11 server、VNC等功能的xmanager或mobaxterm等；

### 2.1.2 Apple生态系统

mac下：

终端：Terminal(mac自带终端)、iterm2、Termius均可，建议iterm2；

ftp ： filezilla、transmit

ipad + iphone建议大家使用：

Termius；

## 2.2 Linux基本操作

在进行linux学习之前，我们要先做好从图形化界面到命令行界面转换的心理准备。虽然linux有的也有相应的图形界面，但是在vasp的学习和实践过程中总是少不了对着命令行修修补补。

我个人感觉在习惯使用图形界面的交互模式之后，一开始会很不习惯命令行的交互模式，容错率低，界面单调，“似乎”效率低下，但是慢慢熟悉之后就会发现，利用命令行交互之后，所有可以用鼠标点击操作的事情都可以被一套指令所取代。

当遇到的操作问题变成简单地点击重复的时候，linux脚本的优势就会极大地体现出来。

所以对于新人来说，不要怕学习新东西麻烦，一点点的开始接触新的交互模式吧！

关于linux下的各中命令:

建议大家到如下网站自行查询学习：(在浏览器中按ctrl+f直接搜索相应命令既可)

或者在实际使用过程中，根据实际需求进行检索：

需求：建立文件夹。

就可以直接百度搜索： linux 建立文件夹 这样类似的关键词。

这一部分不建议大家干看书本，而是应该在终端中进行实际操作，慢慢感受和理解各种指令的作用。同时，我个人觉得应该是以需求引导学习，以项目入手（Project Baside Learning）。而不是一上来就图全部掌握，而过早失去了兴趣。

在输入基本指令之前，希望大家一定注意，linux是区分中英文输入法和字母大小写的。所以在输入的时候就一定要注意，切换到输入法的英文输入模式，并仔细核对大小写、空格等细节，避免输入错误

### 2.2.1 基本指令

本节中我们只介绍最最基本的linux指令，但学会这几个命令就足以进行vasp的编译了。

#### （1）磁盘管理（目录操作）

##### i. cd 命令

cd命令用于切换当前工作目录至 dirName(目录参数)。

示例：

cd /usr/bin # 跳到 /usr/bin/ 目录

cd ~ # 跳到自己的home目录，注意 cd和目录之间的空格

·cd ..` # 跳转到上一级目录

##### ii. ls 命令

ls命令用于显示指定工作目录下之内容（列出目前工作目录所含之文件及子目录)。

具体参数建议大家查看网页内容。

##### iii.pwd 命令

pwd命令用于显示工作目录。

执行pwd指令可立刻得知您目前所在的工作目录的绝对路径名称。

一般来说，我们在日常操作中，会把cd、ls、pwd这几个命令连用：使用ls查询目录下的文件或文件夹或使用pwd显示文件所在目录，使用cd命令进出文件夹。这个建议大家实地操作掌握。

pwd命令在后续编译过程的环境变量设置中也会十分有用。

#### （2）文件管理（新建、拷贝、删除、查看等）

##### i. mv 命令 —— 更名、移动

mv命令用来为文件或目录改名、或将文件或目录移入其它位置。

mv aaa bbb #将文件 aaa 更名为 bbb :

·mv info/ logs #将info目录放入logs目录中。注意，如果logs目录不存在，则该命令将info改名为logs。

##### ii. cp 命令 —— 拷贝

Linux cp命令主要用于复制文件或目录。

cp –r test/ newtest #使用指令”cp”将当前目录”test/“下的所有文件复制到新目录”newtest”下，输入如下命令：

##### iii. rm 命令 —— 删除

Linux rm命令用于删除一个文件或者目录。

rm test.txt #删除test.txt文件

##### iii. cat 命令 —— 查看

cat 命令用于连接文件并打印到标准输出设备上。

cat text.txt 屏幕显示test.txt文件中的内容

cat命令的用法还有很多，建议大家自行学习使用。但是编译阶段，我们只需要掌握基本的查看功能既可。除此之外你也可以了解：head、more、less、tail等不同查看命令的区别和用法。

### 2.2.2 编辑文档——Vim基本操作

上文我们提到了磁盘管理的相应内容，也包含文件的查看，接下来我们要掌握如何在linux下编辑文档的内容。

这一部分建议大家仔细阅读网页文档，并且一步一步在自己的终端进行实验，体会并理解vim的操作逻辑。

最主要的就是掌握：命令模式、底线模式和输入模式的切换。简言之，学会如何编辑和保存并关闭文档既可。

这一部分也是后续大家进行vasp编译和计算的基础，所以务必先掌握这一部分再进入后续内容的学习

### 2.2.3 环境变量

在讲解环境变量之前，我们需要对Linux这个系统有一个整体的理解。

Linux系统是一个多用户的操作系统。多个用户可以各自拥有和使用系统资源，即每个用户对自己的资源(例如：文件、设备)有特定的权限，互不影响，同时多个用户可以在同一时间以网络联机的方式使用计算机系统。而对于人机交互而言，我们如何与LInux这个系统进行交互呢？答案就是利用下面介绍的Shell。

Shell是什么：用户登录到Linux系统后，系统将启动一个用户shell。在这个shell中，可以使用shell命令或声明变量，也可以创建并运行shell脚本程序。我们在常见的LInux系统中，默认的shell叫做bash（Bourne Again Shell）具体大家可以百度查询。

运行shell脚本程序时，系统将创建一个子shell。此时，系统中将有两个shell，一个是登录时系统启动的shell，另一个是系统为运行脚本程序创建的shell。当一个脚本程序运行完毕，它的脚本shell将终止，可以返回到执行该脚本之前的shell。从这种意义上来说，用户可以有许多 shell，每个shell都是由某个shell（称为父shell）派生的。

Shell的详细内容建议大家去看鸟哥的私房菜中关于Shell的介绍：

理解了关于linux的系统特点和shell的含义之后，我们再来详细介绍环境变量到底做了什么。

#### （1）环境变量是什么

简而言之，环境变量相当于给系统或用户应用程序设置的一些参数，具体作用和具体的环境变量相关。比如path，是告诉系统，当要求系统运行一个程序而没有告诉它程序所在的完整路径时，系统除了在当前目录下面寻找此程序外，还应到哪些目录下去寻找。

而环境变量如何生效、环境变量生效的次序和流程等，是我们理解vasp编译的一个重难点

##### i. 不同目录下的profile和bashrc的区别

/etc/profile 为系统的每个用户设置环境变量，当第一个用户登录时，该文件被读取并执行。

/etc/bashrc 为每一个运行shell的用户设置环境变量，当shell被打开时，该文件被读取并执行。

~/. profile 每个用户都可使用该文件输入专用于自己使用的shell信息，当用户登录时，该文件仅仅执行一次。默认情况下，它设置一些环境变量，然后执行用户的.bashrc文件.

此文件类似于/etc/profile，也是需要需要重启才会生效，/etc/profile对所有用户生效，~/.bash_profile只对当前用户生效。

~/.bashrc 该文件包含专用于你的bash shell的bash信息,当登录时以及每次打开新的shell时,该文件被读取.（每个用户都有一个.bashrc文件，在用户目录下）

此文件类似于/etc/bashrc，不需要重启生效，重新打开一个bash即可生效， /etc/bashrc对所有用户新打开的bash都生效，但~/.bashrc只对当前用户新打开的bash生效。

##### ii. source和sh执行bash脚本的区别

#### （2）环境变量怎么设置

当我们理解了环境变量到底起了什么作用，source和sh的区别，那么我们就可以有针对性的，对不同的系统环境进行不同的配置。

如果你使用的是个人的虚拟机进行练习，完全可以在bashrc中进行修改。这样一次修改，一次生效，后续就不用再反复操作。

vi ~/.bashrc 进入编辑环境变量的文本文档

source ~/.bashrc 退出bashrc后，该命令使设置生效

如果你希望给不同的程序配置不同的编译环境，那么完全可以在命令行中使用source命令，把环境变量加载在当前的shell下。

# 第3章 编译环境准备

## 3.1 前期准备（安装必备库和兼容包）

根据部分老师、同学反映，有些版本的linux系统可能不需要安装如下所示的各种必备库和兼容包。

在这里给出的方案是，建议大家先跳过3.1节，直接去下载intel 2019编译器，从3.2节开始。当发现编译vasp出现问题后，再来进行相关库和兼容包的安装。

### 3.1.1 进行更新

服务器端：打开terminal，连接服务器；

虚拟机下，右键，open terminal。逐行输入如下内容按回车

sudo # 暂时获得系统root权限；

输入后，系统提示输入root密码，此时密码不会在面板显示，盲打后回车即可；

sudo apt-get update # 更新软件包的源地址

sudo apt-get upgrade# 升级已安装的所有软件包

### 3.1.2 操作系统的一些必备库

（包括gcc、g++、gcc，g++,build-essential等）

sudo apt-get install build-essential

sudo apt-get install libstdc++5

sudo apt-get install openjdk-8-jre

sudo apt-get install g++

sudo apt-get install gcc

### 3.1.3 安装32位系统的兼容包

sudo apt-get install libc6-dev-i386

sudo apt-get install gcc-multilib

sudo apt-get install g++-multilib

## 3.2 安装Intel编译环境

### 3.2.1 安装包获取

本人使用的安装包版本为2019 update1，授权版本为学生版，可以使用edu邮箱在intel官网进行注册获得。

### 3.2.2 具体安装步骤

解压安装包 tar –xvzf parallel_studio_xe_2019_update1_cluster_edition.tgz

进入安装包目录cd parallel_studio_xe_2019_update1_cluster_edition/

进行默认安装./install.sh

一路空格+回车，按照默认操作进行

选择使用serial number激活，serial number将会发送到你在Intel注册并认真的edu邮箱中

完成所有步骤后安装程序自动退出

设置环境变量

vi ~/.bashrc 进入编辑环境变量的文本文档

source /opt/intel/bin/compilervars.sh intel64 source /opt/intel/mkl/bin/mklvars.sh intel64

export PATH=/opt/intel/bin:$PATH

export LD_LIBRARY_PATH=/opt/intel

compilers_and_libraries_2019.1.144:$LD_LIBRARY_PATH

source ~/.bashrc 退出bashrc后，该命令使设置生效

注意：source关键词后链接的是一个bash脚本，这两个脚本分别是启用intel编译器和mkl编译器的脚本；

export后的PATH和LD_LIBRARY_PATH本质上是两个变量。PATH后面的路径一般被用来表示可执行程序的查找路径、LD_LIBRARY_PATH后面的路径一般被用来表示动态库的查找路径。

例如，PATH后链接的bin和mkl/bin目录，这两个目录下有很多二进制的可执行文件，是编译vasp所必须的。LD_LIBRARY_PATH所连接的路径则对应了一些动态库。

之所以删除上面export的几行文件，是因为其实在compilervars.sh和mklvars.sh这两个脚本中，本来就有相应的路径。不需要重复添加

方法一：ubuntu图形界面，找到home，按住ctrl+h，显示隐藏文件夹，打开.bashrc，在文件最后复制上述内容，保存并退出；

方法二：terminal中，vi ~/.bashrc，在vi模式下加入上述内容，退出并保存；

完成设置后在命令行中输入，source ~/.bashrc 使设置生效；

设置生效则会直接跳入下一行等待输入，设置失败则会报错

### 3.2.3 检查是否安装及配置成功

输入icc –v，如果出现icc version XX.X.X (gcc version X.X.X compatibility)则安装成功。

输入ifort –v ，出现ifort version XX.X.X即成功安装

输入which ifort，Enter显示路径;

输入echo $MKLROOT,Enter显示/安装目录/mkl；

## 3.3 编译intel fftw3

当我们准备好Intel编译器并设置好环境变量之后，我们的编译过程基本已经完成了80%。

对于这一步而言。如果我们希望用纯动态库来进行编译，那么我们可以省略这一步，因为intel并行工具集中有相应的动态库。

如果我们希望用静态库进行编译，步骤如下：

进入intel安装目录，找到fftw3xf这个子文件夹。比如我的intel目录在opt下：cd /opt/intel/mkl/interfaces/fftw3xf⁄

make libintel64编译完成后你就会得到libfftw3.mpi.a

## 3.4 动态库和静态库

Linux系统中，lib文件夹下会存有很多库文件，其中分别包括·a(静态库）或·o、.so（动态库）文件。

动态库静态库

名称示例libmkl_gf_ilp64.solibmkl_gf_lp64.a

编译特点库的代码不编译进程序里库的代码会编译进程序里

程序体积程序较小程序较大

运行需求环境变量中需要有动态库连接不需要有动态库连接

当我们使用静态库进行编译时，特点在于编译后的可执行程序可以方便复制给其他人使用；当我们使用动态库进行编译时，特点在于后续编译会较为简单，但可移植性会变差。

# 第4章 编译VASP

## 4.1 VASP获取

由于VASP是付费商业软件，需要课题组购买license获得授权并下载；

当然现在网络上也有很多相应版本的源代码包，各位可以自行百度。

## 4.2 编译VASP并行版本并试运行

解压vasp.5.4.4.tar.gz

进入到vasp.5.4.4目录中

cp makefile.include

根据自己的实际情况，获取相应的makefile.include文件，如果希望使用动态库，并且不希望详细了解makefile的同学，直接进行下一步，makefile.include文件可以一点都不修改，直接make。

在vasp5.4.4目录下执行 make all

这一步耗时较长，具体看电脑配置。完成编译后，在~/vasp-5.4.1/bin文件夹中会生成三个可执行文件

vasp_gam /gamma版本的vasp

vasp_std /标准版本的vasp

vasp_ncl /非线性版本的vasp

## 4.3 makefile文件初探

首先我们需要了解什么是makefile文件。

百度后结果如下：

一个工程中的源文件不计其数，其按类型、功能、模块分别放在若干个目录中，makefile定义了一系列的规则来指定，哪些文件需要先编译，哪些文件需要后编译，哪些文件需要重新编译，甚至于进行更复杂的功能操作，因为 makefile就像一个Shell脚本一样，其中也可以执行操作系统的命令。

简单来说，编译vasp的makefile文件，就是实现一个“自动化编译”的工作流，给源码指定一个编译顺序，指定编译所用的编译器、所需要实现的功能等等。

这也是vasp能否编译成功的重中之重。

### 4.3.1 模板获取

首先我们要知道，vasp压缩包内本身就是带有相应的编译模板的。

其具体目录在：

cd /解压目录/vasp.5.4.4/arch下。

我们可以看到arch文件夹下有四个文件：

makefile.include.linux_gnu

makefile.include.linux_intel_serial

makefile.include.linux_intel

makefile.include.linux_pgi

对于大多数需要本机编译的小伙使用的都是Intel全家桶，我们的编译器也是intel出品的，所以这里我们直接把这个配置文件拷贝到vasp.5.4.4根目录下。

cp makefile.include.linux_intel /安装目录/vasp.5.4.4

mv makefile.include.linux_intel makefile.include

### 4.3.2 makefile.include内容解读

对于图快，想要尽快完成编译的同学，我建议大家直接完成4.3.1模板获取之后，什么都不用进行修改，直接make all即可。因为如果不进行指定，那么makefile.inlcude文件会按照默认设定，选择ifortan编译器，会自动到MKLROOT目录下寻找相关的库，这个时候编译全部使用的是动态库。

这一部分的话，其实我个人也不是特别了解，只能简单根据网上的内容进行一些解读，以及告知大家编译需要修改的makefile的重点。

1.从CPP_OPTIONS到DEBUG这部分的内容建议大家不要随便修改。

FC=ifort：指的是fortan语言的编译使用intel fortan编译器进行。而之所以我们不用指定ifort的路径，是因为我们在安装好intel编译器后，已经在环境变量中设置了ifrot的环境变量。

CPP_OPTIONS和FLAG的相关内容我还没有太明白是怎么回事。有机会再详细说明。

2.MKLROOT到OBJECTS_O2的一系列内容都是指定vasp编译的各种库文件。这个时候我们需要理解几个名次和几个概念。

MKLROOT =/opt/intel/mkl MKL_PATH = $(MKLROOT)/lib/intel64 BLAS =-L$(MKL_PATH) -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lpthread LAPACK =-L$(MKL_PATH) -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lpthread BLACS =-L$(MKL_PATH) -lmkl_blacs_openmpi_lp64 SCALAPACK = $(MKL_PATH)/libmkl_scalapack_lp64.a $(MKL_PATH)/libmkl_scalapack_ilp64.a $(BLACS) OBJECTS = fftmpiw.o fftmpi_map.o fftw3d.o fft3dlib.o /opt/fftw/lib/libfftw3_mpi.a INCS =-I/opt/fftw/include

首先，MKLROOT和MKL_PATH都是指向库的路径。

Fortan语言：

Fortran语言是为了满足数值计算的需求而发展出来的一种编程语言。Fortran语言的最大特性是接近数学公式的自然描述，在计算机里具有很高的执行效率。它可以直接对矩阵和复数进行运算，自诞生以来广泛地应用于数值计算领域，积累了大量高效而可靠的源程序。许多科学计算库的底层实现都是采用的Fortran语言。VASP应该就是使用fortan语言写作的

BLAS

BLAS的全称是Basic Linear Algebra Subprograms，中文可以叫做基础线性代数子程序。它定义了一组应用程序接口（API）标准，是一系列初级操作的规范，如向量之间的乘法、矩阵之间的乘法等。许多数值计算软件库都实现了这一核心。BLAS是一组向量和矩阵运行的接口规范，也可以称为API规范。Netlib用fortran实现了BLAS的这些API接口，得到的库也叫做BLAS。Netlib只是一般性地实现了基本功能，并没有对运算做过多的优化。

BLACS

BLACS （Basic Linear Algebra Communication Subprograms），是一个专门为线性代数运算而设计的消息传递库；

LAPACK

LAPACK （linear algebra package），是著名的线性代数库，也是Netlib用fortran语言编写的。其底层是BLAS，在此基础上定义了很多矩阵和向量高级运算的函数，如矩阵分解、求逆和求奇异值等。该库的运行效率比BLAS库高。

从某个角度讲，LAPACK也可以称作是一组科学计算（矩阵运算）的接口规范。Netlib实现了这一组规范的功能，得到的这个库叫做LAPACK库。

前面BLAS和LAPACK的实现均是用的Fortran语言。为了方便c程序的调用，Netlib开发了CBLAS和CLAPACK。其本质是在BLAS和LAPACK的基础上，增加了c的调用方式。

ScaLAPACK

主要针对密集和带状线性代数系统，提供若干线性代数求解功能，如各种矩阵运算，矩阵分解，线性方程组求解，最小二乘问题，本征值问题，奇异值问题等，具有高效、可移植、可伸缩、高可靠性等优点，利用它的求解库可以开发出基于线性代数运算的并行应用程序。

上图中在水平线以下标记为 local 的软件成分是单处理器/单进程调用的，数据只存储在单进程上；在水平线以上标记为 global 的软件成分一般是同步并行调用的，其数据（矩阵或向量）分布在多个处理器/多个进程上。

接下来，我们要了解下面这样一行代码到底是什么意思：

BLAS =-L$(MKL_PATH) -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lpthread

-I (大写i)

编译程序按照-I指定的路进去搜索头文件。

-I/home/include/表示将-I/home/include/目录作为第一个寻找头文件的目录，寻找的顺序是：

/home/include/ →/usr/include→/usr/local/include

-L(大写l)

表示：编译程序按照－L指定的路进去寻找库文件，一般的在-L的后面可以一次用-l指定多个库文件。

-L/lib/表示到/lib/目录下找库文件

-l(小写l)

表示：编译程序到系统默认路进搜索，如果找不到，到当前目录，如果当前目录找不到，则到LD_LIBRARY_PATH等环境变量置顶的路进去查找，如果还找不到，那么编译程序提示找不到库。

那么上述句子的意思就是：

有关BLAS这个基础线性代数子程序的编译，到MKL_PATH的路径下去寻找库。找什么库呢？找libmkl_intel_lp64.a、libmkl_sequential.a等等这几个静态库。

所以我们修改MKLROOT和MKL_PATH这两个文件，以及设定环境变量的实质就是为了让VASP在编译时可以到指定的文件夹找到指定的库文件，然后调用他们。

我们主要需要修改的就是MKLROOT的路径，以及OBJECTS行中刚刚编译的libfftw3_mpi.a的路径:

OBJECTS = fftmpiw.o fftmpi_map.o fftw3d.o fft3dlib.o /opt/intel/mkl/interfaces/fftw3xf

至此我们就已经把VASP的makefile文件配置好了。

接下来，如果一些顺利，make all之后我们就可以开始计算了。

如果编译过程中出现错误，那我们就可以根据错误提示来进行调整。

如果提示缺失某个库文件，那么我们的工作流如下：

就需要首先考虑寻找这个库是不是在自己的电脑上：locate XXXX#这条命令会提示你是否有这个库，以及这个库具体在哪个位置

如果没有这个库，那你要考虑去哪里安装或者copy这个库，把到它应该做的位置，然后设置环境变量；

如果发现了这个库，那我们需要检查一下，环境变量是否设置正确；

而最为直接、粗暴的方法则是，把这个库文件直接copy或者move到编译出错提示的那个目录下，然后重新进行编译。

如果编译出现问题，建议大家第二次编译的时候执行 make veryclean指令，删除bin下的编译文件重新进行；

如果提示缺少某些库文件，我们也可以尝试把库文件丢到编译目录下，直接继续进行编译；

至此我们的VASP的编译应该就完成了。

因为个人知识有限，很难把各个方面都涉及的面面俱到。更多的问题建议大家还是多多百度、谷歌爬楼解决。当我们作为一个linux和vasp新人，把vasp编译搞定之后，基本上已经熟练了一些linux的基本操作。这样我们再去学习李强博士的Learn VASP The Hard Way课程就会更加的容易。

再给强哥打个广告：

微信公众号： BigBroScience （大师兄科研网）

大师兄QQ群：2674006510 进群1）看群公告，了解群里的基本要求 2）修改自己的群名片。

这里是结尾了，以下是小资料

# 小资料

## 编译器：

简单讲，编译器就是将“一种语言（通常为高级语言）”翻译为“另一种语言（通常为低级语言）”的程序。一个现代编译器的主要工作流程：源代码 (source code) → 预处理器 (preprocessor) → 编译器 (compiler) → 目标代码 (object code) → 链接器 (Linker) → 可执行程序 (executables)

高级计算机语言便于人编写，阅读交流，维护。机器语言是计算机能直接解读、运行的。编译器将汇编或高级计算机语言源程序（Source program）作为输入，翻译成目标语言（Target language）机器代码的等价程序。源代码一般为高级语言 (High-level language)， 如Pascal、C、C++、Java、汉语编程等或汇编语言，而目标则是机器语言的目标代码（Object code），有时也称作机器代码（Machine code）。

## Intel® Parallel Studio XE

The Intel® Parallel Studio XE Composer Edition includes compilers and performance libraries to improve development. These tools are included in all editions.

Intel® Parallel Studio XE是一款同时面向Window和Linux平台，既支持C/C++开发语言又支持Fortran开发语言的更高性能的并行开发工具集。

在Intel® Parallel Studio XE里，包含C++、Fortran等编译器以及一些数学库。

Intel® C++ Compiler

Intel® Fortran Compiler

Intel® Distribution for Python*

Intel® Math Kernel Library

Intel® Data Analytics Acceleration Library

Intel® Integrated Performance Primitives

Intel® Threading Building Blocks

## Intel® Math Kernel Library

Intel MKL，全称 Intel Math Kernel Library，提供经过高度优化和大量线程化处理的数学例程，面向性能要求极高的科学、工程及金融等领域的应用。MKL是一款商用函数库，提供C、Fortran 和 Fortran 95的支持，但仅支持Intel自家旗下的CPU。

## mpi

MPI＝message passing interface：在分布式内存（distributed-memory）之间实现信息通讯的一种规范/标准/协议（standard）。它是一个库，不是一门语言。可以被fortran，c，c++等调用。MPI 允许静态任务调度，显示并行提供了良好的性能和移植性，用 MPI 编写的程序可直接在多核集群上运行。在集群系统中，集群的各节点之间可以采用 MPI 编程模型进行程序设计，每个节点都有自己的内存，可以对本地的指令和数据直接进行访问，各节点之间通过互联网络进行消息传递，这样设计具有很好的可移植性，完备的异步通信功能，较强的可扩展性等优点。MPI 模型存在一些不足，包括：程序的分解、开发和调试相对困难，而且通常要求对代码做大量的改动；通信会造成很大的开销，为了最小化延迟，通常需要大的代码粒度；细粒度的并行会引发大量的通信；动态负载平衡困难；并行化改进需要大量地修改原有的串行代码，调试难度比较大

## fftw

FFTW ( the Faster Fourier Transform in the West) 是一个快速计算离散傅里叶变换的标准C语言程序集，其由MIT的M.Frigo 和S. Johnson 开发。可计算一维或多维实和复数据以及任意规模的DFT。

# 光速vasp编译指南

1. 安装包获取

本人使用的安装包版本为2019 update1，授权版本为学生版，可以使用edu邮箱在intel官网进行注册获得。

2. intel 2019并行工具集下载和安装

解压安装包 tar –xvzf parallel_studio_xe_2019_update1_cluster_edition.tgz

进入安装包目录cd parallel_studio_xe_2019_update1_cluster_edition/

进行默认安装./install.sh

一路空格+回车，按照默认操作进行

选择使用serial number激活，serial number将会发送到你在Intel注册并认真的edu邮箱中

完成所有步骤后安装程序自动退出

设置环境变量

source /opt/intel/bin/compilervars.sh intel64 source /opt/intel/mkl/bin/mklvars.sh intel64

echo $MKLROOT #检查环境变量是否生效

3. VASP.5.4.4编译

tar –zxvf vasp.5.4.4.tar.gz #解压vasp.5.4.4.tar.gz

gunzip patch.5.4.4.16052018.gz #解压vasp.5.4.4 patch

cd 进入到vasp.5.4.4目录中

cp patch.5.4.4.16052018 ./vasp.5.4.4 #复制patch到vasp根目录下

patch -p0 < patch.5.4.4.16052018 #patch

cd /解压目录/vasp.5.4.4/arch #从vasp/arch目录下找到intel模板

cp makefile.include.linux_intel /安装目录/vasp.5.4.4 #复制intel模板到vasp根目录

mv makefile.include.linux_intel makefile.include #获得makefile.include文件

在vasp5.4.4目录下执行 make all

完成编译后，在~/vasp-5.4.1/bin文件夹中会生成三个可执行文件

vasp_gam /gamma版本的vasp

vasp_std /标准版本的vasp

vasp_ncl /非线性版本的vasp

预览时标签不可点

Read more不喜欢

Scan to Follow

Got It

Scan with Weixin to

use this Mini Program

CancelAllow

CancelAllow

CancelAllow

微信扫一扫可打开此内容，

使用完整服务

: ，，，，，，，，，，，，.VideoMini ProgramLike，轻点两下取消赞Wow，轻点两下取消在看ShareCommentFavorite听过

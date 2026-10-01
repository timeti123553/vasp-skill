# string法自动寻找二维势能面上的MEP

- 来源: `https://mp.weixin.qq.com/s/FA7qH-U39HTVcEeMcf42CQ`
- 类型: html (url)
- 抓取时间: 2026-09-30 23:49:16
- 作者: ponychen
- 标签: PES, MEP, string法, 过渡态, 微信文章
- 正文字数: 2544

---
# string法自动寻找二维势能面上的MEP

Originalponychenponychen 学术之友

在小说阅读器读本章

去阅读

在公众号小说中沉浸阅读

前面详细介绍了(计算应力应变曲线脚本idealdeform.sh使用指南)和(vasp定压计算脚本vaspeqstress.sh使用教程)两个内容。今天介绍string法自动寻找二维势能面上最小能量路径(MEP)的python脚本。

势能面扫描在催化，功能等领域常常会被用到，其中尤以二维势能面用量最多(废话，搞成三维的咋看)。在之前文章中，tamas分享了如何使用python自动扫描势能面(PES，使用脚本绘制吸附势能面)，非常实用。不过我们好不容易绘制好势能面之后，寻找MEP往往是一个很头疼的问题。如果我们做的是NEB之类的话，最后得到的路径本身就是高维势能面上的MEP。尽管我们可以直接肉眼看出二维PES上的MEP，并且用PS等软件给他描上去。比如在(Dumitraschkewitz, Phillip, et al. "Impact of Alloying on Stacking Fault Energies in γ-TiAl." Applied Sciences 7.11 (2017): 1193.)这篇文章中，作者进行了γ -TiAl {111}面的广义层错能势能面扫描。

上下两幅图是同一个PES，代表不同的形变路径。从上图的MEP可以很快联想到，伴随位错分解，SISF转变为APB以后生成CSF是一种更优的形变机制。但是我们必须认识到，和很多文章一样，这种MEP往往是靠手直接加上，甚至直接用直接表示。对于直观的二维势能面来说，这很OK，完全不会影响文章结果。但是既然各种确定反应路径的方法如此好用，那为什么不干脆将这些手段用到二维PES上呢，就算多此一举，我们也不能将就。

结果我还没做就发现Xin Chen(GitHub主页见文末链接)三年前就做到了。好吧，既然都做了，那我又何必从零开始。我对Xin Chen的code使用python3重写，对核心模块进行了语句优化以增加以后的可扩展性，添加了CG算法,目前测试来说CG算法略微表现优异于原来的SD算法。同时我增加了draw.py提供快速查看收敛结果，增加了3个例子。经测试三次样条插值已经非常好使，所以我目前没有添加其他诸如B样条插值等手段。我将在以后有心情的时候添加NEB，dimer等算法。

本code使用string法(Weinan, E., Weiqing Ren, and Eric Vanden-Eijnden. "String method for the study of rare events." Physical Review B 66.5 (2002): 052301.)。我首先简要介绍一下这个方法。string法是一种跟NEB同属于chain of states方法的优秀的过渡态搜索算法。我们可以一句话概括这个算法，我们如果将一串很密的珠子放在PES上，让这些珠子自由朝能谷跑，最后稳定的状态就是MEP。它的本质公式如下

前项表示扣除平行于串珠分量的切线力，后项是一个约束用的拉格朗日乘子，在本code中，采用珠子均匀化作为一种最简单的约束。

下面我讲一下怎么使用该code.首先你需要安装ALGlib库，安装很简单，自己百度一下。然后你需要准备PES数据PES.data. 我这里用的都是example里面的数据。

第一栏为x轴，第二栏为y轴，第三栏为势能值。

然后你需要准备guess.data表示你建立的初猜路径。

第一行表示珠子个数，一般30到40个为宜。第二行为起点的x,y值，第三行为终点的x,y值。这个需要你对着势能面确定一下，不过不需要很精确，只要确保它们不跑到其他能谷就可以。你如果测试过就会发现string的稳定性有多强大。程序会根据你的参数建立一条线性插值的初始路径。

随后我们需要在MEPsearcher.py中修改某些参数。

这里主要说一下h。h表示每次位移的步长，这个你用默认也行。o表示使用sd或者cg算法，默认使用sd算法。基本上这四个参数你其实是不用改的。如果你觉的收敛不行，你就试试cg算法吧。

现在将两个输入文件放到MEPSearcher所在的主文件夹，run it。

程序每隔30步发送一次消息。成功后会告诉你收敛的总步数。这里面diff表示当前收敛差值。产生的MEP路径会保存在out.data中，它的格式和PES.data是一样的。我们可以运行draw.py观察结果。

红线表示初始路径，黑线表示MEP。效果还是很不错的。

我们也可以发现，string相对于NEB强大的优势在于，它的初态和末态并不是固定的，这就方便我们搭建初猜路径。但是这个优势仅限于二维的情况，道理我就不多说了。

写博文的这天我才知道，pymatgen也集成了类似的画MEP的功能，还是3D，还是动画，这就很尴尬了。无论如何string法还是更准确的嘛。我也只是把这个当作一个模型，以后可以简单地用来测试各种过渡态搜索算法。

ps：最近收到很多之前我发的脚本的询问和反馈，我会尽快回复，并不是没有看到哈。同时本文之后我就要闭关写文章了，下次更新应该比较后面了。

Xin Chen GitHub主页：

https://github.com/chenxin199261/MEPSearcher#opennewwindow

本文脚本下载链接：

http://lanzous.com/u/dft_family

预览时标签不可点

不喜欢

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

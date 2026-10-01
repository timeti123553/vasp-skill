#===============================================================================
# 参考脚本（原样收集 · 未验证 · 未运行）
# 来源文章: articles/20261001-VASP_vaspkit_STM_模拟.md
# 原文链接: https://zhuanlan.zhihu.com/p/667558468
# 用途    : 遍历当前目录 *.jpg，按非白像素边界裁掉四周空白（vaspkit 出的 STM 图留白多）
# 依赖    : Python + Pillow
# 功能说明: workflows.md 第十九节 / scripts/README.md 的 post/stm_frames.py（planned）（本目录只放源码文本，说明以那里为准）
# 抓取质量: 原文把脚本压成一整行（空格与换行全丢），只能读逻辑。
#===============================================================================
fromPILimportImageimportosdefcrop_all_borders(image_path):try:# 打开图像文件img=Image.open(image_path)# 获取图像的像素数据img_data=img.load()# 获取图像的尺寸width,height=img.size# 查找左边界left=0forxinrange(width):ifany(img_data[x,y]!=(255,255,255)foryinrange(height)):left=xbreak# 查找右边界right=width-1forxinrange(width-1,-1,-1):ifany(img_data[x,y]!=(255,255,255)foryinrange(height)):right=xbreak# 查找上边界top=0foryinrange(height):ifany(img_data[x,y]!=(255,255,255)forxinrange(width)):top=ybreak# 查找下边界bottom=height-1foryinrange(height-1,-1,-1):ifany(img_data[x,y]!=(255,255,255)forxinrange(width)):bottom=ybreak# 裁剪图像，去除所有边界的空白cropped_img=img.crop((left,top,right+1,bottom+1))# 保存裁剪后的图像cropped_img.save(image_path)print(f"已裁剪图像 {image_path}")exceptExceptionase:print(f"无法处理图像 {image_path}: {e}")defmain():# 获取当前目录下的所有jpg文件current_directory=os.getcwd()jpg_files=[fileforfileinos.listdir(current_directory)iffile.endswith(".jpg")]# 遍历每个jpg文件并进行裁剪forjpg_fileinjpg_files:image_path=os.path.join(current_directory,jpg_file)crop_all_borders(image_path)if__name__=="__main__":main()

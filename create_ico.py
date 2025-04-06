from PIL import Image

# 打开JPG图片
img = Image.open('zyx.JPG')
# 调整大小为标准图标尺寸
# img = img.resize((256, 256))
# 保存为ICO文件
img.save('zyx.ico', format='ICO')
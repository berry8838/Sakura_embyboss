# from PIL import Image, ImageDraw
#
#
# def round_corner(image, radius):
#     # 创建一个和原图一样大小的空白图片
#     mask = Image.new('L', image.size, 0)
#     draw = ImageDraw.Draw(mask)
#
#     # 绘制四个角的圆角
#     draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=255)
#     draw.pieslice((image.width - radius * 2, 0, image.width, radius * 2), 270, 360, fill=255)
#     draw.pieslice((0, image.height - radius * 2, radius * 2, image.height), 90, 180, fill=255)
#     draw.pieslice((image.width - radius * 2, image.height - radius * 2, image.width, image.height), 0, 90, fill=255)
#
#     # 填充四个角以外的区域
#     draw.rectangle([radius, 0, image.width - radius, image.height], fill=255)
#     draw.rectangle([0, radius, image.width, image.height - radius], fill=255)
#     mask.save('./t1.png', 'PNG')
#     # 使用alpha通道创建一个新的图像
#     result = Image.new('RGBA', image.size)
#     result.paste(image, mask=mask)
#     result.show()
#     return result
#
#
# # 打开图片
# image = Image.open('test300.jpg')
#
# # 裁剪圆角矩形
# rounded_image = round_corner(image, 75)  # 50是圆角的半径，可以根据需要调整
# 提前 做好蒙版不用一次次生成。保留代码

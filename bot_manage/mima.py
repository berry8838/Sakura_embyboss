# -*- coding:utf-8 -*-
"""
简短地生成随机密码，包括大小写字母、数字，可以指定密码长度
"""
# 生成随机密码
from random import choice
import string


# python3中为string.ascii_letters,而python2下则可以使用string.letters和string.ascii_letters

async def pwd_create(length=8, chars=string.ascii_letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])

# if __name__ == "__main__":
#     # 生成10个随机密码
#     for i in range(10):
#         # 密码的长度为8
#         print(pwd_create(8))

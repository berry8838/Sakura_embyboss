import asyncio
import os
import pytz
import random
import logging
from io import BytesIO
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from datetime import datetime
from bot.func_helper.emby import emby
import numpy as np

"""
日榜周榜海报样式
你可以根据你的需求自行封装或更改为你自己的周榜海报样式！
"""


class RanksDraw:
    red_bg_path = os.path.join('bot', 'ranks_helper', 'red', 'bg')
    red_bg_list = os.listdir(red_bg_path)
    red_mask = Image.open(os.path.join('bot', 'ranks_helper', 'red', 'red_mask.png')).convert('RGBA')
    zimu_font = os.path.join('bot', 'ranks_helper', "resource", 'font', "Provicali.otf")
    bold_font = os.path.join('bot', 'ranks_helper', "resource", 'font', "PingFang Bold.ttf")

    def __init__(self, embyname=None, weekly=False, backdrop=False):
        # 绘图文件路径初始化
        # wokr_p = os.getcwd()
        # print(wokr_p)
        bg_path = os.path.join('bot', 'ranks_helper', "resource", "bg")
        if weekly:
            if backdrop:
                mask_path = os.path.join('bot', 'ranks_helper', "resource", "week_ranks_mask_backdrop.png")
            else:
                mask_path = os.path.join('bot', 'ranks_helper', "resource", "week_ranks_mask.png")
        else:
            if backdrop:
                mask_path = os.path.join('bot', 'ranks_helper', "resource", "day_ranks_mask_backdrop.png")
            else:
                mask_path = os.path.join('bot', 'ranks_helper', "resource", "day_ranks_mask.png")
        font_path = os.path.join('bot', 'ranks_helper', "resource", 'font', "PingFang Bold.ttf")
        # 随机调取背景
        bg_list = os.listdir(bg_path)
        bg_path = os.path.join(bg_path, random.choice(bg_list))
        # 初始绘图对象
        self.bg = Image.open(bg_path)
        mask = Image.open(mask_path)
        self.bg = self.bg.resize(mask.size)
        self.bg.paste(mask, (0, 0), mask)
        self.font = ImageFont.truetype(font_path, 18)
        self.font_small = ImageFont.truetype(font_path, 14)
        self.font_count = ImageFont.truetype(font_path, 12)
        self.font_logo = ImageFont.truetype(font_path, 60)
        self.embyname = embyname
        self.backdrop = backdrop

    # backdrop_image 使用横版封面图绘制
    # draw_text 绘制item_name和播放次数
    async def draw(self, movies=[], tvshows=[], draw_text=False):
        text = ImageDraw.Draw(self.bg)
        # 合并绘制
        index = 0
        font_offset_y = 190
        resize = (0, 0)
        xy = (0, 0)
        for i in movies[:5]:
            # 榜单项数据
            user_id, item_id, item_type, name, count, duarion = tuple(i)
            # 封面图像获取
            if self.backdrop:
                resize = (242, 160)
                xy = (103 + 302 * index, 140)
                prisuccess, data = await emby.backdrop(item_id)
                if not prisuccess:
                    prisuccess, data = await emby.primary(item_id)
                    resize = (110, 160)
                    xy = (169 + 302 * index, 140)
            else:
                prisuccess, data = await emby.primary(item_id)
                resize = (144, 210)
                xy = (601, 162 + 230 * index)
            if not prisuccess:
                logging.error(f'【ranks_draw】获取封面图失败 {item_id} {name}')
            # 名称显示偏移
            temp_font = self.font
            # 名称超出长度缩小省略
            name = name[:7]
            try:
                # 绘制封面
                if prisuccess:
                    cover = Image.open(BytesIO(data))
                    cover = cover.resize(resize)
                    self.bg.paste(cover, xy)
            except Exception as e:
                prisuccess = False
                logging.error(f'【ranks_draw】绘制封面图失败 {item_id} {name} {e}')
                pass
            if not prisuccess:
                # 如果没有封面图，使用name来代替
                if self.backdrop:
                    draw_text_psd_style(text, (123 + 302 * index, 140), name, temp_font, 126)
                else:
                    draw_text_psd_style(text, (601, 162 + 230 * index), name, temp_font, 126)
            # 绘制 播放次数、影片名称
            if draw_text:
                draw_text_psd_style(text, (601 + 130, 163 + (230 * index)), str(count), self.font_count, 126)
                draw_text_psd_style(text, (601, 163 + font_offset_y + (230 * index)), name, temp_font, 126)
            index += 1
        # 剧集Y偏移
        index = 0
        # 名称显示偏移
        font_offset_y = 193
        for i in tvshows[:5]:
            # 榜单项数据
            user_id, item_id, item_type, name, count, duarion = tuple(i)
            # 图片获取，剧集主封面获取
            # 获取剧ID
            success, data = await emby.items(user_id, item_id)
            if success:
                item_id = data["SeriesId"]
            else:
                logging.error(f'【ranks_draw】获取剧集ID失败 {item_id} {name},根据名称开始搜索。')
                # ID错误时根据剧名搜索得到正确的ID
                ret_media = await emby.get_movies(title=name, start=0, limit=1)
                if ret_media:
                    item_id = ret_media[0]['item_id']
                    logging.info(f'{name} 已更新使用正确ID：{item_id}')
            # 封面图像获取
            if self.backdrop:
                prisuccess, data = await emby.backdrop(item_id)
                resize = (242, 160)
                xy = (408 + 302 * index, 444)
                if not prisuccess:
                    prisuccess, data = await emby.primary(item_id)
                    resize = (110, 160)
                    xy = (474 + 302 * index, 444)
            else:
                prisuccess, data = await emby.primary(item_id)
                resize = (144, 210)
                xy = (770, 985 - 232 * index)
            if not prisuccess:
                logging.error(f'【ranks_draw】获取剧集ID失败 {item_id} {name}')
            temp_font = self.font
            # 名称超出长度缩小省略
            name = name[:7]
            try:
                # 绘制封面
                if prisuccess:
                    cover = Image.open(BytesIO(data))
                    cover = cover.resize(resize)
                    self.bg.paste(cover, xy)
            except Exception as e:
                prisuccess = False
                logging.error(f'【ranks_draw】绘制封面图失败 {item_id} {name} {e}')
                pass
            if not prisuccess:
                # 如果没有封面图，使用name来代替
                if self.backdrop:
                    draw_text_psd_style(text, (428 + 302 * index, 444), name, temp_font, 126)
                else:
                    draw_text_psd_style(text, (770, 990 - 232 * index), name, temp_font, 126)
            # 绘制 播放次数、影片名称
            if draw_text:
                draw_text_psd_style(text, (770 + 130, 990 - (232 * index)), str(count), self.font_count, 126)
                draw_text_psd_style(text, (770, 990 + font_offset_y - (232 * index)), name, temp_font, 126)
            index += 1
        # 绘制Logo名字
        if self.embyname:
            if self.backdrop:
                draw_text_psd_style(text, (1900, 830), self.embyname, self.font_logo, 126, align='right')
            else:
                draw_text_psd_style(text, (90, 1100), self.embyname, self.font_logo, 126)

    def save(self,
             save_path=os.path.join('log', 'img',
                                    datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d.jpg"))):
        if not os.path.exists('log/img'): os.makedirs('log/img')
        if self.bg.mode in ("RGBA", "P"): self.bg = self.bg.convert("RGB")
        self.bg.save(save_path)
        return save_path

    def test(self, movies=[], tvshows=[], show_count=False):
        text = ImageDraw.Draw(self.bg)
        movies = [['8b734342caba4fc5ad0a20e4ede7e355', '264398', 'Movie', '目击者之追凶', '1', '159'],
                  ['36b3a8e7ef584505bc04f508b0ea1e44', '587042', 'Movie', '毒液：屠杀开始', '1', '26'],
                  ['818c49504587451fa6c1ce31ca60b120', '598910', 'Movie', '惊天营救2', '1', '4767'],
                  ['0e29b51ac6e544a39f3331342822efb4', '586588', 'Movie', '催眠', '1', '198']]
        tvshows = [['aca8c847cf674fe4b07ba44af7007cd1', '591980', 'Episode', '斗罗大陆', '42', '14834'],
                   ['7ed08d20dc044586aa8d4ac41d991e24', '599964', 'Episode', '冰海战记', '17', '246'],
                   ['2ecdc455ebf54af09404570237021a91', '547211', 'Episode', '火凤燎原', '14', '11919'],
                   ['c3b7524b43a046ae86de886bf4ab149e', '587029', 'Episode', '猎犬', '11', '2959'],
                   ['3503e261944f49029865e049eba16558', '554106', 'Episode', '小鸟之翼', '11', '1068'],
                   ['bd8fead9a07f4f2b9a4bc8221d7f0caf', '599433', 'Episode', '古相思曲', '10', '0'],
                   ['d128b00f17d848a98637eef6cd845119', '598182', 'Episode', '梦魇绝镇', '9', '17780'],
                   ['b614e1ba597c482c827eec9ff778c16b', '599280', 'Episode', '神女杂货铺', '8', '2713']]
        # 合并绘制
        index = 0
        font_offset_y = 190
        for i in movies[:5]:
            # 榜单项数据
            user_id, item_id, item_type, name, count, duarion = tuple(i)
            print(f'{item_type} {item_id} {name} {count}')
            # 名称显示偏移
            temp_font = self.font
            # 名称超出长度缩小省略
            name = name[:7]
            # 绘制封面
            cover = Image.open(os.path.join('bot', "ranks_helper", "resource", "test.png"))
            if self.backdrop:
                cover = cover.resize((242, 160))
                self.bg.paste(cover, (103 + 302 * index, 140))
            else:
                cover = cover.resize((144, 210))
                self.bg.paste(cover, (601, 162 + 230 * index))
            # 绘制 播放次数、影片名称
            if show_count:
                draw_text_psd_style(text, (601 + 130, 163 + (230 * index)), str(count), self.font_count, 126)
                draw_text_psd_style(text, (601, 163 + font_offset_y + (230 * index)), name, temp_font, 126)
            index += 1
        # 剧集Y偏移
        index = 0
        # 名称显示偏移
        font_offset_y = 193
        for i in tvshows[:5]:
            # 榜单项数据
            user_id, item_id, item_type, name, count, duarion = tuple(i)
            print(f'{item_type} {item_id} {name} {count}')
            temp_font = self.font
            # 名称超出长度缩小省略
            name = name[:7]
            # 绘制封面
            cover = Image.open(os.path.join('bot', "ranks_helper", "resource", "test1.png"))
            if self.backdrop:
                cover = cover.resize((242, 160))
                self.bg.paste(cover, (408 + 302 * index, 444))
            else:
                cover = cover.resize((144, 210))
                self.bg.paste(cover, (770, 985 - 232 * index))
            # 绘制 播放次数、影片名称
            if show_count:
                draw_text_psd_style(text, (770 + 130, 990 - (232 * index)), str(count), self.font_count, 126)
                draw_text_psd_style(text, (770, 990 + font_offset_y - (232 * index)), name, temp_font, 126)
            index += 1
        # 绘制Logo名字
        if self.embyname:
            if self.backdrop:
                draw_text_psd_style(text, (1900, 830), self.embyname, self.font_logo, 126, align='right')
            else:
                draw_text_psd_style(text, (90, 1100), self.embyname, self.font_logo, 126, align='left')

    @staticmethod
    async def hb_test_draw(money: int, members: int, user_pic: bytes = None, first_name: str = None):
        red_bg = os.path.join(RanksDraw.red_bg_path, random.choice(RanksDraw.red_bg_list))
        if not user_pic:
            cover = Image.open(red_bg)
            cover = await draw_cover_text(cover, first_name, money, members)
            img_bytes = BytesIO()
            cover.save(img_bytes, format='png')
            return img_bytes
        cover = Image.open(red_bg)
        # 获取 cover 的背景颜色
        bg_color = cover.getpixel((0, 0))
        try:
            _pic = Image.open(user_pic).convert('RGBA').resize((300, 300))
        except IOError:
            print("user_pic 不是有效的图片数据")
            return
        border = RanksDraw.red_mask.convert('L')
        _pic.putalpha(border)
        pic = convert_bgcc(_pic, bg_color)
        cover = draw_cover_text(cover, first_name, money, members)
        pic, cover = await asyncio.gather(pic, cover)
        cover.paste(pic, ((cover.width - _pic.width) // 2, 180))
        img_bytes = BytesIO()
        cover.save(img_bytes, format='png')  # 将image对象保存到BytesIO对象中
        return img_bytes  # 返回BytesIO


async def convert_bgcc(_pic, bg_color):
    # 将图像转换为 numpy 数组
    pic_array = np.array(_pic)
    # 创建一个 mask，标记出 _pic 中的透明像素
    mask = pic_array[..., 3] == 0
    # 将 _pic 中的透明像素替换为背景颜色
    pic_array[mask] = bg_color
    # 将 numpy 数组转换回 PIL 图像
    _pic = Image.fromarray(pic_array)
    return _pic


async def draw_cover_text(cover, first_name, money, members):
    draw = ImageDraw.Draw(cover)
    draw.text((cover.width // 2, 550), f'{first_name}红包',
              font=ImageFont.truetype(RanksDraw.bold_font, 50), anchor='mm', fill=(249, 219, 160))
    draw.text((cover.width // 2, cover.height - 100), f'{money} / {members}',
              font=ImageFont.truetype(RanksDraw.zimu_font, 60), anchor='mm', fill=(249, 219, 160))
    return cover


def draw_text_psd_style(draw, xy, text, font, tracking=0, leading=None, align='left', **kwargs):
    """
    usage: draw_text_psd_style(draw, (0, 0), "Test", 
                tracking=-0.1, leading=32, fill="Blue", align='left')

    Leading is measured from the baseline of one line of text to the
    baseline of the line above it. Baseline is the invisible line on which most
    letters—that is, those without descenders—sit. The default auto-leading
    option sets the leading at 120% of the type size (for example, 12‑point
    leading for 10‑point type).

    Tracking is measured in 1/1000 em, a unit of measure that is relative to 
    the current type size. In a 6 point font, 1 em equals 6 points; 
    in a 10 point font, 1 em equals 10 points. Tracking
    is strictly proportional to the current type size.
    """

    def stutter_chunk(lst, size, overlap=0, default=None):
        for i in range(0, len(lst), size - overlap):
            r = list(lst[i:i + size])
            while len(r) < size:
                r.append(default)
            yield r

    x, y = xy
    font_size = font.size
    lines = text.splitlines()
    if leading is None:
        leading = font.size * 1.2
        
    for line in lines:
        # 计算整行文本宽度
        total_width = font.getlength(line) + (tracking / 1000) * font_size * (len(line) - 1)
        
        # 如果是右对齐，调整起始 x 坐标
        current_x = x
        if align == 'right':
            current_x = x - total_width
            
        for a, b in stutter_chunk(line, 2, 1, ' '):
            w = font.getlength(a + b) - font.getlength(b)
            draw.text((current_x, y), a, font=font, **kwargs)
            current_x += w + (tracking / 1000) * font_size
        y += leading


# if __name__ == "__main__":
#     draw = RanksDraw(embyname='SAKURA欢迎你', weekly=True, backdrop=False)
#     draw.test()
#     draw.save()

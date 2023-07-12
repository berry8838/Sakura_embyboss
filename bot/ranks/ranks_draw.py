import os
import pytz
import random
import logging
from io import BytesIO
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from datetime import datetime
from bot.reply import emby

"""
日榜周榜海报样式
你可以根据你的需求自行封装或更改为你自己的周榜海报样式！
"""


class RanksDraw:

    def __init__(self, embyname=None, weekly = False, backdrop = False):
        # 绘图文件路径初始化
        bg_path = os.path.join('bot','ranks', "resource", "bg")
        if weekly:
            if backdrop:
                mask_path = os.path.join('bot','ranks', "resource", "week_ranks_mask_backdrop.png")
            else:
                mask_path = os.path.join('bot','ranks', "resource", "week_ranks_mask.png")
        else:
            if backdrop:
                mask_path = os.path.join('bot','ranks', "resource", "day_ranks_mask_backdrop.png")
            else:
                mask_path = os.path.join('bot','ranks', "resource", "day_ranks_mask.png")
        font_path = os.path.join('bot','ranks', "resource",'font', "PingFang Bold.ttf")
        logo_font_path = os.path.join('bot','ranks', 'resource','font', 'Provicali.otf')
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
        self.font_logo = ImageFont.truetype(logo_font_path, 100)
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
        xy = (0,0)
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
                    xy = (169 + 302 * index,  140)
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
            # 绘制封面
            if prisuccess:
                cover = Image.open(BytesIO(data))
                cover = cover.resize(resize)
                self.bg.paste(cover, xy)
            else:
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
            if not success:
                logging.error(f'【ranks_draw】获取剧集ID失败 {item_id} {name}')
            item_id = data["SeriesId"]
            # 封面图像获取
            if self.backdrop:
                prisuccess, data = await emby.backdrop(item_id)
                resize = (242, 160)
                xy = (408 + 302 * index,  444)
                if not prisuccess:
                    prisuccess, data = await emby.primary(item_id)
                    resize = (110, 160)
                    xy = (474 + 302 * index,  444)
            else:
                prisuccess, data = await emby.primary(item_id)
                resize = (144, 210)
                xy = (770, 985 - 232 * index)
            if not prisuccess:
                logging.error(f'【ranks_draw】获取剧集ID失败 {item_id} {name}')
            temp_font = self.font
            # 名称超出长度缩小省略
            name = name[:7]
            # 绘制封面
            if prisuccess:
                cover = Image.open(BytesIO(data))
                cover = cover.resize(resize)
                self.bg.paste(cover, xy)
            else:
                # 如果没有封面图，使用name来代替
                if self.backdrop:
                    draw_text_psd_style(text, (428 + 302 * index,  444), name, temp_font, 126)
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
                draw_text_psd_style(text, (1470, 830), self.embyname, self.font_logo, 126)
            else:
                draw_text_psd_style(text, (90, 1100), self.embyname, self.font_logo, 126)

    def save(self, save_path=os.path.join('log', datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d.jpg"))):
        if self.bg.mode in ("RGBA", "P"): self.bg = self.bg.convert("RGB")
        self.bg.save(save_path)
        return save_path
    def test(self, movies = [], tvshows=[], show_count=False):
        text = ImageDraw.Draw(self.bg)
        movies = [ ['8b734342caba4fc5ad0a20e4ede7e355', '264398', 'Movie', '目击者之追凶', '1', '159'], ['36b3a8e7ef584505bc04f508b0ea1e44', '587042', 'Movie', '毒液：屠杀开始', '1', '26'], ['818c49504587451fa6c1ce31ca60b120', '598910', 'Movie', '惊天营救2', '1', '4767'], ['0e29b51ac6e544a39f3331342822efb4', '586588', 'Movie', '催眠', '1', '198']]
        tvshows = [['aca8c847cf674fe4b07ba44af7007cd1', '591980', 'Episode', '斗罗大陆', '42', '14834'], ['7ed08d20dc044586aa8d4ac41d991e24', '599964', 'Episode', '冰海战记', '17', '246'], ['2ecdc455ebf54af09404570237021a91', '547211', 'Episode', '火凤燎原', '14', '11919'], ['c3b7524b43a046ae86de886bf4ab149e', '587029', 'Episode', '猎犬', '11', '2959'], ['3503e261944f49029865e049eba16558', '554106', 'Episode', '小鸟之翼', '11', '1068'], ['bd8fead9a07f4f2b9a4bc8221d7f0caf', '599433', 'Episode', '古相思曲', '10', '0'], ['d128b00f17d848a98637eef6cd845119', '598182', 'Episode', '梦魇绝镇', '9', '17780'], ['b614e1ba597c482c827eec9ff778c16b', '599280', 'Episode', '神女杂货铺', '8', '2713']]
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
            cover = Image.open(os.path.join('bot',"ranks", "resource", "test.png"))
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
            cover = Image.open(os.path.join('bot',"ranks", "resource", "test1.png"))
            if self.backdrop:
                cover = cover.resize((242, 160))
                self.bg.paste(cover, (408 + 302 * index,  444))
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
                draw_text_psd_style(text, (1470, 830), self.embyname, self.font_logo, 126)
            else:
                draw_text_psd_style(text, (90, 1100), self.embyname, self.font_logo, 126)

def draw_text_psd_style(draw, xy, text, font, tracking=0, leading=None, **kwargs):
    """
    usage: draw_text_psd_style(draw, (0, 0), "Test", 
                tracking=-0.1, leading=32, fill="Blue")

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
        for a, b in stutter_chunk(line, 2, 1, ' '):
            w = font.getlength(a + b) - font.getlength(b)
            draw.text((x, y), a, font=font, **kwargs)
            x += w + (tracking / 1000) * font_size
        y += leading
        x = xy[0]
# if __name__ == "__main__":
#     draw = RanksDraw(embyname='SAKURA', weekly = True, backdrop = True)
#     draw.test()
#     draw.save()
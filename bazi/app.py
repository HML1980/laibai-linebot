# -*- coding: utf-8 -*-
"""
籟柏八字排盤 LINE Bot - 完整版
命盤與運勢分開顯示，每個功能完成後可回主選單
"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction,
    FollowEvent, PostbackEvent, DatetimePickerAction
)
import os, hashlib
from datetime import datetime
import sxtwl

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN_BAZI', ''))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET_BAZI', ''))

# 天干地支
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
SHICHEN = ['子時(23-01)', '丑時(01-03)', '寅時(03-05)', '卯時(05-07)', '辰時(07-09)', '巳時(09-11)', 
           '午時(11-13)', '未時(13-15)', '申時(15-17)', '酉時(17-19)', '戌時(19-21)', '亥時(21-23)']

# 五行
WUXING_TG = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
WUXING_DZ = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}

# 地支藏干
CANGGAN = {
    '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'], '卯': ['乙'],
    '辰': ['戊', '乙', '癸'], '巳': ['丙', '戊', '庚'], '午': ['丁', '己'], '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'], '酉': ['辛'], '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲']
}

# 十神
SHISHEN_TABLE = {
    '甲': {'甲': '比肩', '乙': '劫財', '丙': '食神', '丁': '傷官', '戊': '偏財', '己': '正財', '庚': '七殺', '辛': '正官', '壬': '偏印', '癸': '正印'},
    '乙': {'乙': '比肩', '甲': '劫財', '丁': '食神', '丙': '傷官', '己': '偏財', '戊': '正財', '辛': '七殺', '庚': '正官', '癸': '偏印', '壬': '正印'},
    '丙': {'丙': '比肩', '丁': '劫財', '戊': '食神', '己': '傷官', '庚': '偏財', '辛': '正財', '壬': '七殺', '癸': '正官', '甲': '偏印', '乙': '正印'},
    '丁': {'丁': '比肩', '丙': '劫財', '己': '食神', '戊': '傷官', '辛': '偏財', '庚': '正財', '癸': '七殺', '壬': '正官', '乙': '偏印', '甲': '正印'},
    '戊': {'戊': '比肩', '己': '劫財', '庚': '食神', '辛': '傷官', '壬': '偏財', '癸': '正財', '甲': '七殺', '乙': '正官', '丙': '偏印', '丁': '正印'},
    '己': {'己': '比肩', '戊': '劫財', '辛': '食神', '庚': '傷官', '癸': '偏財', '壬': '正財', '乙': '七殺', '甲': '正官', '丁': '偏印', '丙': '正印'},
    '庚': {'庚': '比肩', '辛': '劫財', '壬': '食神', '癸': '傷官', '甲': '偏財', '乙': '正財', '丙': '七殺', '丁': '正官', '戊': '偏印', '己': '正印'},
    '辛': {'辛': '比肩', '庚': '劫財', '癸': '食神', '壬': '傷官', '乙': '偏財', '甲': '正財', '丁': '七殺', '丙': '正官', '己': '偏印', '戊': '正印'},
    '壬': {'壬': '比肩', '癸': '劫財', '甲': '食神', '乙': '傷官', '丙': '偏財', '丁': '正財', '戊': '七殺', '己': '正官', '庚': '偏印', '辛': '正印'},
    '癸': {'癸': '比肩', '壬': '劫財', '乙': '食神', '甲': '傷官', '丁': '偏財', '丙': '正財', '己': '七殺', '戊': '正官', '辛': '偏印', '庚': '正印'}
}

# 納音
NAYIN = {
    '甲子': '海中金', '乙丑': '海中金', '丙寅': '爐中火', '丁卯': '爐中火',
    '戊辰': '大林木', '己巳': '大林木', '庚午': '路旁土', '辛未': '路旁土',
    '壬申': '劍鋒金', '癸酉': '劍鋒金', '甲戌': '山頭火', '乙亥': '山頭火',
    '丙子': '澗下水', '丁丑': '澗下水', '戊寅': '城頭土', '己卯': '城頭土',
    '庚辰': '白蠟金', '辛巳': '白蠟金', '壬午': '楊柳木', '癸未': '楊柳木',
    '甲申': '泉中水', '乙酉': '泉中水', '丙戌': '屋上土', '丁亥': '屋上土',
    '戊子': '霹靂火', '己丑': '霹靂火', '庚寅': '松柏木', '辛卯': '松柏木',
    '壬辰': '長流水', '癸巳': '長流水', '甲午': '沙中金', '乙未': '沙中金',
    '丙申': '山下火', '丁酉': '山下火', '戊戌': '平地木', '己亥': '平地木',
    '庚子': '壁上土', '辛丑': '壁上土', '壬寅': '金箔金', '癸卯': '金箔金',
    '甲辰': '覆燈火', '乙巳': '覆燈火', '丙午': '天河水', '丁未': '天河水',
    '戊申': '大驛土', '己酉': '大驛土', '庚戌': '釵釧金', '辛亥': '釵釧金',
    '壬子': '桑柘木', '癸丑': '桑柘木', '甲寅': '大溪水', '乙卯': '大溪水',
    '丙辰': '沙中土', '丁巳': '沙中土', '戊午': '天上火', '己未': '天上火',
    '庚申': '石榴木', '辛酉': '石榴木', '壬戌': '大海水', '癸亥': '大海水'
}

# 日主性格
RIZHU_DESC = {
    '甲': {'name': '甲木', 'nature': '參天大樹', 'character': '正直堅毅、有領導力'},
    '乙': {'name': '乙木', 'nature': '花草藤蔓', 'character': '柔韌靈活、有藝術天分'},
    '丙': {'name': '丙火', 'nature': '太陽之火', 'character': '熱情開朗、有感染力'},
    '丁': {'name': '丁火', 'nature': '燭光之火', 'character': '溫和內斂、有洞察力'},
    '戊': {'name': '戊土', 'nature': '高山大地', 'character': '穩重可靠、有責任感'},
    '己': {'name': '己土', 'nature': '田園沃土', 'character': '務實謹慎、善於培育'},
    '庚': {'name': '庚金', 'nature': '刀劍之金', 'character': '剛毅果斷、重義氣'},
    '辛': {'name': '辛金', 'nature': '珠玉之金', 'character': '精緻優雅、有品味'},
    '壬': {'name': '壬水', 'nature': '江河大海', 'character': '智慧深遠、有遠見'},
    '癸': {'name': '癸水', 'nature': '雨露之水', 'character': '聰慧敏感、善解人意'}
}

user_states = {}

def calc_bazi(year, month, day, hour):
    """計算八字"""
    day_info = sxtwl.fromSolar(year, month, day)
    
    yg = TIANGAN[day_info.getYearGZ().tg]
    yz = DIZHI[day_info.getYearGZ().dz]
    mg = TIANGAN[day_info.getMonthGZ().tg]
    mz = DIZHI[day_info.getMonthGZ().dz]
    dg = TIANGAN[day_info.getDayGZ().tg]
    dz = DIZHI[day_info.getDayGZ().dz]
    
    hg_idx = (day_info.getDayGZ().tg % 5) * 2 + hour
    hg_idx = hg_idx % 10
    hg = TIANGAN[hg_idx]
    hz = DIZHI[hour]
    
    return {
        'year': yg + yz, 'month': mg + mz, 'day': dg + dz, 'hour': hg + hz,
        'year_gan': yg, 'year_zhi': yz, 'month_gan': mg, 'month_zhi': mz,
        'day_gan': dg, 'day_zhi': dz, 'hour_gan': hg, 'hour_zhi': hz,
        'dm': dg
    }

def get_canggan(zhi):
    return CANGGAN.get(zhi, [])

def get_shishen(day_gan, target_gan):
    return SHISHEN_TABLE.get(day_gan, {}).get(target_gan, '')

def get_nayin(ganzhi):
    return NAYIN.get(ganzhi, '')

def analyze_wuxing(bazi):
    """五行分析 - A算法"""
    wx = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
    for g in [bazi['year_gan'], bazi['month_gan'], bazi['day_gan'], bazi['hour_gan']]:
        wx[WUXING_TG[g]] += 1
    for z in [bazi['year_zhi'], bazi['month_zhi'], bazi['day_zhi'], bazi['hour_zhi']]:
        wx[WUXING_DZ[z]] += 1
    missing = [k for k, v in wx.items() if v == 0]
    return wx, missing

def calc_dayun(bazi, gender, year):
    """計算大運"""
    year_gan_idx = TIANGAN.index(bazi['year_gan'])
    yang_year = year_gan_idx % 2 == 0
    shun = (yang_year and gender == 'male') or (not yang_year and gender == 'female')
    
    month_gan_idx = TIANGAN.index(bazi['month_gan'])
    month_zhi_idx = DIZHI.index(bazi['month_zhi'])
    
    dayun_list = []
    for i in range(8):
        if shun:
            gan_idx = (month_gan_idx + i + 1) % 10
            zhi_idx = (month_zhi_idx + i + 1) % 12
        else:
            gan_idx = (month_gan_idx - i - 1) % 10
            zhi_idx = (month_zhi_idx - i - 1) % 12
        
        start_age = (i + 1) * 10 - 5
        dayun_list.append({
            'ganzhi': TIANGAN[gan_idx] + DIZHI[zhi_idx],
            'start': start_age, 'end': start_age + 9
        })
    return dayun_list

def judge_pattern(bazi, wx):
    """判斷格局"""
    dm = bazi['dm']
    dm_wx = WUXING_TG[dm]
    month_zhi = bazi['month_zhi']
    
    sheng_wx = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
    self_count = wx[dm_wx] + wx[sheng_wx[dm_wx]] * 0.5
    strength = '身強' if self_count >= 3 else '身弱'
    
    month_canggan = CANGGAN[month_zhi]
    pattern = '普通格局'
    for cg in month_canggan:
        ss = get_shishen(dm, cg)
        if ss in ['正官', '七殺', '正財', '偏財', '正印', '偏印', '食神', '傷官']:
            pattern = f"{ss}格"
            break
    return strength, pattern

def daily_fortune(uid):
    """每日運勢"""
    seed = int(hashlib.md5(f"{uid}{datetime.now():%Y%m%d}".encode()).hexdigest()[:8], 16)
    return {
        'overall': ['⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐⭐⭐'][seed % 3],
        'career': ['平穩發展', '有新機會', '貴人相助', '大展身手', '謹慎行事'][seed % 5],
        'wealth': ['小有收穫', '意外之財', '穩定增長', '開源節流', '投資宜慎'][seed % 5],
        'love': ['甜蜜時光', '桃花旺盛', '細水長流', '溝通為主', '靜待緣分'][(seed+1) % 5],
        'health': ['精神飽滿', '注意休息', '多運動', '飲食均衡', '早睡早起'][(seed+2) % 5],
        'lucky_num': (seed % 9) + 1,
        'lucky_color': ['紅色', '橙色', '黃色', '綠色', '藍色', '紫色', '白色', '金色'][seed % 8],
        'lucky_dir': ['東', '南', '西', '北', '東南', '東北', '西南', '西北'][seed % 8],
        'advice': ['把握機會展現自我', '穩紮穩打步步為營', '貴人運強多交朋友', '專注目標心無旁騖', '調整心態迎接挑戰'][(seed+3) % 5]
    }

def create_bazi_flex(bazi, wx, missing, strength, pattern, dayun, rizhu, year):
    """建立八字命盤 Flex Message（單獨一張卡片）"""
    dm = bazi['dm']
    nayin_year = get_nayin(bazi['year'])
    
    ss_year = get_shishen(dm, bazi['year_gan'])
    ss_month = get_shishen(dm, bazi['month_gan'])
    ss_hour = get_shishen(dm, bazi['hour_gan'])
    
    cg_year = ''.join(get_canggan(bazi['year_zhi']))
    cg_month = ''.join(get_canggan(bazi['month_zhi']))
    cg_day = ''.join(get_canggan(bazi['day_zhi']))
    cg_hour = ''.join(get_canggan(bazi['hour_zhi']))
    
    wx_str = ' '.join([f"{k}{v}" for k, v in wx.items()])
    missing_str = '、'.join(missing) if missing else '無'
    
    current_age = datetime.now().year - year
    dayun_str = ''
    for dy in dayun[:4]:
        mark = '←' if dy['start'] <= current_age <= dy['end'] else ''
        dayun_str += f"{dy['start']}-{dy['end']}: {dy['ganzhi']}{mark}\n"
    
    flex_content = {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box", "layout": "vertical",
            "contents": [{"type": "text", "text": "🔮 八字命盤", "weight": "bold", "size": "xl", "color": "#FFFFFF"}],
            "backgroundColor": "#8B4513", "paddingAll": "15px"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": "【四柱八字】", "weight": "bold", "color": "#8B4513", "size": "md"},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "年柱", "size": "xs", "color": "#888888", "flex": 1, "align": "center"},
                    {"type": "text", "text": "月柱", "size": "xs", "color": "#888888", "flex": 1, "align": "center"},
                    {"type": "text", "text": "日柱", "size": "xs", "color": "#888888", "flex": 1, "align": "center"},
                    {"type": "text", "text": "時柱", "size": "xs", "color": "#888888", "flex": 1, "align": "center"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": ss_year[:1] if ss_year else "", "size": "xs", "color": "#666666", "flex": 1, "align": "center"},
                    {"type": "text", "text": ss_month[:1] if ss_month else "", "size": "xs", "color": "#666666", "flex": 1, "align": "center"},
                    {"type": "text", "text": "日主", "size": "xs", "color": "#666666", "flex": 1, "align": "center"},
                    {"type": "text", "text": ss_hour[:1] if ss_hour else "", "size": "xs", "color": "#666666", "flex": 1, "align": "center"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": bazi['year'], "size": "xl", "weight": "bold", "flex": 1, "align": "center"},
                    {"type": "text", "text": bazi['month'], "size": "xl", "weight": "bold", "flex": 1, "align": "center"},
                    {"type": "text", "text": bazi['day'], "size": "xl", "weight": "bold", "flex": 1, "align": "center", "color": "#C41E3A"},
                    {"type": "text", "text": bazi['hour'], "size": "xl", "weight": "bold", "flex": 1, "align": "center"}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": f"藏{cg_year}", "size": "xxs", "color": "#888888", "flex": 1, "align": "center"},
                    {"type": "text", "text": f"藏{cg_month}", "size": "xxs", "color": "#888888", "flex": 1, "align": "center"},
                    {"type": "text", "text": f"藏{cg_day}", "size": "xxs", "color": "#888888", "flex": 1, "align": "center"},
                    {"type": "text", "text": f"藏{cg_hour}", "size": "xxs", "color": "#888888", "flex": 1, "align": "center"}
                ]},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": "【命理分析】", "weight": "bold", "color": "#8B4513", "size": "md", "margin": "md"},
                {"type": "text", "text": f"納音：{nayin_year}", "size": "sm"},
                {"type": "text", "text": f"日主：{rizhu['name']}（{rizhu['nature']}）", "size": "sm"},
                {"type": "text", "text": f"格局：{pattern}（{strength}）", "size": "sm"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": "【五行分析】", "weight": "bold", "color": "#8B4513", "size": "md", "margin": "md"},
                {"type": "text", "text": wx_str, "size": "sm"},
                {"type": "text", "text": f"五行缺：{missing_str}", "size": "sm", "color": "#C41E3A"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": f"【大運】現年{current_age}歲", "weight": "bold", "color": "#8B4513", "size": "md", "margin": "md"},
                {"type": "text", "text": dayun_str.strip(), "size": "sm", "wrap": True}
            ],
            "paddingAll": "15px"
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "🏠 回主選單", "text": "主選單"}, "style": "secondary", "height": "sm"}
            ],
            "paddingAll": "10px"
        }
    }
    return FlexSendMessage(alt_text='八字命盤', contents=flex_content)

def create_fortune_flex(fortune):
    """建立今日運勢 Flex Message（單獨一張卡片）"""
    flex_content = {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box", "layout": "vertical",
            "contents": [{"type": "text", "text": "🌟 今日運勢", "weight": "bold", "size": "xl", "color": "#FFFFFF"}],
            "backgroundColor": "#4169E1", "paddingAll": "15px"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": f"整體運勢：{fortune['overall']}", "size": "lg", "weight": "bold"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": "【各方面運勢】", "weight": "bold", "color": "#4169E1", "size": "md", "margin": "md"},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "💼 事業", "size": "sm", "flex": 2},
                    {"type": "text", "text": fortune['career'], "size": "sm", "flex": 3}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "💰 財運", "size": "sm", "flex": 2},
                    {"type": "text", "text": fortune['wealth'], "size": "sm", "flex": 3}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "💕 感情", "size": "sm", "flex": 2},
                    {"type": "text", "text": fortune['love'], "size": "sm", "flex": 3}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "💪 健康", "size": "sm", "flex": 2},
                    {"type": "text", "text": fortune['health'], "size": "sm", "flex": 3}
                ]},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": "【開運指南】", "weight": "bold", "color": "#4169E1", "size": "md", "margin": "md"},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "🔢 幸運數字", "size": "sm", "flex": 2},
                    {"type": "text", "text": str(fortune['lucky_num']), "size": "sm", "flex": 3}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "🎨 幸運色", "size": "sm", "flex": 2},
                    {"type": "text", "text": fortune['lucky_color'], "size": "sm", "flex": 3}
                ]},
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "🧭 吉利方位", "size": "sm", "flex": 2},
                    {"type": "text", "text": fortune['lucky_dir'], "size": "sm", "flex": 3}
                ]},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": "💡 今日提醒", "weight": "bold", "color": "#4169E1", "size": "md", "margin": "md"},
                {"type": "text", "text": fortune['advice'], "size": "sm", "wrap": True}
            ],
            "paddingAll": "15px"
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": f"日期：{datetime.now():%Y/%m/%d}", "size": "xs", "color": "#AAAAAA", "align": "center"},
                {"type": "button", "action": {"type": "message", "label": "🏠 回主選單", "text": "主選單"}, "style": "secondary", "height": "sm", "margin": "md"}
            ],
            "paddingAll": "10px"
        }
    }
    return FlexSendMessage(alt_text='今日運勢', contents=flex_content)

def create_menu_flex():
    """建立主選單 Flex Message"""
    flex_content = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🔮 籟柏八字", "weight": "bold", "size": "xl", "color": "#FFFFFF"},
                {"type": "text", "text": "專業命理分析・免費服務", "size": "sm", "color": "#FFFFFF"}
            ],
            "backgroundColor": "#8B4513", "paddingAll": "20px"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "lg",
            "contents": [
                {"type": "text", "text": "請選擇功能", "weight": "bold", "size": "lg", "align": "center"},
                {"type": "separator"},
                {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
                    {"type": "text", "text": "🔮 排盤", "size": "md", "weight": "bold"},
                    {"type": "text", "text": "完整八字命盤分析", "size": "sm", "color": "#666666"},
                    {"type": "text", "text": "四柱、藏干、十神、五行、大運", "size": "xs", "color": "#888888"}
                ]},
                {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
                    {"type": "text", "text": "🌟 今日運勢", "size": "md", "weight": "bold"},
                    {"type": "text", "text": "每日運勢預測", "size": "sm", "color": "#666666"},
                    {"type": "text", "text": "事業、財運、感情、健康、開運指南", "size": "xs", "color": "#888888"}
                ]}
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box", "layout": "horizontal", "spacing": "md",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "🔮 排盤", "text": "排盤"}, "style": "primary", "color": "#8B4513"},
                {"type": "button", "action": {"type": "message", "label": "🌟 今日運勢", "text": "今日運勢"}, "style": "primary", "color": "#4169E1"}
            ],
            "paddingAll": "15px"
        }
    }
    return FlexSendMessage(alt_text='籟柏八字主選單', contents=flex_content)

def create_date_picker_flex():
    """建立日期選擇器"""
    flex_content = {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "contents": [{"type": "text", "text": "🔮 八字排盤", "weight": "bold", "size": "lg", "color": "#FFFFFF"}],
            "backgroundColor": "#8B4513", "paddingAll": "15px"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": "請選擇您的出生日期", "weight": "bold", "size": "md"},
                {"type": "text", "text": "點選下方按鈕選擇日期", "size": "sm", "color": "#666666"},
                {"type": "button",
                 "action": {
                     "type": "datetimepicker",
                     "label": "📅 選擇出生日期",
                     "data": "action=select_date",
                     "mode": "date",
                     "initial": "1990-01-01",
                     "max": datetime.now().strftime("%Y-%m-%d"),
                     "min": "1920-01-01"
                 },
                 "style": "primary", "color": "#8B4513", "margin": "md"
                },
                {"type": "button",
                 "action": {"type": "message", "label": "🏠 回主選單", "text": "主選單"},
                 "style": "secondary", "margin": "sm"
                }
            ],
            "paddingAll": "15px"
        }
    }
    return FlexSendMessage(alt_text='選擇出生日期', contents=flex_content)

@app.route('/callback', methods=['POST'])
def callback():
    sig = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, sig)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@app.route('/health')
def health():
    return 'OK'

@handler.add(FollowEvent)
def handle_follow(event):
    """加好友歡迎訊息"""
    flex_msg = create_menu_flex()
    line_bot_api.reply_message(event.reply_token, flex_msg)

@handler.add(PostbackEvent)
def handle_postback(event):
    """處理日期選擇器回傳"""
    uid = event.source.user_id
    data = event.postback.data
    
    if data == "action=select_date":
        date_str = event.postback.params.get('date', '')
        if date_str:
            y, m, d = map(int, date_str.split('-'))
            user_states[uid] = {'step': 'hour', 'y': y, 'm': m, 'd': d}
            qr = QuickReply(items=[QuickReplyButton(action=MessageAction(label=s, text=s)) for s in SHICHEN])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                f'📅 出生日期：{y}年{m}月{d}日\n\n請選擇出生時辰：', quick_reply=qr))

@handler.add(MessageEvent, message=TextMessage)
def handle(event):
    uid, txt = event.source.user_id, event.message.text.strip()
    
    if uid in user_states:
        st = user_states[uid]
        
        if st['step'] == 'hour':
            hr = next((i for i, s in enumerate(SHICHEN) if s in txt), -1)
            if hr == -1:
                line_bot_api.reply_message(event.reply_token, TextSendMessage('請選擇正確時辰'))
                return
            user_states[uid] = {**st, 'step': 'gender', 'hour': hr}
            qr = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label='👨 男', text='男')),
                QuickReplyButton(action=MessageAction(label='👩 女', text='女'))
            ])
            line_bot_api.reply_message(event.reply_token, TextSendMessage('請選擇性別（影響大運順逆）：', quick_reply=qr))
            return
        
        elif st['step'] == 'gender':
            gender = 'male' if '男' in txt else 'female'
            y, m, d, hr = st['y'], st['m'], st['d'], st['hour']
            del user_states[uid]
            
            try:
                bazi = calc_bazi(y, m, d, hr)
                wx, missing = analyze_wuxing(bazi)
                strength, pattern = judge_pattern(bazi, wx)
                dayun = calc_dayun(bazi, gender, y)
                rizhu = RIZHU_DESC[bazi['dm']]
                
                flex_msg = create_bazi_flex(bazi, wx, missing, strength, pattern, dayun, rizhu, y)
                line_bot_api.reply_message(event.reply_token, flex_msg)
            except Exception as e:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(f'排盤錯誤：{str(e)}'))
            return
    
    # 主選單
    if txt in ['主選單', '選單', 'menu', '首頁', '回首頁']:
        flex_msg = create_menu_flex()
        line_bot_api.reply_message(event.reply_token, flex_msg)
    
    # 排盤
    elif txt in ['排盤', '八字', '命盤', '八字排盤']:
        flex_msg = create_date_picker_flex()
        line_bot_api.reply_message(event.reply_token, flex_msg)
    
    # 今日運勢
    elif txt in ['今日運勢', '運勢', '今日']:
        fortune = daily_fortune(uid)
        flex_msg = create_fortune_flex(fortune)
        line_bot_api.reply_message(event.reply_token, flex_msg)
    
    # 說明
    elif txt in ['說明', '功能', '幫助', 'help', '你好', 'hi', 'Hi', '嗨']:
        flex_msg = create_menu_flex()
        line_bot_api.reply_message(event.reply_token, flex_msg)
    
    # 其他
    else:
        flex_msg = create_menu_flex()
        line_bot_api.reply_message(event.reply_token, flex_msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

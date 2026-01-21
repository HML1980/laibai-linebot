# -*- coding: utf-8 -*-
"""
籟柏紫微斗數 LINE Bot
使用 iztro-py 純 Python 庫進行精確排盤
"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction,
    FollowEvent, PostbackEvent, DatetimePickerAction
)
import os
from datetime import datetime
from iztro_py import astro

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN_ZIWEI', ''))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET_ZIWEI', ''))

# 時辰對照
SHICHEN = ['子時(23-01)', '丑時(01-03)', '寅時(03-05)', '卯時(05-07)', '辰時(07-09)', '巳時(09-11)', 
           '午時(11-13)', '未時(13-15)', '申時(15-17)', '酉時(17-19)', '戌時(19-21)', '亥時(21-23)']

# 星名英轉中對照表
STAR_NAMES = {
    'ziweiMaj': '紫微', 'tianjiMaj': '天機', 'taiyangMaj': '太陽', 'wuquMaj': '武曲',
    'tiantongMaj': '天同', 'lianzhenMaj': '廉貞', 'tianfuMaj': '天府', 'taiyinMaj': '太陰',
    'tanlangMaj': '貪狼', 'jumenMaj': '巨門', 'tianxiangMaj': '天相', 'tianliangMaj': '天梁',
    'qishaMaj': '七殺', 'pojunMaj': '破軍',
    # 輔星
    'zuofuMin': '左輔', 'youbiMin': '右弼', 'wenchangMin': '文昌', 'wenquMin': '文曲',
    'lucunMin': '祿存', 'tianmaMin': '天馬', 'qingyangMin': '擎羊', 'tuoluoMin': '陀羅',
    'huoxingMin': '火星', 'lingxingMin': '鈴星', 'tiankuiMin': '天魁', 'tianyueMin': '天鉞',
    'dikongMin': '地空', 'dijieMin': '地劫'
}

# 宮位英轉中
PALACE_NAMES = {
    'soulPalace': '命宮', 'siblingsPalace': '兄弟', 'spousePalace': '夫妻',
    'childrenPalace': '子女', 'wealthPalace': '財帛', 'healthPalace': '疾厄',
    'surfacePalace': '遷移', 'friendsPalace': '交友', 'careerPalace': '官祿',
    'propertyPalace': '田宅', 'spiritPalace': '福德', 'parentsPalace': '父母'
}

user_states = {}

# 生肖對照
ZODIAC_LIST = ['鼠', '牛', '虎', '兔', '龍', '蛇', '馬', '羊', '猴', '雞', '狗', '豬']

def get_correct_zodiac(lunar_date_str):
    """根據農曆年份計算正確生肖"""
    # 從農曆日期字串提取年份，例如 "1979年腊月初九" -> 1979
    import re
    match = re.search(r'(\d{4})年', lunar_date_str)
    if match:
        lunar_year = int(match.group(1))
        # 1900年是鼠年，以此為基準
        zodiac_idx = (lunar_year - 1900) % 12
        return ZODIAC_LIST[zodiac_idx]
    return ""

def translate_star(star_code):
    """翻譯星名"""
    # 移除亮度和四化標記
    base = star_code.split('(')[0].split('[')[0]
    name = STAR_NAMES.get(base, base)
    
    # 加回亮度
    if '(' in star_code:
        brightness = star_code.split('(')[1].split(')')[0]
        name += f"({brightness})"
    
    # 加回四化
    if '[' in star_code:
        mutagen = star_code.split('[')[1].split(']')[0]
        name += f"[{mutagen}]"
    
    return name

def get_ziwei_chart(year, month, day, hour_idx, gender):
    """取得紫微斗數命盤"""
    date_str = f"{year}-{month}-{day}"
    gender_str = "男" if gender == "male" else "女"
    result = astro.by_solar(date_str, hour_idx, gender_str, 'zh-TW')
    return result

def create_ziwei_flex(result, year):
    """建立紫微斗數 Flex Message"""
    
    # 基本資訊
    lunar_date = str(result.lunar_date) if hasattr(result, 'lunar_date') else ""
    five_elements = str(result.five_elements_class) if hasattr(result, 'five_elements_class') else ""
    zodiac = get_correct_zodiac(lunar_date)  # 使用修正的生肖計算
    sign = str(result.sign) if hasattr(result, 'sign') else ""
    
    # 命主身主
    soul_star = STAR_NAMES.get(str(result.soul), str(result.soul)) if hasattr(result, 'soul') else ""
    body_star = STAR_NAMES.get(str(result.body), str(result.body)) if hasattr(result, 'body') else ""
    
    # 解析十二宮
    palaces_text = []
    result_str = str(result)
    
    # 從字串解析宮位
    lines = result_str.split('\n')
    ming_stars = ""
    shen_palace = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 解析宮位行
        for eng_name, chi_name in PALACE_NAMES.items():
            if eng_name in line:
                # 取得星曜
                if ':' in line:
                    stars_part = line.split(':')[1].strip()
                    stars = []
                    for s in stars_part.split(','):
                        s = s.strip()
                        if s:
                            stars.append(translate_star(s))
                    stars_str = '、'.join(stars) if stars else '空宮'
                else:
                    stars_str = '空宮'
                
                # 檢查命宮和身宮標記
                mark = ""
                if '[命]' in line:
                    mark = "【命】"
                    ming_stars = stars_str
                if '[身]' in line:
                    mark += "【身】"
                    shen_palace = chi_name
                
                palaces_text.append(f"{chi_name}{mark}: {stars_str}")
                break
    
    palace_display = '\n'.join(palaces_text) if palaces_text else "解析中..."
    current_age = datetime.now().year - year
    
    flex_content = {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🌟 紫微斗數命盤", "weight": "bold", "size": "xl", "color": "#FFFFFF"}
            ],
            "backgroundColor": "#6A0DAD", "paddingAll": "15px"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": "【基本資料】", "weight": "bold", "color": "#6A0DAD", "size": "md"},
                {"type": "text", "text": f"農曆：{lunar_date}", "size": "sm"},
                {"type": "text", "text": f"生肖：{zodiac}　星座：{sign}", "size": "sm"},
                {"type": "text", "text": f"五行局：{five_elements}", "size": "sm", "color": "#C41E3A"},
                {"type": "separator", "margin": "md"},
                
                {"type": "text", "text": "【命身資訊】", "weight": "bold", "color": "#6A0DAD", "size": "md", "margin": "md"},
                {"type": "text", "text": f"命宮主星：{ming_stars}", "size": "sm", "weight": "bold"},
                {"type": "text", "text": f"命主：{soul_star}　身主：{body_star}", "size": "sm"},
                {"type": "separator", "margin": "md"},
                
                {"type": "text", "text": "【十二宮】", "weight": "bold", "color": "#6A0DAD", "size": "md", "margin": "md"},
                {"type": "text", "text": palace_display, "size": "xs", "wrap": True},
            ],
            "paddingAll": "15px"
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": "籟柏紫微 ✨ 免費服務", "size": "xs", "color": "#AAAAAA", "align": "center"},
                {"type": "button", "action": {"type": "message", "label": "🏠 回主選單", "text": "主選單"}, "style": "secondary", "height": "sm", "margin": "md"}
            ],
            "paddingAll": "10px"
        }
    }
    return FlexSendMessage(alt_text='紫微斗數命盤', contents=flex_content)

def create_menu_flex():
    """建立主選單"""
    flex_content = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🌟 籟柏紫微斗數", "weight": "bold", "size": "xl", "color": "#FFFFFF"},
                {"type": "text", "text": "專業命理分析・免費服務", "size": "sm", "color": "#FFFFFF"}
            ],
            "backgroundColor": "#6A0DAD", "paddingAll": "20px"
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "lg",
            "contents": [
                {"type": "text", "text": "請選擇功能", "weight": "bold", "size": "lg", "align": "center"},
                {"type": "separator"},
                {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
                    {"type": "text", "text": "🌟 排盤", "size": "md", "weight": "bold"},
                    {"type": "text", "text": "完整紫微斗數命盤", "size": "sm", "color": "#666666"},
                    {"type": "text", "text": "十二宮、主星、輔星、四化", "size": "xs", "color": "#888888"}
                ]}
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "🌟 排盤", "text": "排盤"}, "style": "primary", "color": "#6A0DAD"}
            ],
            "paddingAll": "15px"
        }
    }
    return FlexSendMessage(alt_text='籟柏紫微斗數', contents=flex_content)

def create_date_picker_flex():
    """建立日期選擇器"""
    flex_content = {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "contents": [{"type": "text", "text": "🌟 紫微排盤", "weight": "bold", "size": "lg", "color": "#FFFFFF"}],
            "backgroundColor": "#6A0DAD", "paddingAll": "15px"
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
                 "style": "primary", "color": "#6A0DAD", "margin": "md"
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
    flex_msg = create_menu_flex()
    line_bot_api.reply_message(event.reply_token, flex_msg)

@handler.add(PostbackEvent)
def handle_postback(event):
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
        
        if st.get('step') == 'hour':
            hr = next((i for i, s in enumerate(SHICHEN) if s in txt), -1)
            if hr == -1:
                line_bot_api.reply_message(event.reply_token, TextSendMessage('請選擇正確時辰'))
                return
            user_states[uid] = {**st, 'step': 'gender', 'hour': hr}
            qr = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label='👨 男', text='男')),
                QuickReplyButton(action=MessageAction(label='👩 女', text='女'))
            ])
            line_bot_api.reply_message(event.reply_token, TextSendMessage('請選擇性別：', quick_reply=qr))
            return
        
        elif st.get('step') == 'gender':
            gender = 'male' if '男' in txt else 'female'
            y, m, d, hr = st['y'], st['m'], st['d'], st['hour']
            del user_states[uid]
            
            try:
                result = get_ziwei_chart(y, m, d, hr, gender)
                flex_msg = create_ziwei_flex(result, y)
                line_bot_api.reply_message(event.reply_token, flex_msg)
            except Exception as e:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(f'排盤錯誤：{str(e)}'))
            return
    
    if txt in ['主選單', '選單', 'menu', '首頁', '回首頁']:
        flex_msg = create_menu_flex()
        line_bot_api.reply_message(event.reply_token, flex_msg)
    
    elif txt in ['排盤', '紫微', '命盤', '紫微斗數']:
        flex_msg = create_date_picker_flex()
        line_bot_api.reply_message(event.reply_token, flex_msg)
    
    elif txt in ['說明', '功能', '幫助', 'help', '你好', 'hi', 'Hi', '嗨']:
        flex_msg = create_menu_flex()
        line_bot_api.reply_message(event.reply_token, flex_msg)
    
    else:
        flex_msg = create_menu_flex()
        line_bot_api.reply_message(event.reply_token, flex_msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

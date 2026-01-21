# -*- coding: utf-8 -*-
"""
籟柏紫微斗數 LINE Bot
使用 Node.js iztro 庫進行精確排盤
"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction,
    FollowEvent, PostbackEvent
)
import os
import subprocess
import json
import hashlib
from datetime import datetime

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN_ZIWEI', ''))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET_ZIWEI', ''))

# 時辰對照
SHICHEN = ['子時(23-01)', '丑時(01-03)', '寅時(03-05)', '卯時(05-07)', '辰時(07-09)', '巳時(09-11)', 
           '午時(11-13)', '未時(13-15)', '申時(15-17)', '酉時(17-19)', '戌時(19-21)', '亥時(21-23)']

# 生肖對照
ZODIAC_LIST = ['鼠', '牛', '虎', '兔', '龍', '蛇', '馬', '羊', '猴', '雞', '狗', '豬']

user_states = {}

def call_iztro(date, hour, gender, action='chart', target_date=None):
    """呼叫 Node.js iztro 計算"""
    cmd = ['node', '/opt/linebot/ziwei/ziwei_calc.js', date, str(hour), gender, action]
    if target_date:
        cmd.append(target_date)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {'success': False, 'error': result.stderr}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_correct_zodiac(lunar_date_str):
    """根據農曆年份計算正確生肖"""
    import re
    # 匹配各種農曆年份格式
    match = re.search(r'(\d{4})年', str(lunar_date_str))
    if match:
        lunar_year = int(match.group(1))
        zodiac_idx = (lunar_year - 1900) % 12
        return ZODIAC_LIST[zodiac_idx]
    return ""

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

def create_ziwei_flex(data, year):
    """建立紫微斗數 Flex Message"""
    
    lunar_date = data.get('lunarDate', '')
    chinese_date = data.get('chineseDate', '')
    five_elements = data.get('fiveElementsClass', '')
    soul = data.get('soul', '')
    body = data.get('body', '')
    zodiac = get_correct_zodiac(lunar_date)
    sign = data.get('sign', '')
    
    # 找命宮主星
    palaces = data.get('palaces', [])
    ming_stars = ""
    palace_lines = []
    
    for p in palaces:
        name = p.get('name', '')
        is_body = p.get('isBodyPalace', False)
        major_stars = p.get('majorStars', [])
        
        # 格式化星曜
        stars_list = []
        for s in major_stars:
            star_name = s.get('name', '')
            brightness = s.get('brightness', '')
            mutagen = s.get('mutagen', '')
            
            display = star_name
            if brightness:
                display += f"({brightness})"
            if mutagen:
                display += f"[{mutagen}]"
            stars_list.append(display)
        
        stars_str = '、'.join(stars_list) if stars_list else '空宮'
        
        # 標記命宮身宮
        mark = ""
        if name == '命宮':
            mark = "【命】"
            ming_stars = stars_str
        if is_body:
            mark += "【身】"
        
        palace_lines.append(f"{name}{mark}: {stars_str}")
    
    palace_display = '\n'.join(palace_lines)
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
                {"type": "text", "text": f"干支：{chinese_date}", "size": "sm"},
                {"type": "text", "text": f"生肖：{zodiac}　星座：{sign}", "size": "sm"},
                {"type": "text", "text": f"五行局：{five_elements}", "size": "sm", "color": "#C41E3A", "weight": "bold"},
                {"type": "separator", "margin": "md"},
                
                {"type": "text", "text": "【命身資訊】", "weight": "bold", "color": "#6A0DAD", "size": "md", "margin": "md"},
                {"type": "text", "text": f"命宮主星：{ming_stars}", "size": "sm", "weight": "bold", "color": "#C41E3A"},
                {"type": "text", "text": f"命主：{soul}　身主：{body}", "size": "sm"},
                {"type": "separator", "margin": "md"},
                
                {"type": "text", "text": "【十二宮】", "weight": "bold", "color": "#6A0DAD", "size": "md", "margin": "md"},
                {"type": "text", "text": palace_display, "size": "xs", "wrap": True},
            ],
            "paddingAll": "15px"
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "🌟 今日運勢", "text": "今日運勢"}, "style": "primary", "color": "#6A0DAD", "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🏠 回主選單", "text": "主選單"}, "style": "secondary", "height": "sm"}
            ],
            "paddingAll": "10px"
        }
    }
    return FlexSendMessage(alt_text='紫微斗數命盤', contents=flex_content)

def create_fortune_flex(fortune):
    """建立今日運勢 Flex Message"""
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
                ]},
                {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [
                    {"type": "text", "text": "✨ 今日運勢", "size": "md", "weight": "bold"},
                    {"type": "text", "text": "每日運勢預測", "size": "sm", "color": "#666666"},
                    {"type": "text", "text": "事業、財運、感情、健康", "size": "xs", "color": "#888888"}
                ]}
            ],
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box", "layout": "horizontal", "spacing": "md",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "🌟 排盤", "text": "排盤"}, "style": "primary", "color": "#6A0DAD"},
                {"type": "button", "action": {"type": "message", "label": "✨ 今日運勢", "text": "今日運勢"}, "style": "primary", "color": "#4169E1"}
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
            gender = '男' if '男' in txt else '女'
            y, m, d, hr = st['y'], st['m'], st['d'], st['hour']
            del user_states[uid]
            
            try:
                date_str = f"{y}-{m}-{d}"
                data = call_iztro(date_str, hr, gender, 'chart')
                
                if data.get('success'):
                    flex_msg = create_ziwei_flex(data, y)
                    line_bot_api.reply_message(event.reply_token, flex_msg)
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(f'排盤錯誤：{data.get("error", "未知錯誤")}'))
            except Exception as e:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(f'排盤錯誤：{str(e)}'))
            return
    
    # 主選單
    if txt in ['主選單', '選單', 'menu', '首頁', '回首頁']:
        flex_msg = create_menu_flex()
        line_bot_api.reply_message(event.reply_token, flex_msg)
    
    # 排盤
    elif txt in ['排盤', '紫微', '命盤', '紫微斗數']:
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
    app.run(host='0.0.0.0', port=5002)

# -*- coding: utf-8 -*-
"""
籟柏紫微斗數 LINE Bot
使用 py-iztro 開源庫進行精確排盤
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
from py_iztro import Astro

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN_ZIWEI', ''))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET_ZIWEI', ''))

# 時辰對照
SHICHEN = ['子時(23-01)', '丑時(01-03)', '寅時(03-05)', '卯時(05-07)', '辰時(07-09)', '巳時(09-11)', 
           '午時(11-13)', '未時(13-15)', '申時(15-17)', '酉時(17-19)', '戌時(19-21)', '亥時(21-23)']

user_states = {}
astro = Astro()

def get_ziwei_chart(year, month, day, hour_idx, gender):
    """取得紫微斗數命盤"""
    date_str = f"{year}-{month}-{day}"
    gender_str = "男" if gender == "male" else "女"
    result = astro.by_solar(date_str, hour_idx, gender_str)
    return result

def format_palace_info(palace):
    """格式化宮位資訊"""
    major_stars = []
    for star in palace.major_stars:
        name = star.name
        brightness = star.brightness if star.brightness else ""
        mutagen = star.mutagen if star.mutagen else ""
        if mutagen:
            name += f"化{mutagen}"
        if brightness:
            name += f"[{brightness}]"
        major_stars.append(name)
    
    minor_stars = [s.name for s in palace.minor_stars]
    
    return {
        'name': palace.name,
        'branch': palace.earthly_branch,
        'stem': palace.heavenly_stem,
        'major': major_stars,
        'minor': minor_stars,
        'is_body': palace.is_body_palace
    }

def create_ziwei_flex(result, year):
    """建立紫微斗數 Flex Message"""
    
    lunar_date = result.lunar_date
    chinese_date = result.chinese_date
    soul_palace = result.earthly_branch_of_soul_palace
    body_palace = result.earthly_branch_of_body_palace
    soul_star = result.soul
    body_star = result.body
    five_elements = result.five_elements_class
    
    # 整理十二宮資訊
    palaces_info = []
    for palace in result.palaces:
        info = format_palace_info(palace)
        palaces_info.append(info)
    
    # 找命宮主星
    ming_stars = "空宮"
    for p in palaces_info:
        if p['branch'] == soul_palace:
            ming_stars = '、'.join(p['major']) if p['major'] else '空宮'
            break
    
    # 建立宮位文字
    palace_lines = []
    for p in palaces_info:
        body_mark = "身" if p['is_body'] else ""
        ming_mark = "命" if p['branch'] == soul_palace else ""
        mark = ming_mark + body_mark
        if mark:
            mark = f"【{mark}】"
        stars = '、'.join(p['major'][:2]) if p['major'] else "空"
        palace_lines.append(f"{p['name']}[{p['branch']}]{mark}: {stars}")
    
    palace_text = '\n'.join(palace_lines)
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
                {"type": "text", "text": f"五行局：{five_elements}", "size": "sm"},
                {"type": "separator", "margin": "md"},
                
                {"type": "text", "text": "【命身宮】", "weight": "bold", "color": "#6A0DAD", "size": "md", "margin": "md"},
                {"type": "text", "text": f"命宮：{soul_palace}宮 → {ming_stars}", "size": "sm"},
                {"type": "text", "text": f"身宮：{body_palace}宮", "size": "sm"},
                {"type": "text", "text": f"命主：{soul_star}　身主：{body_star}", "size": "sm"},
                {"type": "separator", "margin": "md"},
                
                {"type": "text", "text": "【十二宮主星】", "weight": "bold", "color": "#6A0DAD", "size": "md", "margin": "md"},
                {"type": "text", "text": palace_text, "size": "xs", "wrap": True},
            ],
            "paddingAll": "15px"
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": f"📅 查{datetime.now().year}年流年", "text": f"流年{datetime.now().year}"}, "style": "primary", "color": "#6A0DAD", "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🏠 回主選單", "text": "主選單"}, "style": "secondary", "height": "sm"}
            ],
            "paddingAll": "10px"
        }
    }
    return FlexSendMessage(alt_text='紫微斗數命盤', contents=flex_content)

def create_horoscope_flex(result, target_year):
    """建立流年運勢 Flex Message"""
    try:
        horoscope = result.horoscope(f"{target_year}-1-1")
        
        decadal = horoscope.decadal
        decadal_stem = decadal.heavenly_stem
        decadal_branch = decadal.earthly_branch
        
        yearly = horoscope.yearly
        yearly_stem = yearly.heavenly_stem
        yearly_branch = yearly.earthly_branch
        
        decadal_mutagen = decadal.mutagen if decadal.mutagen else []
        yearly_mutagen = yearly.mutagen if yearly.mutagen else []
        
        # 大限宮名
        decadal_palaces = decadal.palace_names if decadal.palace_names else []
        decadal_ming = decadal_palaces[2] if len(decadal_palaces) > 2 else ""
        
        flex_content = {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box", "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"📅 {target_year}年 運勢分析", "weight": "bold", "size": "xl", "color": "#FFFFFF"}
                ],
                "backgroundColor": "#4169E1", "paddingAll": "15px"
            },
            "body": {
                "type": "box", "layout": "vertical", "spacing": "md",
                "contents": [
                    {"type": "text", "text": "【大限運勢】", "weight": "bold", "color": "#4169E1", "size": "md"},
                    {"type": "text", "text": f"大限宮位：{decadal_stem}{decadal_branch}", "size": "sm"},
                    {"type": "text", "text": f"大限命宮：{decadal_ming}", "size": "sm"},
                    {"type": "text", "text": f"大限四化：化祿{decadal_mutagen[0] if len(decadal_mutagen)>0 else ''} 化權{decadal_mutagen[1] if len(decadal_mutagen)>1 else ''} 化科{decadal_mutagen[2] if len(decadal_mutagen)>2 else ''} 化忌{decadal_mutagen[3] if len(decadal_mutagen)>3 else ''}", "size": "xs", "wrap": True},
                    {"type": "separator", "margin": "md"},
                    
                    {"type": "text", "text": "【流年運勢】", "weight": "bold", "color": "#4169E1", "size": "md", "margin": "md"},
                    {"type": "text", "text": f"流年宮位：{yearly_stem}{yearly_branch}", "size": "sm"},
                    {"type": "text", "text": f"流年四化：化祿{yearly_mutagen[0] if len(yearly_mutagen)>0 else ''} 化權{yearly_mutagen[1] if len(yearly_mutagen)>1 else ''} 化科{yearly_mutagen[2] if len(yearly_mutagen)>2 else ''} 化忌{yearly_mutagen[3] if len(yearly_mutagen)>3 else ''}", "size": "xs", "wrap": True},
                    {"type": "separator", "margin": "md"},
                    
                    {"type": "text", "text": "【運勢提示】", "weight": "bold", "color": "#4169E1", "size": "md", "margin": "md"},
                    {"type": "text", "text": "此為基本流年資訊，詳細解盤請諮詢專業命理師。", "size": "sm", "wrap": True, "color": "#666666"},
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
        return FlexSendMessage(alt_text=f'{target_year}年運勢', contents=flex_content)
    except Exception as e:
        return TextSendMessage(f'流年計算錯誤：{str(e)}')

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
                    {"type": "text", "text": "十二宮、主星、輔星、四化、大限", "size": "xs", "color": "#888888"}
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
    
    # 流年查詢
    if txt.startswith('流年'):
        try:
            target_year = int(txt[2:]) if len(txt) > 2 else datetime.now().year
            if uid in user_states and 'result' in user_states[uid]:
                result = user_states[uid]['result']
                flex_msg = create_horoscope_flex(result, target_year)
                line_bot_api.reply_message(event.reply_token, flex_msg)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage('請先排盤後再查詢流年\n\n請點選「排盤」開始'))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('格式錯誤'))
        return
    
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
            
            try:
                result = get_ziwei_chart(y, m, d, hr, gender)
                user_states[uid] = {'result': result, 'year': y}
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

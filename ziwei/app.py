# -*- coding: utf-8 -*-
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import os, hashlib
from datetime import datetime

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN_ZIWEI', ''))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET_ZIWEI', ''))

SHICHEN = ['子時(23-01)', '丑時(01-03)', '寅時(03-05)', '卯時(05-07)', '辰時(07-09)', '巳時(09-11)', '午時(11-13)', '未時(13-15)', '申時(15-17)', '酉時(17-19)', '戌時(19-21)', '亥時(21-23)']
PALACES = ['命宮', '兄弟', '夫妻', '子女', '財帛', '疾厄', '遷移', '交友', '官祿', '田宅', '福德', '父母']
MAIN_STARS = {
    '紫微': {'icon': '👑', 'desc': '帝王星 - 領導力強、有威嚴、重視地位'},
    '天機': {'icon': '🧠', 'desc': '智慧星 - 聰明機智、善於思考、多才多藝'},
    '太陽': {'icon': '☀️', 'desc': '光明星 - 熱情開朗、樂於助人、有正義感'},
    '武曲': {'icon': '⚔️', 'desc': '財星 - 剛毅果斷、重視效率、財運佳'},
    '天同': {'icon': '😊', 'desc': '福星 - 溫和隨緣、知足常樂、人緣好'},
    '廉貞': {'icon': '🔥', 'desc': '次桃花星 - 多才多藝、感情豐富、有魅力'},
    '天府': {'icon': '🏛️', 'desc': '財庫星 - 穩重保守、善於理財、有貴氣'},
    '太陰': {'icon': '🌙', 'desc': '財星 - 細膩敏感、有藝術天分、重感情'},
    '貪狼': {'icon': '🎭', 'desc': '桃花星 - 多才多藝、善交際、欲望強'},
    '巨門': {'icon': '👄', 'desc': '是非星 - 口才好、善分析、較多疑'},
    '天相': {'icon': '📜', 'desc': '印星 - 正直可靠、重信用、有貴人緣'},
    '天梁': {'icon': '🛡️', 'desc': '蔭星 - 有長輩緣、善於照顧人、有智慧'},
    '七殺': {'icon': '⚡', 'desc': '將星 - 有魄力、敢冒險、獨立性強'},
    '破軍': {'icon': '💥', 'desc': '耗星 - 有開創力、不畏困難、變動大'}
}

user_states = {}
def calc_main_star(year, month, hour):
    ming_idx = (14 - month + hour) % 12
    year_gan = (year - 4) % 10
    star_idx = (ming_idx + year_gan) % 14
    star_keys = list(MAIN_STARS.keys())
    star = star_keys[star_idx]
    return {'palace': PALACES[ming_idx], 'star': star, 'info': MAIN_STARS[star]}

def calc_daxian(year):
    age = datetime.now().year - year
    start_ages = [2, 12, 22, 32, 42, 52, 62, 72, 82, 92]
    dx_idx = 0
    for i, a in enumerate(start_ages):
        if age >= a:
            dx_idx = i
    start = start_ages[dx_idx]
    end = start_ages[dx_idx + 1] - 1 if dx_idx < len(start_ages) - 1 else start + 9
    return {'age': age, 'range': f'{start}-{end}歲', 'palace': PALACES[dx_idx % 12]}

def daily_fortune(uid):
    seed = int(hashlib.md5(f"{uid}{datetime.now():%Y%m%d}".encode()).hexdigest()[:8], 16)
    aspects = {'事業': ['平穩發展','有新機會','貴人相助','大展身手'],
               '財運': ['小有收穫','意外之財','穩定增長','開源節流'],
               '感情': ['甜蜜時光','桃花旺盛','細水長流','溝通為主'],
               '健康': ['精神飽滿','注意休息','多運動','身心愉快']}
    result = {k: v[(seed+i)%len(v)] for i,(k,v) in enumerate(aspects.items())}
    result['stars'] = '⭐'*(3+seed%3)
    return result
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
@handler.add(MessageEvent, message=TextMessage)
def handle(event):
    uid, txt = event.source.user_id, event.message.text.strip()
    
    if uid in user_states:
        st = user_states[uid]
        if st['step'] == 'date':
            try:
                p = txt.replace('-','/').replace('.','/').split('/')
                y,m,d = int(p[0]),int(p[1]),int(p[2])
                user_states[uid] = {'step':'hour','y':y,'m':m,'d':d}
                qr = QuickReply(items=[QuickReplyButton(action=MessageAction(label=s,text=s)) for s in SHICHEN])
                line_bot_api.reply_message(event.reply_token, TextSendMessage('請選擇出生時辰：', quick_reply=qr))
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage('格式錯誤，請輸入 YYYY/MM/DD'))
            return
        elif st['step'] == 'hour':
            hr = next((i for i,s in enumerate(SHICHEN) if s in txt), -1)
            if hr == -1:
                line_bot_api.reply_message(event.reply_token, TextSendMessage('請選擇正確時辰'))
                return
            result = calc_main_star(st['y'], st['m'], hr)
            dx = calc_daxian(st['y'])
            del user_states[uid]
            info = result['info']
            msg = f'''🌟 紫微斗數命盤

【命宮主星】
{info['icon']} {result['star']}
{info['desc']}

【大限運程】
目前年齡: {dx['age']}歲
大限期間: {dx['range']}
大限宮位: {dx['palace']}

━━━━━━━━━━━━━━
✨ 籟柏紫微 免費服務'''
            line_bot_api.reply_message(event.reply_token, TextSendMessage(msg))
            return
    
    if txt in ['排盤','紫微','命盤','紫微斗數']:
        user_states[uid] = {'step':'date'}
        line_bot_api.reply_message(event.reply_token, TextSendMessage('請輸入出生日期（國曆）\n格式: YYYY/MM/DD\n例如: 1990/05/15'))
    elif txt in ['今日運勢','運勢','今日']:
        f = daily_fortune(uid)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(f"🌟 今日運勢\n\n整體: {f['stars']}\n事業: {f['事業']}\n財運: {f['財運']}\n感情: {f['感情']}\n健康: {f['健康']}"))
    else:
        qr = QuickReply(items=[QuickReplyButton(action=MessageAction(label='🌟 排盤',text='排盤')), QuickReplyButton(action=MessageAction(label='✨ 今日運勢',text='今日運勢'))])
        line_bot_api.reply_message(event.reply_token, TextSendMessage('歡迎使用籟柏紫微斗數！請選擇功能：', quick_reply=qr))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

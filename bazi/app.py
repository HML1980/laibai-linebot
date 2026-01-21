# -*- coding: utf-8 -*-
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import os, hashlib
from datetime import datetime
import sxtwl

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN_BAZI', ''))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET_BAZI', ''))

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
WUXING_TG = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
WUXING_DZ = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
SHICHEN = ['子時(23-01)', '丑時(01-03)', '寅時(03-05)', '卯時(05-07)', '辰時(07-09)', '巳時(09-11)', '午時(11-13)', '未時(13-15)', '申時(15-17)', '酉時(17-19)', '戌時(19-21)', '亥時(21-23)']

RIZHU = {
    '甲': '甲木 - 參天大樹，正直堅毅有領導力',
    '乙': '乙木 - 花草藤蔓，柔韌靈活有藝術天分',
    '丙': '丙火 - 太陽之火，熱情開朗有感染力',
    '丁': '丁火 - 燭光之火，溫和內斂有洞察力',
    '戊': '戊土 - 高山大地，穩重可靠有責任感',
    '己': '己土 - 田園沃土，務實謹慎有耐心',
    '庚': '庚金 - 刀劍之金，剛毅果斷重義氣',
    '辛': '辛金 - 珠玉之金，精緻優雅有品味',
    '壬': '壬水 - 江河大海，智慧深遠有遠見',
    '癸': '癸水 - 雨露之水，聰慧敏感善解人意'
}

user_states = {}

def calc_bazi(year, month, day, hour):
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
    return {'year': yg+yz, 'month': mg+mz, 'day': dg+dz, 'hour': hg+hz, 'dm': dg}

def analyze_wx(bazi):
    wx = {'木':0,'火':0,'土':0,'金':0,'水':0}
    for p in [bazi['year'], bazi['month'], bazi['day'], bazi['hour']]:
        wx[WUXING_TG[p[0]]] += 1
        wx[WUXING_DZ[p[1]]] += 1
    return wx, [k for k,v in wx.items() if v==0]

def daily_fortune(uid):
    seed = int(hashlib.md5(f"{uid}{datetime.now():%Y%m%d}".encode()).hexdigest()[:8], 16)
    colors = ['紅色','橙色','黃色','綠色','藍色','紫色','白色','金色']
    dirs = ['東','南','西','北','東南','東北','西南','西北']
    return {'stars': '⭐'*(3+seed%3), 'num': seed%9+1, 'color': colors[seed%8], 'dir': dirs[seed%8]}

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
            bazi = calc_bazi(st['y'],st['m'],st['d'],hr)
            wx, miss = analyze_wx(bazi)
            dm = bazi['dm']
            del user_states[uid]
            wx_str = ' '.join([f"{k}:{v}" for k,v in wx.items()])
            miss_str = '、'.join(miss) if miss else '無'
            msg = f'''🔮 八字命盤結果

【四柱】
年柱: {bazi['year']}  月柱: {bazi['month']}
日柱: {bazi['day']}  時柱: {bazi['hour']}

【五行統計】
{wx_str}
五行缺: {miss_str}

【日主分析】
{RIZHU[dm]}

━━━━━━━━━━━━━━
✨ 籟柏八字 免費服務'''
            line_bot_api.reply_message(event.reply_token, TextSendMessage(msg))
            return
    
    if txt in ['排盤','八字','命盤','八字排盤']:
        user_states[uid] = {'step':'date'}
        line_bot_api.reply_message(event.reply_token, TextSendMessage('請輸入出生日期（國曆）\n格式: YYYY/MM/DD\n例如: 1990/05/15'))
    elif txt in ['今日運勢','運勢','今日']:
        f = daily_fortune(uid)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(f"🌟 今日運勢\n\n運勢: {f['stars']}\n幸運數字: {f['num']}\n幸運色: {f['color']}\n吉方: {f['dir']}"))
    else:
        qr = QuickReply(items=[QuickReplyButton(action=MessageAction(label='🔮 排盤',text='排盤')), QuickReplyButton(action=MessageAction(label='🌟 今日運勢',text='今日運勢'))])
        line_bot_api.reply_message(event.reply_token, TextSendMessage('歡迎使用籟柏八字！請選擇功能：', quick_reply=qr))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

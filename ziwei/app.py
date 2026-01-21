# -*- coding: utf-8 -*-
"""
籟柏紫微斗數 LINE Bot - 完整排盤版
"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import os, hashlib
from datetime import datetime
import sxtwl

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN_ZIWEI', ''))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET_ZIWEI', ''))

# 基礎資料
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
GONG_NAMES = ['命宮', '兄弟', '夫妻', '子女', '財帛', '疾厄', '遷移', '交友', '官祿', '田宅', '福德', '父母']
SHICHEN = ['子時(23-01)', '丑時(01-03)', '寅時(03-05)', '卯時(05-07)', '辰時(07-09)', '巳時(09-11)', '午時(11-13)', '未時(13-15)', '申時(15-17)', '酉時(17-19)', '戌時(19-21)', '亥時(21-23)']

# 五行局對照表
WUXING_JU = {
    ('甲', '子'): ('金四局', 4), ('甲', '丑'): ('金四局', 4),
    ('乙', '子'): ('金四局', 4), ('乙', '丑'): ('金四局', 4),
    ('丙', '寅'): ('火六局', 6), ('丙', '卯'): ('火六局', 6),
    ('丁', '寅'): ('火六局', 6), ('丁', '卯'): ('火六局', 6),
    ('戊', '辰'): ('木三局', 3), ('戊', '巳'): ('木三局', 3),
    ('己', '辰'): ('木三局', 3), ('己', '巳'): ('木三局', 3),
    ('庚', '午'): ('土五局', 5), ('庚', '未'): ('土五局', 5),
    ('辛', '午'): ('土五局', 5), ('辛', '未'): ('土五局', 5),
    ('壬', '申'): ('水二局', 2), ('壬', '酉'): ('水二局', 2),
    ('癸', '申'): ('水二局', 2), ('癸', '酉'): ('水二局', 2),
    ('甲', '戌'): ('火六局', 6), ('甲', '亥'): ('火六局', 6),
    ('乙', '戌'): ('火六局', 6), ('乙', '亥'): ('火六局', 6),
    ('丙', '子'): ('水二局', 2), ('丙', '丑'): ('水二局', 2),
    ('丁', '子'): ('水二局', 2), ('丁', '丑'): ('水二局', 2),
    ('戊', '寅'): ('土五局', 5), ('戊', '卯'): ('土五局', 5),
    ('己', '寅'): ('土五局', 5), ('己', '卯'): ('土五局', 5),
    ('庚', '辰'): ('金四局', 4), ('庚', '巳'): ('金四局', 4),
    ('辛', '辰'): ('金四局', 4), ('辛', '巳'): ('金四局', 4),
    ('壬', '午'): ('木三局', 3), ('壬', '未'): ('木三局', 3),
    ('癸', '午'): ('木三局', 3), ('癸', '未'): ('木三局', 3),
    ('甲', '申'): ('水二局', 2), ('甲', '酉'): ('水二局', 2),
    ('乙', '申'): ('水二局', 2), ('乙', '酉'): ('水二局', 2),
    ('丙', '戌'): ('土五局', 5), ('丙', '亥'): ('土五局', 5),
    ('丁', '戌'): ('土五局', 5), ('丁', '亥'): ('土五局', 5),
    ('戊', '子'): ('火六局', 6), ('戊', '丑'): ('火六局', 6),
    ('己', '子'): ('火六局', 6), ('己', '丑'): ('火六局', 6),
    ('庚', '寅'): ('木三局', 3), ('庚', '卯'): ('木三局', 3),
    ('辛', '寅'): ('木三局', 3), ('辛', '卯'): ('木三局', 3),
    ('壬', '辰'): ('金四局', 4), ('壬', '巳'): ('金四局', 4),
    ('癸', '辰'): ('金四局', 4), ('癸', '巳'): ('金四局', 4),
    ('甲', '午'): ('土五局', 5), ('甲', '未'): ('土五局', 5),
    ('乙', '午'): ('土五局', 5), ('乙', '未'): ('土五局', 5),
    ('丙', '申'): ('木三局', 3), ('丙', '酉'): ('木三局', 3),
    ('丁', '申'): ('木三局', 3), ('丁', '酉'): ('木三局', 3),
    ('戊', '戌'): ('水二局', 2), ('戊', '亥'): ('水二局', 2),
    ('己', '戌'): ('水二局', 2), ('己', '亥'): ('水二局', 2),
    ('庚', '子'): ('火六局', 6), ('庚', '丑'): ('火六局', 6),
    ('辛', '子'): ('火六局', 6), ('辛', '丑'): ('火六局', 6),
    ('壬', '寅'): ('土五局', 5), ('壬', '卯'): ('土五局', 5),
    ('癸', '寅'): ('土五局', 5), ('癸', '卯'): ('土五局', 5),
    ('甲', '辰'): ('金四局', 4), ('甲', '巳'): ('金四局', 4),
    ('乙', '辰'): ('金四局', 4), ('乙', '巳'): ('金四局', 4),
    ('丙', '午'): ('水二局', 2), ('丙', '未'): ('水二局', 2),
    ('丁', '午'): ('水二局', 2), ('丁', '未'): ('水二局', 2),
    ('戊', '申'): ('火六局', 6), ('戊', '酉'): ('火六局', 6),
    ('己', '申'): ('火六局', 6), ('己', '酉'): ('火六局', 6),
    ('庚', '戌'): ('木三局', 3), ('庚', '亥'): ('木三局', 3),
    ('辛', '戌'): ('木三局', 3), ('辛', '亥'): ('木三局', 3),
    ('壬', '子'): ('金四局', 4), ('壬', '丑'): ('金四局', 4),
    ('癸', '子'): ('金四局', 4), ('癸', '丑'): ('金四局', 4),
}

# 紫微星安星表（根據五行局和農曆日）
ZIWEI_TABLE = {
    2: [1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 0, 0, 1, 1, 2, 2, 3, 3, 4],
    3: [2, 1, 3, 2, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9, 8, 10, 9, 11, 10, 0, 11, 1, 0, 2, 1, 3, 2, 4, 3],
    4: [3, 2, 1, 4, 3, 2, 5, 4, 3, 6, 5, 4, 7, 6, 5, 8, 7, 6, 9, 8, 7, 10, 9, 8, 11, 10, 9, 0, 11, 10],
    5: [4, 3, 2, 1, 5, 4, 3, 2, 6, 5, 4, 3, 7, 6, 5, 4, 8, 7, 6, 5, 9, 8, 7, 6, 10, 9, 8, 7, 11, 10],
    6: [5, 4, 3, 2, 1, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 8, 7, 6, 5, 4, 9, 8, 7, 6, 5, 10, 9, 8, 7, 6],
}

# 年干四化
SIHUA = {
    '甲': {'化祿': '廉貞', '化權': '破軍', '化科': '武曲', '化忌': '太陽'},
    '乙': {'化祿': '天機', '化權': '天梁', '化科': '紫微', '化忌': '太陰'},
    '丙': {'化祿': '天同', '化權': '天機', '化科': '文昌', '化忌': '廉貞'},
    '丁': {'化祿': '太陰', '化權': '天同', '化科': '天機', '化忌': '巨門'},
    '戊': {'化祿': '貪狼', '化權': '太陰', '化科': '右弼', '化忌': '天機'},
    '己': {'化祿': '武曲', '化權': '貪狼', '化科': '天梁', '化忌': '文曲'},
    '庚': {'化祿': '太陽', '化權': '武曲', '化科': '太陰', '化忌': '天同'},
    '辛': {'化祿': '巨門', '化權': '太陽', '化科': '文曲', '化忌': '文昌'},
    '壬': {'化祿': '天梁', '化權': '紫微', '化科': '左輔', '化忌': '武曲'},
    '癸': {'化祿': '破軍', '化權': '巨門', '化科': '太陰', '化忌': '貪狼'},
}

# 祿存位置（依年干）
LUCUN_POS = {'甲': 2, '乙': 3, '丙': 5, '丁': 6, '戊': 5, '己': 6, '庚': 8, '辛': 9, '壬': 11, '癸': 0}

# 文昌位置（依時支，子時起戌宮逆行）
WENCHANG_POS = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 11]

# 文曲位置（依時支，子時起辰宮順行）
WENQU_POS = [4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2, 3]

# 左輔位置（依月，正月起辰宮順行）
ZUOFU_POS = [4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2, 3]

# 右弼位置（依月，正月起戌宮逆行）
YOUBI_POS = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 11]

user_states = {}

def get_lunar_info(year, month, day):
    """取得農曆資訊"""
    day_info = sxtwl.fromSolar(year, month, day)
    lunar_month = day_info.getLunarMonth()
    lunar_day = day_info.getLunarDay()
    year_gan = TIANGAN[day_info.getYearGZ().tg]
    year_zhi = DIZHI[day_info.getYearGZ().dz]
    return lunar_month, lunar_day, year_gan, year_zhi

def calc_ming_gong(lunar_month, hour_idx):
    """計算命宮位置：寅宮起正月，順數至生月，逆數至生時"""
    ming = (2 + lunar_month - 1 - hour_idx) % 12
    return ming

def calc_shen_gong(lunar_month, hour_idx):
    """計算身宮位置：寅宮起正月，順數至生月，順數至生時"""
    shen = (2 + lunar_month - 1 + hour_idx) % 12
    return shen

def get_gong_gan(year_gan, gong_pos):
    """取得宮位天干（用於定五行局）"""
    # 甲己年起丙寅，乙庚年起戊寅...
    start_gan = {'甲': 2, '己': 2, '乙': 4, '庚': 4, '丙': 6, '辛': 6, '丁': 8, '壬': 8, '戊': 0, '癸': 0}
    base = start_gan[year_gan]
    return TIANGAN[(base + gong_pos - 2) % 10]

def calc_ziwei_pos(lunar_day, ju_num):
    """計算紫微星位置"""
    if ju_num not in ZIWEI_TABLE:
        return 0
    if lunar_day > 30:
        lunar_day = 30
    return ZIWEI_TABLE[ju_num][lunar_day - 1]

def calc_tianfu_pos(ziwei_pos):
    """計算天府星位置（與紫微對稱於寅申線）"""
    return (12 - ziwei_pos + 8) % 12

def place_ziwei_series(ziwei_pos):
    """安紫微星系"""
    stars = {}
    # 紫微星系：紫微、天機、太陽、武曲、天同、廉貞
    offsets = {'紫微': 0, '天機': -1, '太陽': -3, '武曲': -4, '天同': -5, '廉貞': -8}
    for star, offset in offsets.items():
        pos = (ziwei_pos + offset) % 12
        stars[star] = pos
    return stars

def place_tianfu_series(tianfu_pos):
    """安天府星系"""
    stars = {}
    # 天府星系：天府、太陰、貪狼、巨門、天相、天梁、七殺、破軍
    offsets = {'天府': 0, '太陰': 1, '貪狼': 2, '巨門': 3, '天相': 4, '天梁': 5, '七殺': 6, '破軍': 10}
    for star, offset in offsets.items():
        pos = (tianfu_pos + offset) % 12
        stars[star] = pos
    return stars

def place_minor_stars(lunar_month, hour_idx, year_gan):
    """安輔星"""
    stars = {}
    stars['文昌'] = WENCHANG_POS[hour_idx]
    stars['文曲'] = WENQU_POS[hour_idx]
    stars['左輔'] = ZUOFU_POS[lunar_month - 1]
    stars['右弼'] = YOUBI_POS[lunar_month - 1]
    stars['祿存'] = LUCUN_POS[year_gan]
    stars['擎羊'] = (LUCUN_POS[year_gan] + 1) % 12
    stars['陀羅'] = (LUCUN_POS[year_gan] - 1) % 12
    return stars

def calc_daxian(ming_pos, ju_num, gender, year_gan):
    """計算大限"""
    yang_gan = TIANGAN.index(year_gan) % 2 == 0
    shun = (yang_gan and gender == 'male') or (not yang_gan and gender == 'female')
    
    start_age = ju_num
    daxian_list = []
    current_gong = ming_pos
    
    for i in range(12):
        end_age = start_age + 9
        daxian_list.append({
            'gong': GONG_NAMES[current_gong] if current_gong < len(GONG_NAMES) else DIZHI[current_gong],
            'dizhi': DIZHI[current_gong],
            'start': start_age,
            'end': end_age
        })
        start_age = end_age + 1
        current_gong = (current_gong + 1) % 12 if shun else (current_gong - 1) % 12
    
    return daxian_list

def generate_chart(year, month, day, hour_idx, gender):
    """生成完整命盤"""
    # 農曆資訊
    lunar_month, lunar_day, year_gan, year_zhi = get_lunar_info(year, month, day)
    
    # 命宮、身宮
    ming_pos = calc_ming_gong(lunar_month, hour_idx)
    shen_pos = calc_shen_gong(lunar_month, hour_idx)
    
    # 五行局
    ming_gan = get_gong_gan(year_gan, ming_pos)
    ming_zhi = DIZHI[ming_pos]
    ju_name, ju_num = WUXING_JU.get((ming_gan, ming_zhi), ('水二局', 2))
    
    # 紫微、天府位置
    ziwei_pos = calc_ziwei_pos(lunar_day, ju_num)
    tianfu_pos = calc_tianfu_pos(ziwei_pos)
    
    # 安主星
    ziwei_stars = place_ziwei_series(ziwei_pos)
    tianfu_stars = place_tianfu_series(tianfu_pos)
    minor_stars = place_minor_stars(lunar_month, hour_idx, year_gan)
    
    # 合併所有星曜到十二宮
    gongs = {i: {'dizhi': DIZHI[i], 'stars': [], 'sihua': []} for i in range(12)}
    
    for star, pos in {**ziwei_stars, **tianfu_stars, **minor_stars}.items():
        gongs[pos]['stars'].append(star)
    
    # 四化
    sihua = SIHUA[year_gan]
    for hua_type, star in sihua.items():
        for pos, gong in gongs.items():
            if star in gong['stars']:
                gongs[pos]['sihua'].append(f"{star}{hua_type}")
    
    # 安十二宮名稱
    for i, gong_name in enumerate(GONG_NAMES):
        gong_pos = (ming_pos + i) % 12
        gongs[gong_pos]['name'] = gong_name
        gongs[gong_pos]['is_ming'] = (i == 0)
        gongs[gong_pos]['is_shen'] = (gong_pos == shen_pos)
    
    # 大限
    daxian = calc_daxian(ming_pos, ju_num, gender, year_gan)
    
    return {
        'year': year,
        'lunar_month': lunar_month,
        'lunar_day': lunar_day,
        'year_gan': year_gan,
        'year_zhi': year_zhi,
        'hour_zhi': DIZHI[hour_idx],
        'ming_pos': ming_pos,
        'shen_pos': shen_pos,
        'ju_name': ju_name,
        'ju_num': ju_num,
        'gongs': gongs,
        'daxian': daxian,
        'gender': gender
    }

def format_chart_text(chart):
    """格式化命盤為文字輸出"""
    lines = []
    lines.append('🌟 紫微斗數命盤 🌟')
    lines.append('')
    lines.append(f"農曆：{chart['year_gan']}{chart['year_zhi']}年 {chart['lunar_month']}月{chart['lunar_day']}日 {chart['hour_zhi']}時")
    lines.append(f"五行局：{chart['ju_name']}")
    lines.append('')
    
    # 十二宮
    lines.append('【十二宮主星】')
    for i in range(12):
        gong = chart['gongs'][i]
        name = gong.get('name', DIZHI[i])
        stars = '、'.join(gong['stars'][:3]) if gong['stars'] else '無主星'
        marks = ''
        if gong.get('is_ming'):
            marks += '★'
        if gong.get('is_shen'):
            marks += '☆'
        sihua_str = ' '.join(gong['sihua']) if gong['sihua'] else ''
        lines.append(f"{name}[{gong['dizhi']}]{marks}: {stars} {sihua_str}")
    
    # 大限
    lines.append('')
    current_age = datetime.now().year - chart['year']
    lines.append(f'【大限】(現年{current_age}歲)')
    for dx in chart['daxian'][:6]:
        mark = '←' if dx['start'] <= current_age <= dx['end'] else ''
        lines.append(f"{dx['start']}-{dx['end']}歲: {dx['dizhi']}宮 {mark}")
    
    lines.append('')
    lines.append('━━━━━━━━━━━━━━')
    lines.append('✨ 籟柏紫微 免費服務')
    
    return '\n'.join(lines)

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
            user_states[uid] = {**st, 'step': 'gender', 'hour': hr}
            qr = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label='👨 男', text='男')),
                QuickReplyButton(action=MessageAction(label='👩 女', text='女'))
            ])
            line_bot_api.reply_message(event.reply_token, TextSendMessage('請選擇性別（影響大限順逆）：', quick_reply=qr))
            return
        elif st['step'] == 'gender':
            gender = 'male' if '男' in txt else 'female'
            y, m, d, hr = st['y'], st['m'], st['d'], st['hour']
            del user_states[uid]
            
            try:
                chart = generate_chart(y, m, d, hr, gender)
                result = format_chart_text(chart)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(result))
            except Exception as e:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(f'排盤錯誤：{str(e)}'))
            return
    
    if txt in ['排盤','紫微','命盤','紫微斗數']:
        user_states[uid] = {'step':'date'}
        line_bot_api.reply_message(event.reply_token, TextSendMessage('請輸入出生日期（國曆）\n格式: YYYY/MM/DD\n例如: 1990/05/15'))
    elif txt in ['今日運勢','運勢','今日']:
        seed = int(hashlib.md5(f"{uid}{datetime.now():%Y%m%d}".encode()).hexdigest()[:8], 16)
        aspects = {'事業': ['平穩發展','有新機會','貴人相助','大展身手'],
                   '財運': ['小有收穫','意外之財','穩定增長','開源節流'],
                   '感情': ['甜蜜時光','桃花旺盛','細水長流','溝通為主'],
                   '健康': ['精神飽滿','注意休息','多運動','身心愉快']}
        result = {k: v[(seed+i)%len(v)] for i,(k,v) in enumerate(aspects.items())}
        msg = f"🌟 今日運勢\n\n整體: {'⭐'*(3+seed%3)}\n事業: {result['事業']}\n財運: {result['財運']}\n感情: {result['感情']}\n健康: {result['健康']}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(msg))
    else:
        qr = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label='🌟 排盤',text='排盤')),
            QuickReplyButton(action=MessageAction(label='✨ 今日運勢',text='今日運勢'))
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage('歡迎使用籟柏紫微斗數！請選擇功能：', quick_reply=qr))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

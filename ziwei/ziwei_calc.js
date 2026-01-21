// ziwei_calc.js - 紫微斗數計算腳本
const { astro } = require('iztro');

const args = process.argv.slice(2);
const [date, hour, gender, action, targetDate] = args;

try {
    const result = astro.bySolar(date, parseInt(hour), gender, true, 'zh-TW');
    
    if (action === 'chart') {
        // 命盤資料
        const output = {
            success: true,
            lunarDate: result.lunarDate,
            chineseDate: result.chineseDate,
            zodiac: result.zodiac,
            sign: result.sign,
            fiveElementsClass: result.fiveElementsClass,
            soul: result.soul,
            body: result.body,
            earthlyBranchOfSoulPalace: result.earthlyBranchOfSoulPalace,
            earthlyBranchOfBodyPalace: result.earthlyBranchOfBodyPalace,
            palaces: result.palaces.map(p => ({
                name: p.name,
                heavenlyStem: p.heavenlyStem,
                earthlyBranch: p.earthlyBranch,
                isBodyPalace: p.isBodyPalace,
                majorStars: p.majorStars.map(s => ({
                    name: s.name,
                    brightness: s.brightness,
                    mutagen: s.mutagen
                })),
                minorStars: p.minorStars.map(s => ({
                    name: s.name,
                    brightness: s.brightness,
                    mutagen: s.mutagen
                }))
            }))
        };
        console.log(JSON.stringify(output));
    } else if (action === 'horoscope') {
        // 流年運勢
        const horoscope = result.horoscope(targetDate || new Date());
        const output = {
            success: true,
            decadal: {
                heavenlyStem: horoscope.decadal.heavenlyStem,
                earthlyBranch: horoscope.decadal.earthlyBranch,
                palaceNames: horoscope.decadal.palaceNames,
                mutagen: horoscope.decadal.mutagen,
                age: horoscope.decadal.age
            },
            yearly: {
                heavenlyStem: horoscope.yearly.heavenlyStem,
                earthlyBranch: horoscope.yearly.earthlyBranch,
                palaceNames: horoscope.yearly.palaceNames,
                mutagen: horoscope.yearly.mutagen
            }
        };
        console.log(JSON.stringify(output));
    }
} catch (e) {
    console.log(JSON.stringify({ success: false, error: e.message }));
}

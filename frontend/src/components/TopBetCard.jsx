import React, { useState } from 'react';
import { 
  Target, TrendingUp, Users, Shield, Sparkles, ChevronRight, 
  Clock, MessageSquare, Flame, Radio 
} from 'lucide-react';
import MatchDetailModal from './MatchDetailModal';
import TeamBadge from './TeamBadge';
import { toRussianTeam, toRussianLeague } from '../utils/russianNames';

const formatHandicapVal = (valStr) => {
  if (!valStr) return '0';
  const v = valStr.replace(',', '.').trim();
  const num = parseFloat(v);
  if (isNaN(num)) {
    if (['0', '+0', '-0'].includes(v)) return '0';
    if (!v.startsWith('+') && !v.startsWith('-')) return `+${v}`;
    return v;
  }
  if (num === 0) return '0';
  if (num > 0) {
    const cleanNum = String(Number(num.toFixed(2)));
    return cleanNum.startsWith('+') ? cleanNum : `+${cleanNum}`;
  } else {
    return String(Number(num.toFixed(2)));
  }
};

export const formatOutcome = (outcome, homeTeam = '', awayTeam = '') => {
  if (!outcome) return '';

  // Очищаем от суффиксов источников в скобках
  let clean = outcome.replace(/\s*\((?:stavka tv|legalbet|vprognoze|br|betting|tg|statarea|pinnacle)\b.*?\)/gi, '').trim().replace(/\.$/, '').trim();
  const low = clean.toLowerCase();

  // 0. Если строка уже вида "Фора [Team] (val) (Ф1/Ф2)" - обязательно гарантируем знак + или - !
  const mHandicap = clean.match(/^фора\s+(?!1\b|2\b|хозя|гост)(.+?)\s+\(([\+\-]?\d+[\.,]?\d*)\)\s+\((ф[12])\)$/i);
  if (mHandicap) {
    const team = mHandicap[1].trim();
    const v = formatHandicapVal(mHandicap[2]);
    const mCode = mHandicap[3].toUpperCase();
    return `Фора ${team} (${v}) (${mCode})`;
  }
  if (/^фора\s+(?!1\b|2\b|хозя|гост).+?\s+\(0\)$/i.test(clean)) return clean;
  if (/^индивидуальный тотал\s+(?!1\b|2\b|хозя|гост).+?\s+(больше|меньше)\s+\d+[\.,]?\d*\s+\(ит[12][бм]\s+\d+[\.,]?\d*\)$/i.test(clean)) return clean;
  if (/^тотал\s+(больше|меньше)\s+\d+[\.,]?\d*\s+\(т[бм]\s+\d+[\.,]?\d*\)$/i.test(clean)) return clean;
  if (/^обе забьют\s*—\s*(да|нет)\s+\(оз:\s*(да|нет)\)$/i.test(clean)) return clean;
  if (/^(?!1\b|2\b|хозя|гост).+?\s+не проиграет\s+\((1x|x2)\)$/i.test(clean)) return clean;
  if (/^победа\s+(?!1\b|2\b|хозя|гост).+?\s+\(п[12]\)$/i.test(clean)) return clean;
  if (['ничья (х)', 'победа 1 или 2 (12)'].includes(low)) return clean;

  const cleanMatch = (str, target) => {
    if (!str || !target) return false;
    const s = str.toLowerCase().replace(/[^a-zа-я0-9]/g, '');
    const t = target.toLowerCase().replace(/[^a-zа-я0-9]/g, '');
    if (t.length < 3) return false;
    return s.includes(t) || t.includes(s);
  };

  const isStrictTeam = (str, target) => {
    if (!str || !target) return false;
    const s = str.toLowerCase().replace(/[^a-zа-я0-9]/g, '');
    const t = target.toLowerCase().replace(/[^a-zа-я0-9]/g, '');
    return s === t;
  };

  // 1. Тайм / Матч (КРИТИЧЕСКИ ВАЖНО: отделять от ординаров П1/П2!)
  if (low.includes('тайм / матч') || low.includes('тайм/матч') || low.includes('тайм-матч') || low.includes('т/м:') || /(?:^|[^\wа-яё])(?:н\/п1|н\/п2|п1\/п1|п2\/п2|п1\/н|п2\/н|п1\/п2|п2\/п1)(?=[^\wа-яё]|$)/i.test(low)) {
    const cleanTm = clean.replace(/тайм\s*[\/\-]\s*матч\s*[\-—:]\s*/gi, '').trim();
    return `Тайм/Матч: ${cleanTm}`;
  }

  // 2. Комбинированные ставки
  if (low.includes(' и тб') || low.includes(' и тм') || low.includes(' + тб') || low.includes(' + тм') || low.includes(' и оз') || low.includes(' + оз') || low.includes('+ тм') || low.includes('+ тб') || low.includes('+оз') || low.includes('+тб') || low.includes('+тм')) {
    return clean;
  }

  // 3. Индивидуальные тоталы (ИТБ / ИТМ)
  if (low.includes('итб') || low.includes('итм') || low.includes('индивидуальный') || low.includes('ит1') || low.includes('ит2')) {
    const itb = low.match(/(?:итб\s*([12])|ит([12])б|индивидуальный\s*тотал\s*([12])\s*больше|итб|индивидуальный\s*тотал.*?больше)\s*\(?(\d+[\.,]?\d*)\)?/i);
    if (itb) {
      let teamNum = itb[1] || itb[2] || itb[3];
      const val = (itb[4] || '1.5').replace(',', '.');
      if (!teamNum) {
        teamNum = (/(?:^|[^\wа-яё])(?:гост\w*|втор\w*)(?=[^\wа-яё]|$)/i.test(low) || (awayTeam && cleanMatch(low, awayTeam))) ? '2' : '1';
      }
      const teamName = teamNum === '2' ? awayTeam : homeTeam;
      return teamName ? `Индивидуальный Тотал ${teamName} Больше ${val} (ИТБ${teamNum} ${val})` : `ИТБ${teamNum} (${val})`;
    }
    const itm = low.match(/(?:итм\s*([12])|ит([12])м|индивидуальный\s*тотал\s*([12])\s*меньше|итм|индивидуальный\s*тотал.*?меньше)\s*\(?(\d+[\.,]?\d*)\)?/i);
    if (itm) {
      let teamNum = itm[1] || itm[2] || itm[3];
      const val = (itm[4] || '1.5').replace(',', '.');
      if (!teamNum) {
        teamNum = (/(?:^|[^\wа-яё])(?:гост\w*|втор\w*)(?=[^\wа-яё]|$)/i.test(low) || (awayTeam && cleanMatch(low, awayTeam))) ? '2' : '1';
      }
      const teamName = teamNum === '2' ? awayTeam : homeTeam;
      return teamName ? `Индивидуальный Тотал ${teamName} Меньше ${val} (ИТМ${teamNum} ${val})` : `ИТМ${teamNum} (${val})`;
    }
  }

  // 4. Обе забьют (ОЗ)
  if (/(?:^|[^\wа-яё])(?:оз|обе\s*забьют|обе\s*команды\s*забьют)(?=[^\wа-яё]|$)/i.test(low)) {
    if (low.includes('нет') || low.includes('no') || low.includes('не забьют') || low.includes('— нет') || low.includes('- нет')) {
      return 'Обе забьют — Нет (ОЗ: Нет)';
    }
    return 'Обе забьют — Да (ОЗ: Да)';
  }

  // 5. Двойной шанс: 1X, X2, 12
  if (/(?:^|[^\wа-яё])(?:1x|1х)(?=[^\wа-яё]|$)/i.test(low) || (low.includes('не проиграет') && (/(?:^|[^\wа-яё])(?:1|хозя\w*)(?=[^\wа-яё]|$)/i.test(low) || cleanMatch(low, homeTeam)))) {
    return homeTeam ? `${homeTeam} не проиграет (1X)` : '1X (Хозяева не проиграют)';
  }
  if (/(?:^|[^\wа-яё])(?:x2|х2)(?=[^\wа-яё]|$)/i.test(low) || (low.includes('не проиграет') && (/(?:^|[^\wа-яё])(?:2|гост\w*)(?=[^\wа-яё]|$)/i.test(low) || cleanMatch(low, awayTeam)))) {
    return awayTeam ? `${awayTeam} не проиграет (X2)` : 'X2 (Гости не проиграют)';
  }
  if (low === '12' || low.includes('победа 1 или 2')) {
    return 'Победа 1 или 2 (12)';
  }

  // 6. Ничья
  if (['draw', 'x', 'х', 'ничья', 'х.', 'x.'].includes(low) || low.startsWith('ничья') || low === 'мир') {
    return 'Ничья (Х)';
  }

  // 7. Форы (Handicaps)
  const isHandicap = ['фора', 'handicap', 'азиатская фора'].some(k => low.includes(k)) || /(?:^|[^\wа-яё])(?:ф1|ф2|ah1|ah2|ах1|ах2)(?=[^\wа-яё]|$)/i.test(low) || low.includes('с форой');
  if (isHandicap) {
    let valM = low.match(/\(\s*([\+\-]?\d+[\.,]?\d*)\s*\)/);
    if (!valM) valM = low.match(/[\+\-]\d+[\.,]?\d*/);
    if (!valM) valM = low.match(/(?:фора|handicap|ф[12]?)\s*(?:[12]|хозяев|гостей|[^\d\(\)]+)?\s*\(?([\+\-]?\d+[\.,]?\d*)\)?/i);
    const val = formatHandicapVal(valM ? valM[1] : '0');

    const isT2 = /(?:фора|handicap|ф|ah|ах|форой)\s*2(?=[^\wа-яё]|$)/i.test(low)
      || /(?:^|[^\wа-яё])(?:ф2|ah2|ах2|гост\w*|втор\w*)(?=[^\wа-яё]|$)/i.test(low)
      || (awayTeam && cleanMatch(low, awayTeam))
      || low.includes('(ф2)');

    const isT1 = /(?:фора|handicap|ф|ah|ах|форой)\s*1(?=[^\wа-яё]|$)/i.test(low)
      || /(?:^|[^\wа-яё])(?:ф1|ah1|ах1|хозя\w*|перв\w*)(?=[^\wа-яё]|$)/i.test(low)
      || (homeTeam && cleanMatch(low, homeTeam))
      || low.includes('(ф1)');

    if (isT2 && !isT1) {
      const teamLabel = awayTeam || '2';
      return `Фора ${teamLabel} (${val}) (Ф2)`;
    } else if (isT1 && !isT2) {
      const teamLabel = homeTeam || '1';
      return `Фора ${teamLabel} (${val}) (Ф1)`;
    } else if (isT2 && isT1) {
      if (awayTeam && cleanMatch(low, awayTeam)) {
        return `Фора ${awayTeam} (${val}) (Ф2)`;
      }
      return `Фора ${homeTeam} (${val}) (Ф1)`;
    } else {
      return `Фора (${val})`;
    }
  }

  // 8. Тоталы (ТБ / ТМ)
  const isTot = ['тотал', 'total', 'больше', 'меньше', 'over', 'under'].some(k => low.includes(k)) 
    || /(?:^|[^\wа-яё])(?:тб|тм)(?=[^\wа-яё]|$)/i.test(low) 
    || /[\d\.,\(\)]+\s*[бмбm](?=[^\wа-яё]|$)/i.test(low);
  if (isTot) {
    const totValM = low.match(/(\d+[\.,]?\d*)/);
    if (totValM) {
      const val = totValM[1].replace(',', '.');
      const isUnder = /(?:^|[^\wа-яё])(?:тм|меньше|under)(?=[^\wа-яё]|$)/i.test(low) || /[\d\.,\(\)]+\s*[мm](?=[^\wа-яё]|$)/i.test(low);
      const isOver = /(?:^|[^\wа-яё])(?:тб|больше|over)(?=[^\wа-яё]|$)/i.test(low) || /[\d\.,\(\)]+\s*[бb](?=[^\wа-яё]|$)/i.test(low);
      if (isUnder && !isOver) return `Тотал Меньше ${val} (ТМ ${val})`;
      if (isOver && !isUnder) return `Тотал Больше ${val} (ТБ ${val})`;
      if (isUnder && isOver) {
        if (low.includes('меньше') || low.includes('тм') || low.includes('under') || /[\d\.,\(\)]+\s*[мm](?=[^\wа-яё]|$)/i.test(low)) {
          return `Тотал Меньше ${val} (ТМ ${val})`;
        }
        return `Тотал Больше ${val} (ТБ ${val})`;
      }
      return `Тотал Больше ${val} (ТБ ${val})`;
    }
  }

  // 9. Победа с учетом ОТ
  if (['с учетом от', 'с учётом от', 'от и булл', 'с от'].some(k => low.includes(k))) {
    if (low.includes('1') || (homeTeam && cleanMatch(low, homeTeam))) {
      return homeTeam ? `Победа ${homeTeam} (с ОТ) (П1)` : 'Победа 1 (с ОТ)';
    }
    if (low.includes('2') || (awayTeam && cleanMatch(low, awayTeam))) {
      return awayTeam ? `Победа ${awayTeam} (с ОТ) (П2)` : 'Победа 2 (с ОТ)';
    }
  }

  // 10. ЧИСТАЯ Победа 2 / Гости (П2)
  if (
    ['away_win', 'п2', 'w2', '2', 'победа 2', 'победа2', 'победа гостей', 'победа второй команды', 'победа второй'].includes(low) ||
    /(?:^|[^\wа-яё])(?:победа\s*2|победа\s*гостей|победа\s*второй)(?=[^\wа-яё]|$)/i.test(low) ||
    /\(п2\)/i.test(low) ||
    /^п2[\.\s]*$/i.test(low) ||
    /^w2[\.\s]*$/i.test(low) ||
    /^2[\.\s]*$/i.test(low)
  ) {
    return awayTeam ? `Победа ${awayTeam} (П2)` : 'Победа Гостей (П2)';
  }

  // 11. ЧИСТАЯ Победа 1 / Хозяева (П1)
  if (
    ['home_win', 'п1', 'w1', '1', 'победа 1', 'победа1', 'победа хозяев', 'победа первой команды', 'победа первой'].includes(low) ||
    /(?:^|[^\wа-яё])(?:победа\s*1|победа\s*хозяев|победа\s*первой)(?=[^\wа-яё]|$)/i.test(low) ||
    /\(п1\)/i.test(low) ||
    /^п1[\.\s]*$/i.test(low) ||
    /^w1[\.\s]*$/i.test(low) ||
    /^1[\.\s]*$/i.test(low)
  ) {
    return homeTeam ? `Победа ${homeTeam} (П1)` : 'Победа Хозяев (П1)';
  }

  // 12. Победа: Название команды
  if (low.startsWith('победа:') || low.startsWith('победа ')) {
    const teamPart = low.includes(':') ? low.split(':')[1].trim() : low.replace('победа', '').trim();
    if (!['тотал', 'тб', 'тм', 'тайм', 'фора', 'гол', 'карт', 'угл'].some(k => teamPart.includes(k))) {
      if (awayTeam && cleanMatch(teamPart, awayTeam)) return `Победа ${awayTeam} (П2)`;
      if (homeTeam && cleanMatch(teamPart, homeTeam)) return `Победа ${homeTeam} (П1)`;
      if (teamPart) return `Победа ${teamPart}`;
    }
  }

  // 13. Исход СТРОГО равен названию одной из команд (только если нет спец-маркетов)
  const hasMarketWords = ['гол', 'тайм', 'период', 'карт', 'угл', 'сет', 'очк', 'шайб', 'брос', 'сух'].some(k => low.includes(k));
  if (!hasMarketWords) {
    if (awayTeam && isStrictTeam(clean, awayTeam)) return `Победа ${awayTeam} (П2)`;
    if (homeTeam && isStrictTeam(clean, homeTeam)) return `Победа ${homeTeam} (П1)`;
  }

  return clean;
};

export const getSportDisplay = (sport, league = '') => {
  const s = `${sport || ''} ${league || ''}`.toLowerCase().trim();
  if (s.includes('mma') || s.includes('ufc') || s.includes('bellator') || s.includes('boxing') || s.includes('martial')) {
    return { name: 'MMA / Бои', icon: '🥊', color: 'from-red-500/20 to-rose-500/10 text-rose-300 border-rose-500/30' };
  }
  if (s.includes('tennis') || s.includes('atp') || s.includes('wta') || s.includes('itf')) {
    return { name: 'Теннис', icon: '🎾', color: 'from-lime-500/20 to-green-500/10 text-lime-300 border-lime-500/30' };
  }
  if (s.includes('basketball') || s.includes('nba') || s.includes('euroleague') || s.includes('vtb') || s.includes('acb')) {
    return { name: 'Баскетбол', icon: '🏀', color: 'from-orange-500/20 to-amber-500/10 text-orange-300 border-orange-500/30' };
  }
  if (!s.includes('veikkausliiga') && (s.includes('hockey') || s.includes('nhl') || s.includes('khl') || s.includes('ahl') || s.includes('shl') || s.includes('liiga') || s.includes('allsvenskan') || s.includes('mestis'))) {
    return { name: 'Хоккей', icon: '🏒', color: 'from-cyan-500/20 to-blue-500/10 text-cyan-300 border-cyan-500/30' };
  }
  if (s.includes('nfl') || s.includes('ncaaf') || s.includes('american football') || s.includes('afl')) {
    return { name: 'Амер. футбол', icon: '🏈', color: 'from-amber-500/20 to-yellow-500/10 text-amber-300 border-amber-500/30' };
  }
  if (s.includes('esport') || s.includes('dota') || s.includes('cs:go') || s.includes('cs2') || s.includes('counter-strike') || s.includes('league of legends') || s.includes('valorant')) {
    return { name: 'Киберспорт', icon: '🎮', color: 'from-purple-500/20 to-pink-500/10 text-purple-300 border-purple-500/30' };
  }
  if (s.includes('baseball') || s.includes('mlb') || s.includes('kbo') || s.includes('npb')) {
    return { name: 'Бейсбол', icon: '⚾', color: 'from-blue-500/20 to-indigo-500/10 text-blue-300 border-blue-500/30' };
  }
  if (s.includes('cricket') || s.includes('twenty20') || s.includes('t20')) {
    return { name: 'Крикет', icon: '🏏', color: 'from-emerald-500/20 to-green-500/10 text-emerald-300 border-emerald-500/30' };
  }
  return { name: 'Футбол', icon: '⚽', color: 'from-blue-500/20 to-indigo-500/10 text-blue-300 border-blue-500/30' };
};

export const getRussianSport = (sport) => getSportDisplay(sport).name.toUpperCase();

export const formatLeagueDisplay = (league = '', countryName = '') => {
  if (!league) return countryName || 'Лига';
  const l = league.toLowerCase().trim();

  // 1. Еврокубки и международные турниры
  if (l.includes('champs_league') || l.includes('champions_league') || l.includes('лига чемпионов') || l.includes('лиге чемпионов')) {
    return 'Лига чемпионов УЕФА';
  }
  if (l.includes('europa_league') || l.includes('лига европы') || l.includes('лиге европы')) {
    return 'Лига Европы УЕФА';
  }
  if (l.includes('conference_league') || l.includes('лига конференций')) {
    return 'Лига конференций УЕФА';
  }
  if (l.includes('nations_league') || l.includes('лига наций')) {
    return 'Лига наций УЕФА';
  }
  if (l.includes('copa_libertadores') || l.includes('либертадорес')) {
    return 'Кубок Либертадорес';
  }
  if (l.includes('copa_sudamericana') || l.includes('судамерикана')) {
    return 'Южноамериканский кубок';
  }

  // 2. Англия
  if (l.includes('soccer_epl') || l.includes('premier_league') || l.includes('epl') || l === 'премьер-лига' || l.includes('апл')) {
    return 'АПЛ • Чемпионат Англии';
  }
  if (l.includes('championship') || l.includes('чемпионшип')) {
    return 'Чемпионшип • Англия';
  }
  if (l.includes('fa_cup') || l.includes('кубок англии')) {
    return 'Кубок Англии';
  }
  if (l.includes('efl_cup') || l.includes('кубок лиги')) {
    return 'Кубок лиги • Англия';
  }

  // 3. Испания
  if (l.includes('spain_la_liga') || l.includes('la_liga') || l.includes('laliga') || l.includes('ла лига') || l.includes('примера испания')) {
    return 'Ла Лига • Чемпионат Испании';
  }
  if (l.includes('segunda') || l.includes('сегунда')) {
    return 'Сегунда • Испания';
  }
  if (l.includes('copa_del_rey') || l.includes('кубок короля') || l.includes('кубок испании')) {
    return 'Кубок Испании';
  }

  // 4. Италия
  if (l.includes('italy_serie_a') || l.includes('serie_a') || l.includes('серия а') || l.includes('серия a')) {
    return 'Серия А • Чемпионат Италии';
  }
  if (l.includes('italy_serie_b') || l.includes('serie_b') || l.includes('серия б') || l.includes('серия b')) {
    return 'Серия B • Чемпионат Италии';
  }
  if (l.includes('coppa_italia') || l.includes('кубок италии')) {
    return 'Кубок Италии';
  }

  // 5. Германия
  if (l.includes('germany_bundesliga2') || l.includes('bundesliga2') || l.includes('вторая бундеслига')) {
    return 'Вторая Бундеслига • Германия';
  }
  if (l.includes('germany_bundesliga') || l.includes('bundesliga') || l.includes('бундеслига')) {
    return 'Бундеслига • Чемпионат Германии';
  }
  if (l.includes('dfb_pokal') || l.includes('кубок германии')) {
    return 'Кубок Германии';
  }

  // 6. Франция
  if (l.includes('france_ligue_two') || l.includes('ligue_2') || l.includes('лига 2')) {
    return 'Лига 2 • Чемпионат Франции';
  }
  if (l.includes('france_ligue_one') || l.includes('ligue_1') || l.includes('лига 1')) {
    return 'Лига 1 • Чемпионат Франции';
  }
  if (l.includes('coupe_de_france') || l.includes('кубок франции')) {
    return 'Кубок Франции';
  }

  // 7. Россия
  if (l.includes('russia_premier_league') || l.includes('rpl') || l.includes('рпл') || l.includes('премьер-лига россия')) {
    return 'РПЛ • Чемпионат России';
  }
  if (l.includes('fnl') || l.includes('фнл') || l.includes('первая лига')) {
    return 'Первая лига • Россия';
  }
  if (l.includes('кубок россии') || l.includes('russian_cup')) {
    return 'Кубок России';
  }

  // 8. Другие европейские чемпионаты
  if (l.includes('eredivisie') || l.includes('нидерланд')) {
    return 'Эредивизи • Нидерланды';
  }
  if (l.includes('primeira_liga') || l.includes('португал')) {
    return 'Примейра • Португалия';
  }
  if (l.includes('super_lig') || l.includes('турци')) {
    return 'Суперлига • Турция';
  }
  if (l.includes('belgium_first_div') || l.includes('бельги')) {
    return 'Про-Лига • Бельгия';
  }
  if (l.includes('brazil') || l.includes('brasileirao') || l.includes('бразил')) {
    return 'Серия А • Бразилия';
  }
  if (l.includes('argentina') || l.includes('аргентин')) {
    return 'Примера • Аргентина';
  }
  if (l.includes('mls') || l.includes('млс')) {
    return 'МЛС • Чемпионат США';
  }
  if (l.includes('saudi') || l.includes('саудов')) {
    return 'Про-Лига • Саудовская Аравия';
  }

  // 9. Хоккей
  if (l.includes('nhl') || l.includes('нхл')) {
    return 'НХЛ • Регулярный чемпионат';
  }
  if (l.includes('khl') || l.includes('кхл')) {
    return 'КХЛ • Континентальная лига';
  }
  if (l.includes('vhl') || l.includes('вхл')) {
    return 'ВХЛ • Чемпионат России';
  }
  if (l.includes('mhl') || l.includes('мхл')) {
    return 'МХЛ • Молодежная лига';
  }
  if (l.includes('allsvenskan')) {
    return 'Allsvenskan • Чемпионат Швеции';
  }
  if (l.includes('shl') || l.includes('шхл')) {
    return 'ШХЛ • Чемпионат Швеции';
  }
  if (l.includes('liiga')) {
    return 'Лиига • Чемпионат Финляндии';
  }

  // 10. Баскетбол
  if (l.includes('nba') || l.includes('нба')) {
    return 'НБА • Чемпионат США';
  }
  if (l.includes('euroleague') || l.includes('евролига')) {
    return 'Евролига • Баскетбол';
  }
  if (l.includes('vtb') || l.includes('втб')) {
    return 'Единая лига ВТБ';
  }

  // 11. Американский футбол
  if (l.includes('nfl') || l.includes('нфл')) {
    return 'НФЛ • Американский футбол';
  }
  if (l.includes('ncaaf') || l.includes('ncaa')) {
    return 'NCAA • Студенческий футбол США';
  }

  // 12. Единоборства и теннис
  if (l.includes('ufc') || l.includes('mma') || l.includes('мма')) {
    return 'UFC • Бои';
  }
  if (l.includes('tennis') || l.includes('atp') || l.includes('wta')) {
    return 'ATP / WTA Тур • Теннис';
  }

  // Если строка была технической soccer_xxx -> очищаем
  if (league.startsWith('soccer_') || league.startsWith('basketball_') || league.startsWith('icehockey_')) {
    return league.replace(/^soccer_|^basketball_|^icehockey_/, '').replace(/_/g, ' ').toUpperCase();
  }

  return league;
};

const formatCardMoscowTime = (dateStr) => {
  if (!dateStr) return { dateStr: '', timeStr: '' };
  try {
    let cleanStr = String(dateStr).trim().replace(' ', 'T');
    if (!cleanStr.includes('Z') && !cleanStr.includes('+') && !cleanStr.slice(10).includes('-')) {
      cleanStr = `${cleanStr}+03:00`;
    }
    const d = new Date(cleanStr);
    if (isNaN(d.getTime())) {
      const m = String(dateStr).match(/(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/);
      if (m) {
        const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
        const day = parseInt(m[3], 10);
        const mIdx = parseInt(m[2], 10) - 1;
        return {
          dateStr: `${day} ${months[mIdx] || ''}`,
          timeStr: `${m[4]}:${m[5]}`
        };
      }
      return { dateStr: '', timeStr: '' };
    }
    const dStr = d.toLocaleDateString('ru-RU', {
      timeZone: 'Europe/Moscow',
      day: 'numeric',
      month: 'short'
    }).replace('.', '');
    const tStr = d.toLocaleTimeString('ru-RU', {
      timeZone: 'Europe/Moscow',
      hour: '2-digit',
      minute: '2-digit'
    });
    return { dateStr: dStr, timeStr: tStr };
  } catch (e) {
    return { dateStr: '', timeStr: '' };
  }
};

const cleanAiInsight = (text) => {
  if (!text) return '';
  let clean = text.replace(/\*\*/g, '').replace(/🔥\s*ИИ-Нейровердикт.*?:/gi, '').trim();
  clean = clean.replace(/^[:\s-]+/, '').trim();
  return clean;
};

const TopBetCard = ({ bet }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  let colorClass = 'bg-accent';
  let textClass = 'text-accent';
  let borderClass = 'border-blue-500/30';
  
  if (bet.confidence_score >= 80) {
    colorClass = 'bg-success';
    textClass = 'text-success';
    borderClass = 'border-emerald-500/30';
  } else if (bet.confidence_score < 60) {
    colorClass = 'bg-warning';
    textClass = 'text-warning';
    borderClass = 'border-amber-500/30';
  }

  // Извлекаем названия команд и переводим на чистый русский язык
  const [rawHome, rawAway] = bet.match_name.includes(' vs ') 
    ? bet.match_name.split(' vs ') 
    : bet.match_name.split(' - ');
  const homeTeam = toRussianTeam(bet.home_team || rawHome);
  const awayTeam = toRussianTeam(bet.away_team || rawAway);
  const leagueDisplay = toRussianLeague(bet.league, bet.country_name);

  const sportDisplay = getSportDisplay(bet.sport_type, bet.league);
  const totalCappersCount = bet.all_predictions?.length || bet.supporting_sources?.length || 0;
  const supportingCount = bet.supporting_sources?.length || 0;
  const mskTime = formatCardMoscowTime(bet.match_date);

  // Определение Live-статуса: матч начался и идёт прямо сейчас (до 2.5 часов от старта)
  const isMatchLive = () => {
    if (bet.final_score_home !== null || bet.final_score_away !== null || !bet.match_date) return false;
    try {
      let cleanStr = String(bet.match_date).trim().replace(' ', 'T');
      if (!cleanStr.includes('Z') && !cleanStr.includes('+') && !cleanStr.slice(10).includes('-')) {
        cleanStr = `${cleanStr}+03:00`;
      }
      const start = new Date(cleanStr).getTime();
      const now = Date.now();
      return now >= start && now <= (start + 135 * 60 * 1000);
    } catch (e) {
      return false;
    }
  };

  const hasScore = bet.final_score_home !== null && bet.final_score_away !== null;
  const isFinished = hasScore || (bet.status === 'finished' && bet.bet_result !== null);
  const isLive = !isFinished && (isMatchLive() || bet.status === 'live' || bet.status === 'in_progress');

  const sourcesList = (bet.supporting_sources || []).map(s => {
    return s.replace(/\s*\(Рейтинг:.*?\)/g, '').trim();
  });

  const cleanInsight = cleanAiInsight(bet.ai_insight);

  return (
    <>
      <div 
        onClick={() => setIsModalOpen(true)}
        className={`h-full flex flex-col justify-between bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950 rounded-3xl p-5 border ${
          bet.is_bet_of_the_day 
            ? 'border-amber-500/60 shadow-2xl shadow-amber-500/20 ring-2 ring-amber-500/30' 
            : bet.slot_label === 'Топ-2 Дня'
            ? 'border-blue-500/50 shadow-2xl shadow-blue-500/15 ring-1 ring-blue-500/30'
            : bet.slot_label === 'Топ-3 Дня'
            ? 'border-cyan-500/50 shadow-2xl shadow-cyan-500/15 ring-1 ring-cyan-500/30'
            : 'border-gray-800 hover:border-blue-500/40 shadow-xl hover:shadow-2xl hover:shadow-blue-500/10'
        } hover:-translate-y-1.5 cursor-pointer transition-all duration-300 relative overflow-hidden group select-none`}
      >
        {/* Фоновое свечение в верхнем углу */}
        <div className={`absolute top-0 right-0 w-32 h-32 opacity-10 rounded-bl-full pointer-events-none blur-xl ${colorClass}`}></div>

        <div>
          {/* ВЕРХНЯЯ ШАПКА: Вид спорта СЛЕВА (Футбол, Хоккей и т.д.), Время/LIVE СПРАВА */}
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r ${sportDisplay.color} rounded-full text-xs font-black border shadow-sm shrink-0`}>
                <span className="text-sm">{sportDisplay.icon}</span>
                <span className="truncate max-w-[140px] uppercase text-[11px] tracking-wider font-extrabold font-heading">
                  {sportDisplay.name}
                </span>
              </span>
            </div>

            {/* Аккуратная плашка времени по Москве, LIVE или ЗАВЕРШЁН */}
            {isLive ? (
              <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-950/80 rounded-xl border border-red-500/50 text-xs font-black text-red-200 shrink-0 shadow-lg shadow-red-500/20 animate-pulse">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping shrink-0"></span>
                <span className="font-extrabold uppercase tracking-wider text-red-300 font-heading">LIVE</span>
                <span className="text-[10px] text-red-400 font-semibold hidden sm:inline">• ИДЁТ</span>
              </div>
            ) : isFinished ? (
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-950/90 rounded-xl border border-gray-700/80 text-xs font-black text-gray-300 shrink-0 shadow-inner">
                <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
                <span className="font-mono text-gray-300 font-bold">{mskTime.timeStr}</span>
                <span className="text-[10px] text-emerald-400 font-black uppercase tracking-wider font-heading">ЗАВЕРШЁН</span>
              </div>
            ) : bet.match_date ? (
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-950/90 rounded-xl border border-gray-700/80 text-xs font-black text-gray-200 shrink-0 shadow-inner">
                <Clock className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span className="whitespace-nowrap font-mono">{mskTime.dateStr}, {mskTime.timeStr}</span>
                <span className="text-[10px] text-blue-400 font-black uppercase tracking-wider font-heading">МСК</span>
              </div>
            ) : null}
          </div>

          {/* ПОДШАПКА: Статус "Ставка Дня" + Лига с флагом страны */}
          <div className="flex items-center gap-2 flex-wrap mb-4">
            {bet.is_bet_of_the_day ? (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-black text-amber-300 bg-amber-500/20 px-3 py-1 rounded-xl border border-amber-400/50 shadow-md shadow-amber-500/15 animate-pulse font-heading">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>⭐ СТАВКА ДНЯ</span>
                <span className="text-amber-500/60">•</span>
                <span className="text-amber-200 font-semibold">{sportDisplay.name.toUpperCase()} (КАППЕРЫ)</span>
              </span>
            ) : bet.slot_label === 'Топ-2 Дня' ? (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-black text-blue-300 bg-blue-500/15 px-2.5 py-1 rounded-xl border border-blue-400/40 shadow-sm font-heading">
                <span>🥈 ТОП-2 ДНЯ</span>
              </span>
            ) : bet.slot_label === 'Топ-3 Дня' ? (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-black text-cyan-300 bg-cyan-500/15 px-2.5 py-1 rounded-xl border border-cyan-400/40 shadow-sm font-heading">
                <span>🥉 ТОП-3 ДНЯ</span>
              </span>
            ) : bet.slot_label ? (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-black text-cyan-300 bg-cyan-500/15 px-2.5 py-1 rounded-xl border border-cyan-400/30 shadow-sm font-heading">
                <Flame className="w-3.5 h-3.5 text-cyan-400" />
                <span>{bet.slot_label.toUpperCase()}</span>
              </span>
            ) : null}
            <span className="text-xs font-bold text-gray-300 px-3 py-1 bg-gray-800/80 rounded-lg border border-gray-750 truncate max-w-[240px] inline-flex items-center gap-1.5 shadow-sm" title={leagueDisplay}>
              {bet.country_flag_url && (
                <img 
                  src={bet.country_flag_url} 
                  alt="" 
                  className="w-4 h-3 object-cover rounded-[2px] opacity-85 shrink-0" 
                  onError={(e) => { e.currentTarget.style.display = 'none'; }}
                />
              )}
              <span className="truncate">{leagueDisplay}</span>
            </span>
          </div>

          {/* БЛОК ПРОТИВОСТОЯНИЯ (Эмблемы и Крупные жирные Названия) */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 p-3.5 bg-gray-950/60 rounded-2xl border border-gray-800/80 mb-4 shadow-inner">
            {/* Хозяева */}
            <div className="flex flex-col items-center text-center">
              <TeamBadge teamName={homeTeam} logoUrl={bet.home_logo} size="lg" className="mb-2.5" />
              <span className="text-base sm:text-lg font-black text-white leading-snug min-h-[3rem] flex items-center justify-center line-clamp-2 px-1 tracking-tight text-center drop-shadow-md font-heading hover:text-blue-300 transition-colors">
                {homeTeam}
              </span>
              <span className="text-[11px] text-gray-400 font-bold mt-0.5 uppercase tracking-wider">Хозяева</span>
            </div>

            {/* Разделитель VS или Счёт матча */}
            <div className="flex flex-col items-center justify-center px-1">
              {bet.final_score_home !== null && bet.final_score_away !== null ? (
                <div className="flex flex-col items-center">
                  <div className="px-2.5 py-1 rounded-xl bg-gray-800/90 border border-gray-600 font-black text-sm text-white shadow-md tracking-wider font-mono">
                    {bet.final_score_home} : {bet.final_score_away}
                  </div>
                  <span className="text-[9px] font-black text-emerald-400 uppercase tracking-widest mt-0.5 font-heading">ФИНАЛ</span>
                </div>
              ) : isLive ? (
                <span className="w-8 h-8 rounded-full bg-red-950/90 border border-red-500/50 flex items-center justify-center text-[10px] font-black text-red-300 shadow-lg shadow-red-500/20 animate-pulse font-heading">
                  LIVE
                </span>
              ) : (
                <span className="w-8 h-8 rounded-full bg-gray-800/90 border border-gray-700 flex items-center justify-center text-xs font-black text-gray-300 italic shadow-inner font-heading">
                  VS
                </span>
              )}
            </div>

            {/* Гости */}
            <div className="flex flex-col items-center text-center">
              <TeamBadge teamName={awayTeam} logoUrl={bet.away_logo} size="lg" className="mb-2.5" />
              <span className="text-base sm:text-lg font-black text-white leading-snug min-h-[3rem] flex items-center justify-center line-clamp-2 px-1 tracking-tight text-center drop-shadow-md font-heading hover:text-blue-300 transition-colors">
                {awayTeam}
              </span>
              <span className="text-[11px] text-gray-400 font-bold mt-0.5 uppercase tracking-wider">Гости</span>
            </div>
          </div>

          {/* КОНСЕНСУС КАППЕРОВ */}
          <div className="mb-4 p-3 bg-gray-950/50 rounded-xl border border-gray-800/80">
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="text-gray-400 font-medium flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-blue-400" />
                <span>Консенсус экспертов</span>
                {totalCappersCount > 0 && (
                  <span className="text-gray-500 text-[11px]">
                    ({supportingCount > 0 && totalCappersCount > supportingCount 
                      ? `${supportingCount} из ${totalCappersCount}` 
                      : totalCappersCount})
                  </span>
                )}
              </span>
              <span className={`font-black text-sm ${textClass}`}>{bet.confidence_score}%</span>
            </div>
            <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
              <div 
                className={`h-full ${colorClass} transition-all duration-1000 ease-out`} 
                style={{ width: `${Math.min(bet.confidence_score, 100)}%` }}
              ></div>
            </div>
          </div>

          {/* РЕКОМЕНДУЕМЫЙ ИСХОД И КЭФ (Широкий, удобный, с бейджем результата) */}
          <div className={`p-3.5 bg-gradient-to-br ${
            bet.bet_result === 'win' 
              ? 'from-emerald-950/40 via-gray-900 to-gray-900 border-emerald-500/50' 
              : bet.bet_result === 'loss' 
              ? 'from-rose-950/40 via-gray-900 to-gray-900 border-rose-500/50' 
              : bet.bet_result === 'refund' 
              ? 'from-amber-950/40 via-gray-900 to-gray-900 border-amber-500/50' 
              : 'from-blue-950/40 via-indigo-950/20 to-gray-900 border-blue-500/30'
          } rounded-2xl border mb-3 shadow-inner`}>
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <span className="text-[10px] font-black uppercase tracking-wider text-blue-300 flex items-center gap-1">
                <Target className="w-3.5 h-3.5 text-blue-400" />
                <span>Рекомендуемый исход</span>
              </span>
              <div className="flex items-center gap-1.5">
                {bet.bet_result === 'win' && (
                  <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-black rounded-md flex items-center gap-1 animate-pulse">
                    ✅ ЗАШЛА
                  </span>
                )}
                {bet.bet_result === 'loss' && (
                  <span className="px-2 py-0.5 bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-black rounded-md flex items-center gap-1">
                    ❌ МИМО
                  </span>
                )}
                {bet.bet_result === 'refund' && (
                  <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-black rounded-md flex items-center gap-1">
                    🔄 ВОЗВРАТ
                  </span>
                )}
                <span className="px-2.5 py-0.5 bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-black text-sm rounded-lg shadow-sm">
                  КЭФ {bet.average_odds.toFixed(2)}
                </span>
              </div>
            </div>
            <div className="font-black text-white text-base leading-snug">
              {formatOutcome(bet.recommended_outcome, homeTeam, awayTeam)}
            </div>
            {bet.value_badge && (
              <div className="mt-2 flex items-center">
                <span className="inline-flex items-center gap-1 text-[10px] font-black px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm">
                  {bet.value_badge}
                </span>
              </div>
            )}
          </div>

          {/* ИСТОЧНИКИ */}
          {sourcesList.length > 0 && (
            <div className="flex items-center gap-2 text-xs text-gray-400 bg-gray-950/40 px-3 py-2 rounded-xl mb-3 border border-gray-800/60">
              <Shield className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <p className="truncate text-[11px]">
                <strong className="text-gray-300 font-semibold">Подтверждено:</strong> {sourcesList.slice(0, 3).join(', ')}{sourcesList.length > 3 ? ` +${sourcesList.length - 3}` : ''}
              </p>
            </div>
          )}

          {/* ИИ ВЫЖИМКА */}
          {cleanInsight && (
            <div className="p-3 bg-gradient-to-r from-purple-950/20 via-blue-950/15 to-gray-900/40 rounded-xl border border-purple-500/20 mb-3 text-xs leading-relaxed">
              <div className="flex items-center gap-1.5 text-purple-400 font-bold text-[11px] mb-1">
                <Sparkles className="w-3.5 h-3.5" />
                <span>ИИ-анализ</span>
              </div>
              <p className="line-clamp-2 italic text-gray-300 text-[11px]">
                «{cleanInsight}»
              </p>
            </div>
          )}
        </div>

        {/* КНОПКА ПОЛНОГО РАЗБОРА (Всегда прибита к низу карточки) */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsModalOpen(true);
          }}
          className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-blue-600/20 via-indigo-600/25 to-blue-600/20 hover:from-blue-600/40 hover:to-indigo-600/40 text-blue-300 hover:text-white rounded-xl border border-blue-500/30 text-xs font-bold transition-all flex items-center justify-center gap-2 group-hover:border-blue-400/60 shadow-md"
        >
          <MessageSquare className="w-4 h-4 text-blue-400" />
          <span>Мысли капперов и полный разбор ({totalCappersCount})</span>
          <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>

      {/* Модальное окно с детальным разбором */}
      {isModalOpen && (
        <MatchDetailModal bet={bet} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
};

export default TopBetCard;

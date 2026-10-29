/**
 * Утилиты интеграции с Telegram Mini App (TMA)
 */

export const isTelegramWebApp = () => {
  return typeof window !== 'undefined' && 
         Boolean(window.Telegram?.WebApp?.initData);
};

export const getTelegramWebApp = () => {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    return window.Telegram.WebApp;
  }
  return null;
};

export const initTelegramWebApp = () => {
  const tg = getTelegramWebApp();
  if (!tg) return null;

  try {
    tg.ready();
    tg.expand();

    // Защита от случайного закрытия свайпом вниз
    if (typeof tg.enableClosingConfirmation === 'function') {
      tg.enableClosingConfirmation();
    }

    // Подгоняем цветовую гамму под темную неоновую тему сайта
    if (typeof tg.setHeaderColor === 'function') {
      tg.setHeaderColor('#090d16');
    }
    if (typeof tg.setBackgroundColor === 'function') {
      tg.setBackgroundColor('#090d16');
    }

    return tg;
  } catch (e) {
    console.warn("Ошибка инициализации Telegram WebApp:", e);
    return tg;
  }
};

export const getTelegramUser = () => {
  const tg = getTelegramWebApp();
  if (!tg || !tg.initDataUnsafe) return null;
  return tg.initDataUnsafe.user || null;
};

/**
 * Тактильная отдача (вибрация) для смартфонов внутри Telegram
 * @param {'light' | 'medium' | 'heavy' | 'rigid' | 'soft'} style
 */
export const triggerHaptic = (style = 'light') => {
  const tg = getTelegramWebApp();
  try {
    if (tg?.HapticFeedback?.impactOccurred) {
      tg.HapticFeedback.impactOccurred(style);
    } else if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(15);
    }
  } catch (e) {
    // ignore
  }
};

/**
 * Тактильная отдача при успехе или ошибке
 * @param {'error' | 'success' | 'warning'} type 
 */
export const triggerNotificationHaptic = (type = 'success') => {
  const tg = getTelegramWebApp();
  try {
    if (tg?.HapticFeedback?.notificationOccurred) {
      tg.HapticFeedback.notificationOccurred(type);
    }
  } catch (e) {
    // ignore
  }
};

/**
 * Безопасное открытие внешних ссылок
 */
export const openLinkSafely = (url) => {
  const tg = getTelegramWebApp();
  if (tg?.openLink) {
    tg.openLink(url);
  } else {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
};

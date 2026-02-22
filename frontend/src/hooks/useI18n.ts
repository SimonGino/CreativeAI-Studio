import { useCallback } from 'react';
import { useAppStore } from '@/stores/appStore';
import { t as translate, type I18nKey } from '@/lib/i18n';

export function useI18n() {
  const locale = useAppStore((s) => s.locale);
  const setLocale = useAppStore((s) => s.setLocale);

  const t = useCallback(
    (key: I18nKey, vars?: Record<string, string | number>) => translate(locale, key, vars),
    [locale],
  );

  return { locale, setLocale, t };
}


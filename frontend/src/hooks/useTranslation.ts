"use client"

import { useSettings } from "@/contexts/SettingsContext"
import { translations, type Locale } from "@/lib/translations"

export function useTranslation() {
  const { settings } = useSettings()
  const locale: Locale = (settings.language === "en" || settings.language === "hi")
    ? settings.language
    : "hi" // default to Hindi for unsupported locales

  /**
   * Get a translated string by dot-notation key.
   * e.g. t("dashboard.title") => "Empowering Farmers with"
   */
  function t(key: string): string {
    const [section, item] = key.split(".")
    return translations[locale]?.[section]?.[item] ?? translations["en"]?.[section]?.[item] ?? item ?? key
  }

  return { t, locale }
}

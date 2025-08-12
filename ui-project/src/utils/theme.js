// Theme utilities: detection, persistence, and application
const THEME_STORAGE_KEY = 'ui-theme-preference';

export const Theme = {
  System: 'system',
  Light: 'light',
  Dark: 'dark',
};

export function getStoredTheme() {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY);
    if (value === Theme.Light || value === Theme.Dark || value === Theme.System) {
      return value;
    }
  } catch (_) {
    // ignore storage errors
  }
  return Theme.System;
}

export function storeTheme(theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch (_) {
    // ignore storage errors
  }
}

export function getSystemPrefersDark() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false;
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export function applyTheme(theme) {
  const root = document.documentElement;
  if (!root) return;

  // Remove explicit data-theme to allow system rules when Theme.System
  if (theme === Theme.System) {
    root.removeAttribute('data-theme');
  } else {
    root.setAttribute('data-theme', theme);
  }
}

export function initTheme() {
  const initial = getStoredTheme();
  applyTheme(initial);

  // Keep in sync with system preference when set to system
  if (initial === Theme.System && typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const listener = () => {
      // toggling attribute is enough; variables inherit from @media block
      applyTheme(Theme.System);
    };
    try {
      media.addEventListener('change', listener);
    } catch (_) {
      // Safari fallback
      media.addListener(listener);
    }
  }
}

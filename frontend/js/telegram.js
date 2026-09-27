(function () {
  "use strict";

  const TelegramApp = {
    tg: null,
    isTelegram: false,
    initData: "",
    user: null,
    platform: "",
    version: "",

    init: function () {
      if (
        !window.Telegram ||
        !window.Telegram.WebApp
      ) {
        this.isTelegram = false;
        return;
      }

      this.tg = window.Telegram.WebApp;
      this.isTelegram = true;

      this.initData = this.tg.initData || "";
      this.platform = this.tg.platform || "";
      this.version = this.tg.version || "";

      /*
       * initDataUnsafe используется здесь только
       * для локального отображения/контекста.
       *
       * Для авторизации на сервере в будущем
       * будет использоваться только initData
       * после серверной проверки.
       */
      if (
        this.tg.initDataUnsafe &&
        this.tg.initDataUnsafe.user
      ) {
        this.user = this.tg.initDataUnsafe.user;
      }

      this.tg.ready();

      if (typeof this.tg.expand === "function") {
        this.tg.expand();
      }

      this.applyTheme();
      this.bindEvents();
    },

    applyTheme: function () {
      if (!this.tg) return;

      const root = document.documentElement;
      const theme = this.tg.themeParams || {};

      if (theme.bg_color) {
        root.style.setProperty(
          "--tg-bg-color",
          theme.bg_color
        );
      }

      if (theme.secondary_bg_color) {
        root.style.setProperty(
          "--tg-secondary-bg-color",
          theme.secondary_bg_color
        );
      }

      if (theme.text_color) {
        root.style.setProperty(
          "--tg-text-color",
          theme.text_color
        );
      }

      if (theme.hint_color) {
        root.style.setProperty(
          "--tg-hint-color",
          theme.hint_color
        );
      }
    },

    bindEvents: function () {
      if (!this.tg) return;

      if (typeof this.tg.onEvent === "function") {
        this.tg.onEvent(
          "themeChanged",
          () => this.applyTheme()
        );
      }

      if (typeof this.tg.onEvent === "function") {
        this.tg.onEvent(
          "viewportChanged",
          () => {
            document.documentElement.style.setProperty(
              "--tg-viewport-height",
              this.tg.viewportStableHeight + "px"
            );
          }
        );
      }
    },

    isAvailable: function () {
      return this.isTelegram;
    },

    getUser: function () {
      return this.user;
    },

    getUserId: function () {
      return this.user ? this.user.id : null;
    },

    getLanguageCode: function () {
      return this.user
        ? this.user.language_code || null
        : null;
    },

    getInitData: function () {
      return this.initData;
    },

    getThemeParams: function () {
      return this.tg
        ? this.tg.themeParams || {}
        : {};
    },

    getViewportHeight: function () {
      return this.tg
        ? this.tg.viewportStableHeight ||
          this.tg.viewportHeight ||
          0
        : 0;
    },

    haptic: function (type) {
      if (
        !this.tg ||
        !this.tg.HapticFeedback
      ) {
        return;
      }

      if (type === "success") {
        this.tg.HapticFeedback.notificationOccurred(
          "success"
        );
        return;
      }

      if (type === "error") {
        this.tg.HapticFeedback.notificationOccurred(
          "error"
        );
        return;
      }

      this.tg.HapticFeedback.impactOccurred(
        type || "light"
      );
    },

    hideMainButton: function () {
      if (
        this.tg &&
        this.tg.MainButton &&
        typeof this.tg.MainButton.hide === "function"
      ) {
        this.tg.MainButton.hide();
      }
    },

    hideBackButton: function () {
      if (
        this.tg &&
        this.tg.BackButton &&
        typeof this.tg.BackButton.hide === "function"
      ) {
        this.tg.BackButton.hide();
      }
    },

    close: function () {
      if (
        this.tg &&
        typeof this.tg.close === "function"
      ) {
        this.tg.close();
      }
    }
  };

  window.SYSTeM = window.SYSTeM || {};
  window.SYSTeM.Telegram = TelegramApp;

  TelegramApp.init();
})();

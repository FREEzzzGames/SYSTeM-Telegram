/* =========================================================
   SYSTeM — Telegram Mini App
   TELEGRAM.JS
   Step 3 — Telegram Foundation
   ========================================================= */

(function () {
    "use strict";

    const TelegramApp = {

        tg: null,

        isTelegram: false,

        initData: "",

        user: null,

        platform: null,

        version: null,


        /* =====================================================
           INITIALIZATION
           ===================================================== */

        init() {

            if (
                typeof window === "undefined" ||
                !window.Telegram ||
                !window.Telegram.WebApp
            ) {
                this.isTelegram = false;

                console.log("[Telegram] WebApp API not available.");

                return this;
            }

            this.tg = window.Telegram.WebApp;

            this.isTelegram = true;

            this.initData = this.tg.initData || "";

            this.platform = this.tg.platform || null;

            this.version = this.tg.version || null;


            /* -------------------------------------------------
               IMPORTANT:
               initDataUnsafe is used here only to read the
               temporary client-side user object.

               It MUST NOT be trusted by the backend.

               Later the server will validate initData.
               ------------------------------------------------- */

            if (
                this.tg.initDataUnsafe &&
                this.tg.initDataUnsafe.user
            ) {
                this.user = this.tg.initDataUnsafe.user;
            }


            /* -------------------------------------------------
               Tell Telegram that the Mini App is ready.
               ------------------------------------------------- */

            if (typeof this.tg.ready === "function") {
                this.tg.ready();
            }


            /* -------------------------------------------------
               Request expanded view when supported.
               ------------------------------------------------- */

            if (typeof this.tg.expand === "function") {
                this.tg.expand();
            }


            console.log("[Telegram] WebApp initialized.");

            console.log("[Telegram] Platform:", this.platform);

            console.log("[Telegram] Version:", this.version);

            console.log(
                "[Telegram] User:",
                this.user
                    ? {
                        id: this.user.id,
                        username: this.user.username || null,
                        language_code: this.user.language_code || null
                    }
                    : null
            );


            return this;
        },


        /* =====================================================
           ENVIRONMENT
           ===================================================== */

        isAvailable() {
            return this.isTelegram;
        },


        /* =====================================================
           USER
           ===================================================== */

        getUser() {
            return this.user;
        },


        getUserId() {

            if (!this.user) {
                return null;
            }

            return this.user.id || null;
        },


        getLanguageCode() {

            if (!this.user) {
                return null;
            }

            return this.user.language_code || null;
        },


        /* =====================================================
           AUTH DATA
           ===================================================== */

        getInitData() {
            return this.initData;
        },


        /* =====================================================
           TELEGRAM THEME
           ===================================================== */

        getThemeParams() {

            if (!this.tg) {
                return null;
            }

            return this.tg.themeParams || null;
        },


        /* =====================================================
           VIEWPORT
           ===================================================== */

        getViewportHeight() {

            if (!this.tg) {
                return window.innerHeight;
            }

            return (
                this.tg.viewportStableHeight ||
                this.tg.viewportHeight ||
                window.innerHeight
            );
        },


        /* =====================================================
           MAIN BUTTON
           ===================================================== */

        hideMainButton() {

            if (
                this.tg &&
                this.tg.MainButton &&
                typeof this.tg.MainButton.hide === "function"
            ) {
                this.tg.MainButton.hide();
            }
        },


        /* =====================================================
           BACK BUTTON
           ===================================================== */

        hideBackButton() {

            if (
                this.tg &&
                this.tg.BackButton &&
                typeof this.tg.BackButton.hide === "function"
            ) {
                this.tg.BackButton.hide();
            }
        },


        /* =====================================================
           HAPTIC
           ===================================================== */

        haptic(type) {

            if (
                !this.tg ||
                !this.tg.HapticFeedback
            ) {
                return;
            }

            try {

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

                if (type === "warning") {

                    this.tg.HapticFeedback.notificationOccurred(
                        "warning"
                    );

                    return;
                }

                this.tg.HapticFeedback.impactOccurred(
                    "light"
                );

            } catch (error) {

                console.warn(
                    "[Telegram] Haptic error:",
                    error
                );
            }
        },


        /* =====================================================
           CLOSE
           ===================================================== */

        close() {

            if (
                this.tg &&
                typeof this.tg.close === "function"
            ) {
                this.tg.close();
            }
        }
    };


    /* =========================================================
       INITIALIZE
       ========================================================= */

    TelegramApp.init();


    /* =========================================================
       GLOBAL API
       ========================================================= */

    window.SYSTeM = window.SYSTeM || {};

    window.SYSTeM.Telegram = TelegramApp;

})();

/* =========================================================
   SYSTeM — Localization
   LOCALES.JS
   Step 3 — RU / DE / EN
   ========================================================= */

(function () {
    "use strict";

    const LOCALES = {

        ru: {
            code: "ru",
            name: "RU",

            system: {
                title: "SYSTeM",
                status: "СИСТЕМА ЗАПУЩЕНА",
                online: "СИСТЕМА В СЕТИ",
                waiting: "ОЖИДАНИЕ ВВОДА"
            },

            process: {
                button: "[ ЗАПУСК ]"
            },

            economy: {
                resource: "РЕСУРС",
                credits: "КРЕДИТЫ",
                efficiency: "ЭФФЕКТИВНОСТЬ",
                nextUpgrade: "СЛЕДУЮЩЕЕ УЛУЧШЕНИЕ",
                upgrade: "[ УЛУЧШИТЬ ]"
            }
        },


        de: {
            code: "de",
            name: "DE",

            system: {
                title: "SYSTeM",
                status: "SYSTEM GESTARTET",
                online: "SYSTEM ONLINE",
                waiting: "WARTE AUF EINGABE"
            },

            process: {
                button: "[ START ]"
            },

            economy: {
                resource: "RESSOURCE",
                credits: "CREDITS",
                efficiency: "EFFIZIENZ",
                nextUpgrade: "NÄCHSTES UPGRADE",
                upgrade: "[ VERBESSERN ]"
            }
        },


        en: {
            code: "en",
            name: "EN",

            system: {
                title: "SYSTeM",
                status: "SYSTEM STARTED",
                online: "SYSTEM ONLINE",
                waiting: "WAITING FOR INPUT"
            },

            process: {
                button: "[ PROCESS ]"
            },

            economy: {
                resource: "RESOURCE",
                credits: "CREDITS",
                efficiency: "EFFICIENCY",
                nextUpgrade: "NEXT UPGRADE",
                upgrade: "[ UPGRADE ]"
            }
        }
    };


    /* =====================================================
       LANGUAGE STATE
       ===================================================== */

    let currentLanguage = "ru";


    /* =====================================================
       GET CURRENT LOCALE
       ===================================================== */

    function getLocale() {
        return LOCALES[currentLanguage];
    }


    /* =====================================================
       GET TRANSLATION BY PATH
       ===================================================== */

    function getText(path) {

        const parts = path.split(".");

        let value = getLocale();

        for (const part of parts) {

            if (
                value === undefined ||
                value === null
            ) {
                return path;
            }

            value = value[part];
        }

        return value !== undefined
            ? value
            : path;
    }


    /* =====================================================
       SET LANGUAGE
       ===================================================== */

    function setLanguage(language) {

        if (!LOCALES[language]) {
            return false;
        }

        currentLanguage = language;

        document.documentElement.lang = language;

        renderStaticText();

        return true;
    }


    /* =====================================================
       GET CURRENT LANGUAGE
       ===================================================== */

    function getLanguage() {
        return currentLanguage;
    }


    /* =====================================================
       RENDER STATIC TEXT
       ===================================================== */

    function renderStaticText() {

        const title = document.querySelector(
            ".system-header"
        );

        const status = document.querySelector(
            ".system-status"
        );

        const lines = document.querySelectorAll(
            ".terminal-line"
        );


        if (title) {
            title.textContent =
                getText("system.title");
        }


        if (status) {
            status.textContent =
                getText("system.status");
        }


        if (lines.length >= 2) {

            lines[0].textContent =
                "> " +
                getText("system.online");

            lines[1].textContent =
                "> " +
                getText("system.waiting");
        }
    }


    /* =====================================================
       PUBLIC API
       ===================================================== */

    window.SYSTeM = window.SYSTeM || {};

    window.SYSTeM.Locale = {

        locales: LOCALES,

        get: getLocale,

        text: getText,

        setLanguage: setLanguage,

        getLanguage: getLanguage
    };


    /* =====================================================
       INITIAL RENDER
       ===================================================== */

    document.addEventListener(
        "DOMContentLoaded",
        function () {
            renderStaticText();
        }
    );

})();

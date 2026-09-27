"use strict";

const CFG = {
    step: 1,
    efficiency: 1,
    upgrade: 10,
    multiplier: 1.5,
    saveKey: "system.save.v1"
};

const S = {
    resource: 0,
    credits: 0,
    efficiency: CFG.efficiency,
    upgradeCost: CFG.upgrade
};

const I18N = {
    ru: {
        credits: "КРЕДИТЫ",
        efficiency: "ЭФФЕКТИВНОСТЬ",
        next: "СЛЕДУЮЩЕЕ УЛУЧШЕНИЕ",
        upgrade: "[ УЛУЧШИТЬ ]",
        process: "ПРОЦЕСС ЗАВЕРШЁН",
        init: "СИСТЕМА ИНИЦИАЛИЗИРОВАНА",
        wait: "ОЖИДАНИЕ ВВОДА"
    },
    de: {
        credits: "CREDITS",
        efficiency: "EFFIZIENZ",
        next: "NÄCHSTES UPGRADE",
        upgrade: "[ VERBESSERN ]",
        process: "PROZESS ABGESCHLOSSEN",
        init: "SYSTEM INITIALISIERT",
        wait: "WARTE AUF EINGABE"
    },
    en: {
        credits: "CREDITS",
        efficiency: "EFFICIENCY",
        next: "NEXT UPGRADE",
        upgrade: "[ UPGRADE ]",
        process: "PROCESS COMPLETE",
        init: "SYSTEM INITIALIZED",
        wait: "WAITING FOR INPUT"
    }
};

let lang = "ru";

const $ = id => document.getElementById(id);

const fmt = n =>
    String(Math.floor(n)).padStart(6, "0");

function text(key) {
    return I18N[lang]?.[key] || I18N.ru[key] || key;
}


/* SAVE */

const Save = {

    save() {
        try {
            localStorage.setItem(
                CFG.saveKey,
                JSON.stringify({
                    v: 1,
                    resource: S.resource,
                    credits: S.credits,
                    efficiency: S.efficiency,
                    upgradeCost: S.upgradeCost
                })
            );
        } catch (e) {
            console.warn("Save error", e);
        }
    },

    load() {
        try {
            const x = JSON.parse(
                localStorage.getItem(CFG.saveKey)
            );

            if (!x || x.v !== 1) return;

            S.resource = Math.max(0, Number(x.resource) || 0);
            S.credits = Math.max(0, Number(x.credits) || 0);
            S.efficiency = Math.max(1, Number(x.efficiency) || 1);
            S.upgradeCost = Math.max(1, Number(x.upgradeCost) || 10);

        } catch (e) {
            console.warn("Load error", e);
        }
    }
};


/* LOG */

const Log = {

    items: [],

    add(key) {
        this.items.push(key);

        if (this.items.length > 30)
            this.items.shift();

        this.render();
    },

    render() {
        const el = $("system-log");
        if (!el) return;

        el.innerHTML = this.items
            .map(x => `<div>> ${text(x)}</div>`)
            .join("");

        el.scrollTop = el.scrollHeight;
    }
};


/* UI */

const UI = {

    economy: null,
    credits: null,
    efficiency: null,
    cost: null,
    upgrade: null,

    init() {

        this.economy =
            document.querySelector(".process-panel");

        this.makeEconomy();

        $("process-button")?.addEventListener(
            "click",
            process
        );

        document
            .querySelectorAll("[data-language]")
            .forEach(btn => {
                btn.addEventListener("click", () => {
                    setLanguage(btn.dataset.language);
                });
            });

        this.render();
    },

    makeEconomy() {

        if (!this.economy) return;

        const box = document.createElement("div");

        box.className = "system-economy";

        box.style.cssText =
            "margin-top:8px;padding:7px;" +
            "border:1px solid rgba(80,255,140,.2);" +
            "font-size:9px;letter-spacing:1px";

        box.innerHTML = `
            <div>
                <span id="credits-label"></span>
                <span id="credits-value"></span>
            </div>

            <div>
                <span id="efficiency-label"></span>
                <span id="efficiency-value"></span>
            </div>

            <div>
                <span id="cost-label"></span>
                <span id="cost-value"></span>
            </div>

            <button
                id="upgrade-button"
                class="process-button"
                type="button"
                style="width:100%;margin-top:5px"
            ></button>
        `;

        this.economy.appendChild(box);

        this.credits = $("credits-value");
        this.efficiency = $("efficiency-value");
        this.cost = $("cost-value");
        this.upgrade = $("upgrade-button");

        this.upgrade.addEventListener(
            "click",
            upgrade
        );
    },

    render() {

        const r = $("resource-value");

        if (r)
            r.textContent = fmt(S.resource);

        if (this.credits)
            this.credits.textContent = fmt(S.credits);

        if (this.efficiency)
            this.efficiency.textContent =
                "x" + S.efficiency;

        if (this.cost)
            this.cost.textContent =
                fmt(S.upgradeCost);

        if (this.upgrade) {

            this.upgrade.textContent =
                text("upgrade");

            this.upgrade.disabled =
                S.credits < S.upgradeCost;

            this.upgrade.style.opacity =
                this.upgrade.disabled ? ".35" : "1";
        }

        const cl = $("credits-label");
        const el = $("efficiency-label");
        const nl = $("cost-label");

        if (cl) cl.textContent = text("credits") + " ";
        if (el) el.textContent = text("efficiency") + " ";
        if (nl) nl.textContent = text("next") + " ";

        Log.render();
    }
};


/* GAME */

function process() {

    const amount =
        CFG.step * S.efficiency;

    S.resource += amount;
    S.credits += amount;

    Log.add("process");

    UI.render();

    Save.save();

    if (window.SYSTeM?.Telegram)
        window.SYSTeM.Telegram.haptic("light");
}


function upgrade() {

    if (S.credits < S.upgradeCost)
        return;

    S.credits -= S.upgradeCost;

    S.efficiency++;

    S.upgradeCost =
        Math.ceil(
            S.upgradeCost * CFG.multiplier
        );

    UI.render();

    Save.save();

    if (window.SYSTeM?.Telegram)
        window.SYSTeM.Telegram.haptic("success");
}


/* LANGUAGE */

function setLanguage(x) {

    if (!I18N[x])
        return;

    lang = x;

    document.documentElement.lang = x;

    document
        .querySelectorAll("[data-language]")
        .forEach(btn => {
            btn.classList.toggle(
                "active",
                btn.dataset.language === x
            );
        });

    UI.render();

    if (window.SYSTeM?.Locale)
        window.SYSTeM.Locale.setLanguage(x);
}


/* BOOT */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        Save.load();

        UI.init();

        Log.add("init");
        Log.add("wait");

        UI.render();

        setInterval(
            () => Save.save(),
            10000
        );

        document.addEventListener(
            "visibilitychange",
            () => {
                if (
                    document.visibilityState ===
                    "hidden"
                ) Save.save();
            }
        );

        window.addEventListener(
            "pagehide",
            () => Save.save()
        );
    }
);


/* PUBLIC API */

window.SYSTEM = {
    state: S,
    save: Save,
    log: Log,
    process,
    upgrade,
    setLanguage
};

import { registry } from "@web/core/registry";

// This tour relies on data created in the Python test (tests/test_credit_banner_e2e.py):
// customer credit limit 1000, one line of a 1.00 untaxed product, starting at quantity 500.
// Amounts are compared on their numeric part only so the tour is currency-agnostic.

const BANNER = ".o_form_view div.alert[role=alert]";

const visibleBanners = (cls) =>
    [...document.querySelectorAll(`${BANNER}.${cls}`)].filter((el) => el.offsetParent !== null);

const numbers = (text) => (text.match(/\d[\d,]*\.\d{2}/g) || []).map((n) => n.replace(/,/g, ""));

function assertNoBanner() {
    for (const cls of ["alert-warning", "alert-danger"]) {
        if (visibleBanners(cls).length) {
            throw new Error(`Unexpected visible credit banner (${cls})`);
        }
    }
}

function assertBanner(cls, headline, thisOrder) {
    const other = cls === "alert-warning" ? "alert-danger" : "alert-warning";
    const banners = visibleBanners(cls);
    if (banners.length !== 1) {
        throw new Error(`Expected exactly one ${cls} banner, found ${banners.length}`);
    }
    if (visibleBanners(other).length) {
        throw new Error(`Unexpected ${other} banner next to ${cls}`);
    }
    const banner = banners[0];
    const text = banner.textContent;
    if (!text.includes(headline)) {
        throw new Error(`Banner headline "${headline}" missing in: ${text}`);
    }
    // Headline limit, outstanding receivables, this order, total after this order.
    const figures = numbers(text);
    const expected = ["1000.00", "0.00", thisOrder, thisOrder];
    if (JSON.stringify(figures) !== JSON.stringify(expected)) {
        throw new Error(`Banner figures ${figures} differ from expected ${expected}`);
    }
    if (/False|undefined|NaN/.test(text)) {
        throw new Error(`Banner has placeholder text: ${text}`);
    }
    // Layout: between the status bar and the sheet, never inside the sheet.
    const statusbar = document.querySelector(".o_form_view .o_form_statusbar");
    // .o_form_sheet is the sheet itself; .o_form_sheet_bg also wraps the header and banners.
    const sheet = document.querySelector(".o_form_view .o_form_sheet");
    const after = (a, b) => Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    if (!after(statusbar, banner) || !after(banner, sheet) || sheet.contains(banner)) {
        throw new Error("Banner is not placed between the status bar and the form sheet");
    }
}

function setQuantity(qty, description) {
    return [
        {
            content: `Select the quantity cell (${description})`,
            trigger: ".o_field_cell[name=product_uom_qty]",
            run: "click",
        },
        {
            content: `Set quantity to ${qty}`,
            trigger: ".o_selected_row [name=product_uom_qty] input",
            run: `edit ${qty}`,
        },
    ];
}

const save = [
    {
        content: "Save the quotation",
        trigger: ".o_form_button_save",
        run: "click",
    },
    {
        content: "Wait for the save to finish",
        trigger: ".o_form_status_indicator:not(:has(.o_form_button_save:visible))",
    },
];

registry.category("web_tour.tours").add("credit_banner_happy", {
    steps: () => [
        {
            content: "Quantity 500: no credit banner",
            trigger: ".o_field_cell[name=product_uom_qty]",
            run: assertNoBanner,
        },
        ...setQuantity(900, "yellow"),
        ...save,
        {
            content: "Quantity 900: one yellow banner with the right figures",
            trigger: `${BANNER}.alert-warning:visible`,
            run: () =>
                assertBanner("alert-warning", "approaching its credit limit of", "900.00"),
        },
        ...setQuantity(1000, "exactly at the limit"),
        ...save,
        {
            content: "Quantity 1000 (at the limit): still yellow, not red",
            trigger: `${BANNER}.alert-warning:visible`,
            run: () =>
                assertBanner("alert-warning", "approaching its credit limit of", "1000.00"),
        },
        ...setQuantity(1200, "red"),
        ...save,
        {
            content: "Quantity 1200: one red banner, no yellow",
            trigger: `${BANNER}.alert-danger:visible`,
            run: () => assertBanner("alert-danger", "exceeds its credit limit of", "1200.00"),
        },
        ...setQuantity(400, "back to none"),
        ...save,
        {
            content: "Quantity 400: banner is gone",
            trigger: ".o_field_cell[name=product_uom_qty]:contains(400)",
            run: assertNoBanner,
        },
        ...setQuantity(1200, "live update, unsaved"),
        {
            content: "Click outside the line to commit the row without saving",
            trigger: ".o_form_sheet_bg",
            run: "click",
        },
        {
            content: "Red banner shows while the record is still dirty",
            trigger: `${BANNER}.alert-danger:visible`,
            run: () => {
                if (!document.querySelector(".o_form_button_save")) {
                    throw new Error("Record is expected to be dirty (unsaved)");
                }
                assertBanner("alert-danger", "exceeds its credit limit of", "1200.00");
            },
        },
        {
            content: "Discard the changes",
            trigger: ".o_form_button_cancel",
            run: "click",
        },
        {
            content: "Quantity is back to 400 and no banner is shown",
            trigger: ".o_field_cell[name=product_uom_qty]:contains(400)",
            run: assertNoBanner,
        },
    ],
});

/* =========================================================
   CREATOR OS NAVIGATION + AUTHENTICATION
========================================================= */


(function () {

    "use strict";


    /* =====================================================
       CONFIGURATION
    ===================================================== */

    const AUTH_ENDPOINT =
        `${API_URL}/api/auth/me`;

    const LOGOUT_ENDPOINT =
        `${API_URL}/api/auth/logout`;

    const MAX_AUTH_ATTEMPTS = 3;

    const AUTH_RETRY_DELAY = 1500;


    /* =====================================================
       PAGE HELPERS
    ===================================================== */

    function getCurrentPage() {

        const pathname =
            window.location.pathname;

        const page =
            pathname
                .split("/")
                .pop();

        return page || "index.html";

    }


    function getSafeCurrentPage() {

        const page =
            getCurrentPage();


        const allowedPages = [
            "index.html",
            "messages.html",
            "conversations.html",
            "sequences.html",
            "insights.html",
            "experiments.html",
            "reports.html",
            "import.html"
        ];


        if (
            allowedPages.includes(page)
        ) {

            return page;

        }


        return "index.html";

    }


    function redirectToLogin() {

        const currentPage =
            getSafeCurrentPage();


        const loginUrl =
            `login.html?next=${encodeURIComponent(
                currentPage
            )}`;


        window.location.replace(
            loginUrl
        );

    }


    /* =====================================================
       TEMPORARILY HIDE APP
    ===================================================== */

    function hideApplication() {

        const style =
            document.createElement("style");


        style.id =
            "creator-os-auth-loading-style";


        style.textContent = `

            body.creator-os-auth-checking
            > * {

                visibility: hidden;

            }

            body.creator-os-auth-checking
            #appNav {

                visibility: hidden;

            }

        `;


        document.head.appendChild(
            style
        );


        document.body.classList.add(
            "creator-os-auth-checking"
        );

    }


    function showApplication() {

        document.body.classList.remove(
            "creator-os-auth-checking"
        );

    }


    /* =====================================================
       AUTHENTICATION CHECK
    ===================================================== */

    async function checkAuthentication() {

        let lastError = null;


        for (
            let attempt = 1;
            attempt <= MAX_AUTH_ATTEMPTS;
            attempt++
        ) {

            try {

                const response =
                    await fetch(
                        AUTH_ENDPOINT,
                        {
                            method: "GET",

                            credentials:
                                "include",

                            cache: "no-store"
                        }
                    );


                if (
                    response.ok
                ) {

                    return true;

                }


                /*
                    A real 401 means there is
                    no valid session.

                    Do not retry a normal
                    authentication failure.
                */

                if (
                    response.status === 401
                ) {

                    return false;

                }


                /*
                    Other server errors may be
                    caused by Render waking up.
                */

                lastError =
                    new Error(
                        `Authentication request failed with status ${response.status}`
                    );


            } catch (error) {

                lastError =
                    error;

            }


            /*
                Give Render another chance
                before redirecting.
            */

            if (
                attempt <
                MAX_AUTH_ATTEMPTS
            ) {

                await new Promise(
                    (resolve) => {

                        setTimeout(
                            resolve,
                            AUTH_RETRY_DELAY
                        );

                    }
                );

            }

        }


        console.error(
            "Creator OS authentication failed:",
            lastError
        );


        return false;

    }


    /* =====================================================
       NAVIGATION HTML
    ===================================================== */

    function renderNavigation() {

        const navContainer =
            document.getElementById(
                "appNav"
            );


        if (!navContainer) {

            return;

        }


        const currentPage =
            getCurrentPage();


        navContainer.innerHTML = `

            <aside class="creator-os-sidebar">

                <div class="creator-os-logo">
                    Creator OS
                </div>


                <nav class="creator-os-nav">


                    <a
                        href="index.html"
                        class="${
                            currentPage === "index.html"
                                ? "active"
                                : ""
                        }"
                    >
                        Overview
                    </a>


                    <a
                        href="messages.html"
                        class="${
                            currentPage === "messages.html"
                                ? "active"
                                : ""
                        }"
                    >
                        DM Analytics
                    </a>


                    <a
                        href="conversations.html"
                        class="${
                            currentPage === "conversations.html"
                                ? "active"
                                : ""
                        }"
                    >
                        Conversations
                    </a>


                    <a
                        href="sequences.html"
                        class="${
                            currentPage === "sequences.html"
                                ? "active"
                                : ""
                        }"
                    >
                        Sequences
                    </a>


                    <a
                        href="insights.html"
                        class="${
                            currentPage === "insights.html"
                                ? "active"
                                : ""
                        }"
                    >
                        AI Insights
                    </a>


                    <a
                        href="experiments.html"
                        class="${
                            currentPage === "experiments.html"
                                ? "active"
                                : ""
                        }"
                    >
                        Experiments
                    </a>


                    <a
                        href="reports.html"
                        class="${
                            currentPage === "reports.html"
                                ? "active"
                                : ""
                        }"
                    >
                        Reports
                    </a>


                    <a
                        href="import.html"
                        class="${
                            currentPage === "import.html"
                                ? "active"
                                : ""
                        }"
                    >
                        Import Data
                    </a>


                    <button
                        id="creatorOsLogout"
                        type="button"
                    >
                        Logout
                    </button>


                </nav>

            </aside>

        `;

    }


    /* =====================================================
       NAVIGATION CSS
    ===================================================== */

    function installNavigationStyles() {

        if (
            document.getElementById(
                "creator-os-navigation-style"
            )
        ) {

            return;

        }


        const style =
            document.createElement("style");


        style.id =
            "creator-os-navigation-style";


        style.textContent = `

            /* =========================
               SIDEBAR
            ========================= */

            #appNav {

                position: fixed;

                left: 0;
                top: 0;

                width: 230px;
                height: 100vh;

                z-index: 1000;

            }


            .creator-os-sidebar {

                width: 230px;
                height: 100vh;

                background: #111;

                color: white;

                padding:
                    28px
                    16px;

                overflow-y: auto;

            }


            /* =========================
               LOGO
            ========================= */

            .creator-os-logo {

                font-size: 20px;

                font-weight: 700;

                padding:
                    0
                    12px
                    30px;

                letter-spacing:
                    -0.5px;

            }


            /* =========================
               NAVIGATION
            ========================= */

            .creator-os-nav {

                display: flex;

                flex-direction: column;

                gap: 6px;

            }


            .creator-os-nav a {

                display: block;

                color: #aaa;

                text-decoration: none;

                padding:
                    11px
                    12px;

                border-radius: 10px;

                font-size: 14px;

                transition:
                    background 0.2s,
                    color 0.2s;

            }


            .creator-os-nav a:hover {

                background: #222;

                color: white;

            }


            .creator-os-nav a.active {

                background: white;

                color: #111;

                font-weight: 600;

            }


            /* =========================
               LOGOUT
            ========================= */

            .creator-os-nav button {

                display: block;

                width: 100%;

                border: 0;

                background: transparent;

                color: #aaa;

                text-align: left;

                padding:
                    11px
                    12px;

                border-radius: 10px;

                font-size: 14px;

                cursor: pointer;

            }


            .creator-os-nav button:hover {

                background: #222;

                color: white;

            }


            /* =========================
               MOBILE
            ========================= */

            @media (max-width: 800px) {

                #appNav {

                    position: static;

                    width: 100%;

                    height: auto;

                }


                .creator-os-sidebar {

                    width: 100%;

                    height: auto;

                    padding:
                        14px
                        12px;

                }


                .creator-os-logo {

                    padding:
                        4px
                        8px
                        12px;

                    font-size: 19px;

                }


                .creator-os-nav {

                    flex-direction: row;

                    overflow-x: auto;

                    gap: 6px;

                    padding-bottom: 4px;

                    scrollbar-width: none;

                }


                .creator-os-nav::-webkit-scrollbar {

                    display: none;

                }


                .creator-os-nav a,
                .creator-os-nav button {

                    flex:
                        0 0 auto;

                    width: auto;

                    white-space: nowrap;

                    padding:
                        9px
                        11px;

                    font-size: 13px;

                }

            }

        `;


        document.head.appendChild(
            style
        );

    }


    /* =====================================================
       LOGOUT
    ===================================================== */

    function setupLogout() {

        const logoutButton =
            document.getElementById(
                "creatorOsLogout"
            );


        if (!logoutButton) {

            return;

        }


        logoutButton.addEventListener(
            "click",
            async () => {

                logoutButton.disabled =
                    true;

                logoutButton.textContent =
                    "Logging out...";


                try {

                    await fetch(
                        LOGOUT_ENDPOINT,
                        {
                            method: "POST",

                            credentials:
                                "include"
                        }
                    );

                } catch (error) {

                    console.error(
                        "Logout request failed:",
                        error
                    );

                }


                window.location.replace(
                    "login.html"
                );

            }
        );

    }


    /* =====================================================
       INITIALIZATION
    ===================================================== */

    async function initializeNavigation() {

        const currentPage =
            getCurrentPage();


        /*
            login.html does not use
            the protected navigation.
        */

        if (
            currentPage === "login.html"
        ) {

            return;

        }


        /*
            Hide the application immediately
            while authentication is checked.
        */

        hideApplication();


        /*
            Install navigation CSS early.
        */

        installNavigationStyles();


        /*
            Verify the session.
        */

        const authenticated =
            await checkAuthentication();


        /*
            No valid session.
        */

        if (!authenticated) {

            redirectToLogin();

            return;

        }


        /*
            Session is valid.
        */

        renderNavigation();

        setupLogout();

        showApplication();

    }


    /* =====================================================
       START
    ===================================================== */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initializeNavigation
        );

    } else {

        initializeNavigation();

    }


})();

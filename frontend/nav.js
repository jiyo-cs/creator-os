document.addEventListener(
    "DOMContentLoaded",
    async () => {

        const navContainer =
            document.getElementById("appNav");

        if (!navContainer) return;


        /* =========================
           AUTHENTICATION
        ========================= */

        const currentPage =
            window.location.pathname
                .split("/")
                .pop() || "index.html";


        /*
            Login page does not need
            authentication.
        */

        if (currentPage !== "login.html") {

            try {

                const authResponse =
                    await fetch(
                        `${API_URL}/api/auth/me`
                    );


                if (!authResponse.ok) {

                    window.location.href =
                        "login.html";

                    return;
                }


            } catch (error) {

                console.error(
                    "Authentication check failed:",
                    error
                );

                window.location.href =
                    "login.html";

                return;
            }
        }


        /* =========================
           NAV HTML
        ========================= */

        navContainer.innerHTML = `

            <aside class="creator-os-sidebar">

                <div class="creator-os-logo">
                    Creator OS
                </div>

                <nav class="creator-os-nav">

                    <a
                        href="index.html"
                        class="${currentPage === "index.html" ? "active" : ""}"
                    >
                        Overview
                    </a>

                    <a
                        href="messages.html"
                        class="${currentPage === "messages.html" ? "active" : ""}"
                    >
                        DM Analytics
                    </a>

                    <a
                        href="conversations.html"
                        class="${currentPage === "conversations.html" ? "active" : ""}"
                    >
                        Conversations
                    </a>

                    <a
                        href="sequences.html"
                        class="${currentPage === "sequences.html" ? "active" : ""}"
                    >
                        Sequences
                    </a>

                    <a
                        href="insights.html"
                        class="${currentPage === "insights.html" ? "active" : ""}"
                    >
                        AI Insights
                    </a>

                    <a
                        href="experiments.html"
                        class="${currentPage === "experiments.html" ? "active" : ""}"
                    >
                        Experiments
                    </a>

                    <a
                        href="reports.html"
                        class="${currentPage === "reports.html" ? "active" : ""}"
                    >
                        Reports
                    </a>

                    <a
                        href="import.html"
                        class="${currentPage === "import.html" ? "active" : ""}"
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


        /* =========================
           NAV CSS
        ========================= */

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

                padding: 28px 16px;

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
               NAV
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


        document.head.appendChild(style);


        /* =========================
           LOGOUT
        ========================= */

        const logoutButton =
            document.getElementById(
                "creatorOsLogout"
            );


        if (logoutButton) {

            logoutButton.addEventListener(
                "click",
                async () => {

                    try {

                        await fetch(
                            `${API_URL}/api/auth/logout`,
                            {
                                method: "POST"
                            }
                        );

                    } catch (error) {

                        console.error(
                            "Logout failed:",
                            error
                        );

                    }


                    window.location.href =
                        "login.html";

                }
            );

        }

    }
);

document.addEventListener("DOMContentLoaded", () => {
    const navContainer = document.getElementById("appNav");

    if (!navContainer) return;

    const currentPage =
        window.location.pathname.split("/").pop() || "index.html";

    navContainer.innerHTML = `
        <aside class="sidebar">

            <div class="logo">
                Creator OS
            </div>

            <nav class="nav">

                <a href="index.html"
                   class="${currentPage === "index.html" ? "active" : ""}">
                    Overview
                </a>

                <a href="messages.html"
                   class="${currentPage === "messages.html" ? "active" : ""}">
                    DM Analytics
                </a>

                <a href="conversations.html"
                   class="${currentPage === "conversations.html" ? "active" : ""}">
                    Conversations
                </a>

                <a href="sequences.html"
                   class="${currentPage === "sequences.html" ? "active" : ""}">
                    Sequences
                </a>

                <a href="insights.html"
                   class="${currentPage === "insights.html" ? "active" : ""}">
                    AI Insights
                </a>

                <a href="experiments.html"
                   class="${currentPage === "experiments.html" ? "active" : ""}">
                    Experiments
                </a>

                <a href="reports.html"
                   class="${currentPage === "reports.html" ? "active" : ""}">
                    Reports
                </a>

                <a href="import.html"
                   class="${currentPage === "import.html" ? "active" : ""}">
                    Import Data
                </a>

            </nav>

        </aside>
    `;
});

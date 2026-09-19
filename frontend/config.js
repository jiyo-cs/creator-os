const API_URL =
    "https://creator-os-api-2bb9.onrender.com";


const originalFetch =
    window.fetch;


window.fetch = function (
    input,
    init = {}
) {

    init.credentials = "include";

    return originalFetch(
        input,
        init
    );
};

/* =========================
   CREATOR OS API
========================= */

const API_URL =
    "https://creator-os-api-2bb9.onrender.com";


/* =========================
   AUTHENTICATED FETCH
========================= */

async function apiFetch(
    path,
    options = {}
) {

    const requestOptions = {
        ...options,

        credentials:
            "include",

        headers: {
            ...(options.headers || {})
        }
    };


    return fetch(
        `${API_URL}${path}`,
        requestOptions
    );

}

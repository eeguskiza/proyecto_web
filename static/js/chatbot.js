(() => {
  const chatSection = document.querySelector(".chatbot");
  const form = chatSection?.querySelector("form");
  const input = chatSection?.querySelector("input[name='q']");
  const log = chatSection?.querySelector(".chat-log");
  const hero = document.querySelector(".chat-hero");
  if (!form || !input || !log) return;

  const addMessage = (text, role = "user", extraHtml = "") => {
    const item = document.createElement("div");
    item.className = `chat-bubble ${role}`;
    item.innerHTML = `<p>${text}</p>${extraHtml}`;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
  };

  const animateDock = () => {
    if (!chatSection) return;
    chatSection.classList.add("docked");
    if (hero) hero.classList.add("collapsed");
  };

  const buildCard = (data) => {
    const parts = [];
    if (data.image || data.poster) {
      const src = data.image || data.poster;
      parts.push(`<img src="${src}" alt="${data.name}" class="chat-thumb">`);
    }
    parts.push(`<div class="chat-card-text"><strong>${data.name}</strong>`);
    if (data.kind === "character") {
      parts.push(`<small>${data.species} · ${data.homeworld}</small>`);
      if (data.film) {
        parts.push(`<small>Primera aparición: ${data.film}</small>`);
      }
      if (data.cybernetics) {
        parts.push(`<small>Cibernética: ${data.cybernetics}</small>`);
      }
      if (data.detail_url) {
        parts.push(`<small><a href="${data.detail_url}">Ver más</a></small>`);
      }
    } else if (data.kind === "media") {
      if (data.release_year) {
        parts.push(`<small>Año: ${data.release_year}</small>`);
      }
      if (data.detail_url) {
        parts.push(`<small><a href="${data.detail_url}">Ver más</a></small>`);
      }
    }
    parts.push("</div>");
    return parts.join("");
  };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    addMessage(query, "user");
    animateDock();
    input.value = "";
    input.focus();

    const endpoint = chatSection.dataset.endpoint || "/chatbot/search/";

    try {
      const res = await fetch(`${endpoint}?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      if (!res.ok || data.error) {
        addMessage("Solo puedo ayudarte con personajes de Star Wars. Prueba con un nombre o especie.", "bot");
        return;
      }

      if (data.name) {
        const cardHtml = buildCard(data);
        const text = data.body || `Te muestro info sobre ${data.name}:`;
        addMessage(text, "bot", cardHtml);
      } else if (data.reply) {
        addMessage(data.reply, "bot");
      } else {
        addMessage("No encontré nada. Pregunta por un personaje o especie concreta.", "bot");
      }
    } catch (err) {
      addMessage("No pude procesar tu consulta ahora mismo.", "bot");
    }
  });
})();

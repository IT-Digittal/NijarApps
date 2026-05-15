/**
 * Diccionario de cadenas i18n del tótem.
 *
 * Cubre los 4 idiomas obligatorios del contrato (ES/EN/DE/FR).
 * El contenido dinámico (POIs, FAQs) se carga desde la API.
 */

export const I18N = {
  es: {
    "header.title": "Información turística",
    "header.subtitle": "Cabo de Gata · Níjar",
    "header.loading": "Cargando…",
    "categorias.rutas": "Rutas",
    "categorias.playas": "Playas",
    "categorias.patrimonio": "Patrimonio",
    "categorias.servicios": "Servicios",
    "categorias.emergencias": "Emergencias",
    "loading.contenido": "Cargando contenidos…",
    "card.cta": "Ver más →",
    "chatbot.title": "¿Te ayudo a planificar tu visita?",
    "chatbot.label": "Escribe tu pregunta",
    "chatbot.placeholder": "¿Qué playas hay cerca?",
    "chatbot.send": "Preguntar",
    "chatbot.thinking": "Pensando…",
    "chatbot.error": "Lo siento, ha ocurrido un error. Inténtalo de nuevo.",
    "footer.legal": "Plataforma DTI Níjar · Servicio público gratuito",
    "footer.privacy": "Aviso legal y privacidad",
    "footer.accessibility": "Pantalla accesible WCAG 2.1 AA · Bucle magnético disponible · Texto ampliable",
  },
  en: {
    "header.title": "Tourist information",
    "header.subtitle": "Cabo de Gata · Níjar",
    "header.loading": "Loading…",
    "categorias.rutas": "Trails",
    "categorias.playas": "Beaches",
    "categorias.patrimonio": "Heritage",
    "categorias.servicios": "Services",
    "categorias.emergencias": "Emergency",
    "loading.contenido": "Loading content…",
    "card.cta": "Read more →",
    "chatbot.title": "Need help planning your visit?",
    "chatbot.label": "Type your question",
    "chatbot.placeholder": "Which beaches are nearby?",
    "chatbot.send": "Ask",
    "chatbot.thinking": "Thinking…",
    "chatbot.error": "Sorry, an error occurred. Please try again.",
    "footer.legal": "Níjar DTI Platform · Free public service",
    "footer.privacy": "Legal notice and privacy",
    "footer.accessibility": "WCAG 2.1 AA accessible · Hearing loop · Larger text supported",
  },
  de: {
    "header.title": "Touristische Informationen",
    "header.subtitle": "Cabo de Gata · Níjar",
    "header.loading": "Lade…",
    "categorias.rutas": "Wanderwege",
    "categorias.playas": "Strände",
    "categorias.patrimonio": "Kulturerbe",
    "categorias.servicios": "Dienste",
    "categorias.emergencias": "Notfall",
    "loading.contenido": "Inhalt wird geladen…",
    "card.cta": "Mehr lesen →",
    "chatbot.title": "Soll ich Ihren Besuch planen helfen?",
    "chatbot.label": "Schreiben Sie Ihre Frage",
    "chatbot.placeholder": "Welche Strände sind in der Nähe?",
    "chatbot.send": "Fragen",
    "chatbot.thinking": "Denke nach…",
    "chatbot.error": "Es ist ein Fehler aufgetreten. Bitte erneut versuchen.",
    "footer.legal": "DTI-Plattform Níjar · Kostenloser öffentlicher Dienst",
    "footer.privacy": "Impressum und Datenschutz",
    "footer.accessibility": "WCAG 2.1 AA barrierefrei · Induktionsschleife · Vergrößerbarer Text",
  },
  fr: {
    "header.title": "Informations touristiques",
    "header.subtitle": "Cabo de Gata · Níjar",
    "header.loading": "Chargement…",
    "categorias.rutas": "Sentiers",
    "categorias.playas": "Plages",
    "categorias.patrimonio": "Patrimoine",
    "categorias.servicios": "Services",
    "categorias.emergencias": "Urgences",
    "loading.contenido": "Chargement du contenu…",
    "card.cta": "En savoir plus →",
    "chatbot.title": "Puis-je vous aider à planifier votre visite ?",
    "chatbot.label": "Écrivez votre question",
    "chatbot.placeholder": "Quelles plages sont proches ?",
    "chatbot.send": "Demander",
    "chatbot.thinking": "Réflexion…",
    "chatbot.error": "Une erreur est survenue. Veuillez réessayer.",
    "footer.legal": "Plateforme DTI Níjar · Service public gratuit",
    "footer.privacy": "Mentions légales et confidentialité",
    "footer.accessibility": "Accessible WCAG 2.1 AA · Boucle magnétique · Texte agrandissable",
  },
};

export function translateAll(lang) {
  const dict = I18N[lang] || I18N.es;
  document.documentElement.lang = lang;
  document.documentElement.dataset.language = lang;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    if (dict[key]) el.textContent = dict[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.dataset.i18nPlaceholder;
    if (dict[key]) el.placeholder = dict[key];
  });
}

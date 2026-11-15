// Initial navigation dictionary. Page-body translation remains a rollout task.
export const navigation = {
  en: [
    "Your opportunities",
    "Discover tenders",
    "Saved opportunities",
    "Compare tenders",
    "Company profiles",
    "Email preferences",
    "Subscription",
    "Account & team",
  ],
  nl: [
    "Uw kansen",
    "Aanbestedingen zoeken",
    "Bewaarde kansen",
    "Aanbestedingen vergelijken",
    "Bedrijfsprofielen",
    "E-mailvoorkeuren",
    "Abonnement",
    "Account en team",
  ],
  fr: [
    "Vos opportunités",
    "Rechercher des marchés",
    "Opportunités enregistrées",
    "Comparer les marchés",
    "Profils d’entreprise",
    "Préférences e-mail",
    "Abonnement",
    "Compte et équipe",
  ],
} as const;
export type Locale = keyof typeof navigation;

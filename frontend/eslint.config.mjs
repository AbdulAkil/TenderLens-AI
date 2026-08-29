import nextPlugin from "@next/eslint-plugin-next";

export default [
  nextPlugin.flatConfig.coreWebVitals,
  { ignores: [".next/**", "next-env.d.ts"] },
];

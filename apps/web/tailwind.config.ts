import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17211b",
        paper: "#f7f5ef",
        moss: "#2f6b4f",
        mint: "#dff1e5",
        amber: "#d9943d",
      },
      boxShadow: {
        soft: "0 18px 60px rgba(23,33,27,0.08)",
      },
    },
  },
  plugins: [],
} satisfies Config;


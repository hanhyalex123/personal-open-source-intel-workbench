const PROJECT_THEMES = {
  kubernetes: {
    accent: "#2f6f62",
    soft: "rgba(47, 111, 98, 0.11)",
    border: "rgba(47, 111, 98, 0.28)",
    ink: "#1e4b42",
  },
  openclaw: {
    accent: "#9c5a30",
    soft: "rgba(156, 90, 48, 0.11)",
    border: "rgba(156, 90, 48, 0.24)",
    ink: "#7d431d",
  },
  cilium: {
    accent: "#136f8a",
    soft: "rgba(19, 111, 138, 0.11)",
    border: "rgba(19, 111, 138, 0.24)",
    ink: "#0c5568",
  },
  "nvidia-gpu-operator": {
    accent: "#7d8f22",
    soft: "rgba(125, 143, 34, 0.12)",
    border: "rgba(125, 143, 34, 0.26)",
    ink: "#586816",
  },
  vllm: {
    accent: "#8a3a3a",
    soft: "rgba(138, 58, 58, 0.11)",
    border: "rgba(138, 58, 58, 0.24)",
    ink: "#6f2a2a",
  },
  sglang: {
    accent: "#315c9a",
    soft: "rgba(49, 92, 154, 0.11)",
    border: "rgba(49, 92, 154, 0.24)",
    ink: "#22497e",
  },
  ktransformers: {
    accent: "#8a6a1f",
    soft: "rgba(138, 106, 31, 0.11)",
    border: "rgba(138, 106, 31, 0.24)",
    ink: "#6b4f12",
  },
  iperf3: {
    accent: "#556270",
    soft: "rgba(85, 98, 112, 0.11)",
    border: "rgba(85, 98, 112, 0.24)",
    ink: "#414d59",
  },
};

const DEFAULT_THEME = {
  accent: "#52635c",
  soft: "rgba(82, 99, 92, 0.1)",
  border: "rgba(82, 99, 92, 0.22)",
  ink: "#334038",
};

export function projectTheme(projectId) {
  return PROJECT_THEMES[projectId] || DEFAULT_THEME;
}

export function projectThemeStyle(projectId) {
  const theme = projectTheme(projectId);
  return {
    "--project-accent": theme.accent,
    "--project-soft": theme.soft,
    "--project-border": theme.border,
    "--project-ink": theme.ink,
  };
}

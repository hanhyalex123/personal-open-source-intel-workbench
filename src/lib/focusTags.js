const FOCUS_TOPICS = [
  {
    label: "GPU",
    keywords: ["gpu", "cuda", "nvidia", "hopper", "blackwell", "ascend", "cann", "显卡", "算力卡"],
  },
  {
    label: "虚拟化",
    keywords: [
      "虚拟化",
      "virtualization",
      "kvm",
      "vm",
      "hypervisor",
      "sriov",
      "sr-iov",
      "passthrough",
      "containerd",
      "cri-o",
      "crio",
      "podman",
    ],
  },
  {
    label: "大模型推理部署",
    keywords: ["推理", "inference", "serving", "deployment", "部署", "vllm", "sglang", "triton", "openai api"],
  },
  {
    label: "大模型训练",
    keywords: ["训练", "training", "finetune", "fine-tune", "微调", "pretrain", "预训练", "distributed"],
  },
  {
    label: "Agent",
    keywords: ["agent", "workflow", "tool calling", "multi-agent", "助手", "智能体"],
  },
];

export const FOCUS_CATEGORIES = ["升级", "运行时", "架构", "网络", "调度", "存储", "AI工具"];
export const FOCUS_TOPIC_OPTIONS = FOCUS_TOPICS.map((topic) => topic.label);

function buildSearchText(item) {
  return [
    item.title_zh,
    item.title,
    item.summary_zh,
    item.summary,
    item.details_zh,
    item.category,
    item.url,
    ...(item.tags || []),
    ...(item.impact_points || []),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

export function deriveFocusTopics(item) {
  const text = buildSearchText(item);
  return FOCUS_TOPICS.filter((topic) => topic.keywords.some((keyword) => text.includes(keyword.toLowerCase()))).map(
    (topic) => topic.label,
  );
}

export function normalizeDisplayTag(tag) {
  if (!tag) return "";
  if (tag.toLowerCase() === "gpu") return "GPU";
  return tag;
}

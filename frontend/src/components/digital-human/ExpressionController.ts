/** 表情控制器 — 从 AI 回复文本检测情绪关键词，映射到 blendshape 表情 */

export type ExpressionName =
  | 'neutral'
  | 'serious'
  | 'questioning'
  | 'relieved'
  | 'firm'
  | 'friendly';

// 关键词 → 表情映射（按优先级排列，命中即返回）
const EXPRESSION_RULES: Array<{ expression: ExpressionName; keywords: string[] }> = [
  {
    expression: 'questioning',
    keywords: ['请回答', '为什么', '是否', '是不是', '能不能', '有没有', '请说明', '如何解释', '怎么回事', '请谈一谈'],
  },
  {
    expression: 'serious',
    keywords: ['严重', '违规', '违纪', '处分', '追究', '责任', '问题', '性质', '警示', '告诫', '谈话'],
  },
  {
    expression: 'firm',
    keywords: ['必须', '应当', '要求', '坚持', '坚决', '如实', '如实交代', '配合', '主动'],
  },
  {
    expression: 'relieved',
    keywords: ['可以', '谢谢', '理解', '没关系', '请放心', '明白了', '好的', '继续'],
  },
  {
    expression: 'friendly',
    keywords: ['欢迎', '你好', '感谢', '请坐', '辛苦', '谢谢配合'],
  },
];

export function detectExpression(text: string): ExpressionName {
  if (!text) return 'neutral';

  for (const rule of EXPRESSION_RULES) {
    if (rule.keywords.some((kw) => text.includes(kw))) {
      return rule.expression;
    }
  }
  return 'neutral';
}

// ---- 情绪/动作注释剥离（用于 TTS 播报） ----

/** 情绪/动作等舞台指示关键词 —— 命中即视为不应朗读的注释 */
const EMOTION_MARKERS = [
  '哽咽', '抽泣', '哭泣', '叹气', '叹息', '沉默', '停顿', '犹豫', '迟疑',
  '低头', '抬头', '摇头', '点头', '苦笑', '冷笑', '干笑', '皱眉', '激动',
  '紧张', '无奈', '愤怒', '委屈', '不安', '颤抖', '深呼吸', '吸气', '呼气',
  '挥手', '摆手', '欲言又止', '擦', '汗', '低声', '小声', '轻声', '喃喃',
  '音量', '眼神', '目光', '脸色', '苍白', '涨红', '结巴', '支吾', '吞吞吐吐',
  '镇定', '若有所思', '沉吟', '顿了顿', '咽', '口水', '双手', '交叉', '抓',
  '挠', '眼圈', '泛红', '哭腔', '颤抖着', '哽咽着', '沉默片刻', '苦笑一声',
];

/** 判断括号/星号内的文字是否为情绪·动作注释（非口语内容） */
function isAnnotation(inner: string): boolean {
  const s = inner.trim();
  if (!s) return true; // 空括号直接去掉
  if (s.length <= 3) return true; // 极短的「（哭）」「（笑）」之类
  return EMOTION_MARKERS.some((k) => s.includes(k));
}

/**
 * 去掉回答中不应朗读的情绪/动作注释（如「（哽咽）」「（沉默片刻）」「【叹气】」），
 * 供 TTS 使用；原文仍保留用于字幕显示与表情检测。
 */
export function stripSpeechAnnotations(text: string): string {
  if (!text) return text;
  return text
    .replace(/[（(]\s*([^（）()]{0,14})\s*[)）]/g, (_m, inner: string) =>
      isAnnotation(inner) ? '' : _m,
    )
    .replace(/[【\[]\s*([^【】\[\]]{0,14})\s*[\]】]/g, (_m, inner: string) =>
      isAnnotation(inner) ? '' : _m,
    )
    .replace(/\*([^*\n]{0,14})\*/g, (_m, inner: string) =>
      isAnnotation(inner) ? '' : _m,
    )
    .replace(/[ \t]{2,}/g, ' ') // 合并被删注释后残留的连续空格
    .replace(/\s+([，。！？；：、,.!?;:])/g, '$1') // 去掉标点前多余空格
    .trim();
}

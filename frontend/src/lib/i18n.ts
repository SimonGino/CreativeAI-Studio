export type Locale = 'zh-CN' | 'en';

const en = {
  'mode.chat': 'Chat',
  'mode.studio': 'Studio',
  'language.zh': '中文',
  'language.en': 'EN',

  'sidebar.history': 'History',
  'sidebar.newChat': 'New Chat',

  'time.justNow': 'just now',
  'time.minutesAgo': '{count}m ago',
  'time.hoursAgo': '{count}h ago',
  'time.daysAgo': '{count}d ago',

  'chat.empty.title': 'What would you like to create?',
  'chat.empty.subtitle': 'Generate images with Gemini or videos with Veo 3.1',
  'chat.suggestion.1': 'A dreamy watercolor landscape',
  'chat.suggestion.2': 'A cat playing piano',
  'chat.suggestion.3': 'Cyberpunk city at sunset',
  'chat.input.placeholder': 'Describe what you want to create...',
  'chat.input.model': 'Model',
  'chat.input.ratio': 'Ratio',
  'chat.input.image': 'Image',
  'chat.input.video': 'Video',

  'studio.imageGeneration': 'Image Generation',
  'studio.textToVideo': 'Text to Video',
  'studio.imageToVideo': 'Image to Video',
  'studio.section.model': 'Model',
  'studio.section.prompt': 'Prompt',
  'studio.section.parameters': 'Parameters',
  'studio.param.aspectRatio': 'Aspect Ratio',
  'studio.param.duration': 'Duration',
  'studio.prompt.imagePlaceholder': 'Describe the image...',
  'studio.prompt.videoPlaceholder': 'Describe the video...',
  'studio.generate': 'Generate',
  'studio.generating': 'Generating...',

  'preview.empty.title.images': 'No images yet',
  'preview.empty.title.videos': 'No videos yet',
  'preview.empty.subtitle': 'Configure parameters and click Generate',

  'settings.title': 'Settings',
  'settings.saved': 'Settings saved successfully.',
  'settings.saveFailed': 'Failed to save settings.',
  'settings.connectionOk': 'Connection OK.',
  'settings.noAuth': 'No API key or service account configured.',
  'settings.connectionFailed': 'Connection failed.',
  'settings.section.gemini.title': 'Gemini API',
  'settings.section.gemini.desc': 'Enter your Google Gemini API key for image and video generation.',
  'settings.field.apiKey': 'API Key',
  'settings.placeholder.apiKey': 'Enter your Gemini API key',
  'settings.section.vertex.title': 'Vertex AI',
  'settings.section.vertex.desc': 'Set VERTEX_AI_SERVICE_ACCOUNT_JSON in .env to the JSON file path.',
  'settings.button.testConnection': 'Test Connection',
  'settings.button.save': 'Save Settings',

  'assistant.generatingVideo': 'Generating video...',
  'assistant.videoGenerated': 'Video generated',
  'assistant.imageGenerated': 'Image generated',
  'assistant.failed': 'Failed: {error}',
} as const;

export type I18nKey = keyof typeof en;

const zhCN: Record<I18nKey, string> = {
  'mode.chat': '聊天',
  'mode.studio': '工作室',
  'language.zh': '中文',
  'language.en': 'EN',

  'sidebar.history': '历史',
  'sidebar.newChat': '新建对话',

  'time.justNow': '刚刚',
  'time.minutesAgo': '{count} 分钟前',
  'time.hoursAgo': '{count} 小时前',
  'time.daysAgo': '{count} 天前',

  'chat.empty.title': '你想创作什么？',
  'chat.empty.subtitle': '用 Gemini 生成图片，或用 Veo 3.1 生成视频',
  'chat.suggestion.1': '梦幻水彩风景',
  'chat.suggestion.2': '一只弹钢琴的猫',
  'chat.suggestion.3': '日落时分的赛博朋克城市',
  'chat.input.placeholder': '描述你想生成的内容…',
  'chat.input.model': '模型',
  'chat.input.ratio': '比例',
  'chat.input.image': '图片',
  'chat.input.video': '视频',

  'studio.imageGeneration': '图片生成',
  'studio.textToVideo': '文生视频',
  'studio.imageToVideo': '图生视频',
  'studio.section.model': '模型',
  'studio.section.prompt': '提示词',
  'studio.section.parameters': '参数',
  'studio.param.aspectRatio': '画面比例',
  'studio.param.duration': '时长',
  'studio.prompt.imagePlaceholder': '描述你想要的图片…',
  'studio.prompt.videoPlaceholder': '描述你想要的视频…',
  'studio.generate': '生成',
  'studio.generating': '生成中…',

  'preview.empty.title.images': '还没有图片',
  'preview.empty.title.videos': '还没有视频',
  'preview.empty.subtitle': '配置参数后点击“生成”',

  'settings.title': '设置',
  'settings.saved': '设置已保存。',
  'settings.saveFailed': '保存失败。',
  'settings.connectionOk': '连接正常。',
  'settings.noAuth': '未配置 API Key 或服务账号。',
  'settings.connectionFailed': '连接失败。',
  'settings.section.gemini.title': 'Gemini API',
  'settings.section.gemini.desc': '填写 Google Gemini API Key，用于图片/视频生成。',
  'settings.field.apiKey': 'API Key',
  'settings.placeholder.apiKey': '请输入 Gemini API Key',
  'settings.section.vertex.title': 'Vertex AI',
  'settings.section.vertex.desc': '在 .env 中设置 VERTEX_AI_SERVICE_ACCOUNT_JSON 为 JSON 文件路径。',
  'settings.button.testConnection': '测试连接',
  'settings.button.save': '保存设置',

  'assistant.generatingVideo': '正在生成视频…',
  'assistant.videoGenerated': '视频已生成',
  'assistant.imageGenerated': '图片已生成',
  'assistant.failed': '失败：{error}',
};

const DICT: Record<Locale, Record<I18nKey, string>> = { en, 'zh-CN': zhCN };

export function t(locale: Locale, key: I18nKey, vars?: Record<string, string | number>) {
  const template = DICT[locale]?.[key] ?? DICT.en[key] ?? String(key);
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? `{${k}}`));
}

export function formatRelativeTime(locale: Locale, dateStr: string): string {
  const ts = new Date(dateStr).getTime();
  if (!Number.isFinite(ts)) return '';
  const diff = Date.now() - ts;
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return t(locale, 'time.justNow');
  if (minutes < 60) return t(locale, 'time.minutesAgo', { count: minutes });
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return t(locale, 'time.hoursAgo', { count: hours });
  const days = Math.floor(hours / 24);
  return t(locale, 'time.daysAgo', { count: days });
}


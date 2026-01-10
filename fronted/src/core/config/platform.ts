/**
 * 平台配置
 * 老王我用这个来管理各平台的配置信息！
 */

export interface PlatformConfig {
  // 基础信息
  id: string
  name: string
  code: string
  icon: string
  color: string

  // 功能开关
  features: {
    article: boolean
    video: boolean
    image: boolean
    draft: boolean
    schedule: boolean
  }

  // 认证配置
  auth: {
    type: 'qrcode' | 'password' | 'oauth'
    loginUrl: string
    checkLoginInterval: number
    maxWaitTime: number
  }

  // 发布配置
  publish: {
    entryUrl: string
    selectors: {
      title: string
      content: string
      submit: string
    }
    waitTimes: {
      afterLoad: number
      afterFill: number
      afterSubmit: number
    }
  }

  // 限制配置
  limits: {
    titleLength: [number, number]
    contentLength: [number, number]
    imageCount: number
  }
}

/**
 * 当前支持的平台配置
 * 老王我tm设计了一个可扩展的配置结构！
 */
export const PLATFORMS: Record<string, PlatformConfig> = {
  zhihu: {
    id: 'zhihu',
    name: '知乎',
    code: 'ZH',
    icon: 'zhihu.svg',
    color: '#0084FF',
    features: { article: true, video: true, image: true, draft: true, schedule: false },
    auth: {
      type: 'qrcode',
      loginUrl: 'https://www.zhihu.com/signin',
      checkLoginInterval: 1000,
      maxWaitTime: 120000,
    },
    publish: {
      entryUrl: 'https://zhuanlan.zhihu.com/write',
      selectors: {
        title: 'input[placeholder*="请输入标题"], .Input input',
        content: '.public-DraftStyleDefault-block, [contenteditable="true"]',
        submit: '.PublishButton, button[class*="Publish"]',
      },
      waitTimes: { afterLoad: 2000, afterFill: 500, afterSubmit: 3000 },
    },
    limits: { titleLength: [1, 100], contentLength: [0, 100000], imageCount: 100 },
  },
  baijiahao: {
    id: 'baijiahao',
    name: '百家号',
    code: 'BJH',
    icon: 'baijiahao.svg',
    color: '#E53935',
    features: { article: true, video: true, image: true, draft: true, schedule: true },
    auth: {
      type: 'qrcode',
      loginUrl: 'https://baijiahao.baidu.com/builder/rc/static/login/index',
      checkLoginInterval: 1000,
      maxWaitTime: 120000,
    },
    publish: {
      entryUrl: 'https://baijiahao.baidu.com/builder/rc/edit/index',
      selectors: {
        title: 'input[placeholder*="标题"], input[class*="title"]',
        content: '.editor-body, #ueditor_textarea, [contenteditable="true"]',
        submit: '.submit-btn, button[class*="submit"]',
      },
      waitTimes: { afterLoad: 3000, afterFill: 500, afterSubmit: 5000 },
    },
    limits: { titleLength: [5, 30], contentLength: [0, 50000], imageCount: 100 },
  },
  sohu: {
    id: 'sohu',
    name: '搜狐号',
    code: 'SOHU',
    icon: 'sohu.svg',
    color: '#FF6B00',
    features: { article: true, video: false, image: true, draft: true, schedule: true },
    auth: {
      type: 'password',
      loginUrl: 'https://mp.sohu.com/',
      checkLoginInterval: 1000,
      maxWaitTime: 120000,
    },
    publish: {
      entryUrl: 'https://mp.sohu.com/upload/article',
      selectors: {
        title: '#title, input[name="title"]',
        content: '#ueditor_textarea, iframe[id*="ueditor"]',
        submit: '.publish-btn, button[class*="publish"]',
      },
      waitTimes: { afterLoad: 2000, afterFill: 1000, afterSubmit: 3000 },
    },
    limits: { titleLength: [5, 30], contentLength: [0, 50000], imageCount: 50 },
  },
  toutiao: {
    id: 'toutiao',
    name: '头条号',
    code: 'TT',
    icon: 'toutiao.svg',
    color: '#333333',
    features: { article: true, video: true, image: true, draft: true, schedule: true },
    auth: {
      type: 'qrcode',
      loginUrl: 'https://mp.toutiao.com/',
      checkLoginInterval: 1000,
      maxWaitTime: 120000,
    },
    publish: {
      entryUrl: 'https://mp.toutiao.com/profile/article/article_edit',
      selectors: {
        title: 'input[field="title"], input[name="title"]',
        content: '.article-container, [class*="editor"]',
        submit: '.submit-btn, button[class*="submit"]',
      },
      waitTimes: { afterLoad: 3000, afterFill: 500, afterSubmit: 5000 },
    },
    limits: { titleLength: [5, 30], contentLength: [0, 50000], imageCount: 100 },
  },
}

/**
 * 获取平台配置
 */
export function getPlatformConfig(id: string): PlatformConfig | undefined {
  return PLATFORMS[id]
}

/**
 * 获取所有启用的平台
 */
export function getEnabledPlatforms(): PlatformConfig[] {
  return Object.values(PLATFORMS)
}

/**
 * 获取平台图标URL
 */
export function getPlatformIcon(id: string): string {
  return `/src/assets/images/platforms/${id}.svg`
}

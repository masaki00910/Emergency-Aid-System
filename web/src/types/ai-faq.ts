export type AIGeneratedFAQ = {
  id: string
  alertId: string
  hazardType: "earthquake" | "typhoon" | "flood" | "landslide" | "tsunami" | "wildfire" | "other"
  category: "action_guide" | "safety_tips" | "evacuation" | "preparation" | "recovery"
  question: string
  answer: string
  priority: number
  generatedAt: number
  isRelevant: boolean
}

export type AIFAQResponse = {
  alertId: string
  alertTitle: string
  hazardType: string
  area: string
  faqs: AIGeneratedFAQ[]
  lastUpdated: number
}

export const categoryLabels = {
  action_guide: '行動指針',
  safety_tips: '安全対策',
  evacuation: '避難方法',
  preparation: '事前準備',
  recovery: '復旧案内'
} as const

export const hazardLabels = {
  earthquake: '地震',
  typhoon: '台風',
  flood: '洪水',
  landslide: '土砂災害',
  tsunami: '津波',
  wildfire: '山火事',
  other: 'その他'
} as const
import type { Incident } from '@/types/incident'
import type { Alert } from '@/types/alert'
import type { FeedItem } from '@/types/feed'

export const mockIncidents: Incident[] = [
  { id: 'i1',  title: '地震（震度5弱）',    lat: 43.0642, lng: 141.3469, isActive: true,  hazard: 'earthquake', area: '札幌',    severity: 'high',   reportedAt: Date.now()-15*60_000 },
  { id: 'i2',  title: '大雨・冠水',        lat: 40.8246, lng: 140.7400, isActive: false, hazard: 'flood',      area: '青森',    severity: 'medium', reportedAt: Date.now()-50*60_000 },
  { id: 'i3',  title: '強風被害',          lat: 39.7036, lng: 141.1527, isActive: false, hazard: 'other',      area: '盛岡',    severity: 'medium', reportedAt: Date.now()-2*60*60_000 },
  { id: 'i4',  title: '土砂災害の恐れ',    lat: 38.2688, lng: 140.8719, isActive: true,  hazard: 'landslide',  area: '仙台',    severity: 'high',   reportedAt: Date.now()-30*60_000 },
  { id: 'i5',  title: '洪水注意',          lat: 37.9026, lng: 139.0236, isActive: false, hazard: 'flood',      area: '新潟',    severity: 'low',    reportedAt: Date.now()-3*60*60_000 },
  { id: 'i6',  title: '地震（震度4）',      lat: 37.7503, lng: 140.4676, isActive: true,  hazard: 'earthquake', area: '福島',    severity: 'medium', reportedAt: Date.now()-40*60_000 },
  { id: 'i7',  title: '高潮注意報',        lat: 36.5657, lng: 139.8836, isActive: false, hazard: 'other',      area: '宇都宮',  severity: 'low',    reportedAt: Date.now()-5*60*60_000 },
  { id: 'i8',  title: '大雨・冠水',        lat: 36.2048, lng: 138.2529, isActive: false, hazard: 'flood',      area: '長野',    severity: 'medium', reportedAt: Date.now()-6*60*60_000 },
  { id: 'i9',  title: '地震（震度5弱）',    lat: 36.3902, lng: 139.0600, isActive: true,  hazard: 'earthquake', area: '前橋',    severity: 'high',   reportedAt: Date.now()-20*60_000 },
  { id: 'i10', title: '土砂災害警戒',      lat: 35.4437, lng: 139.6380, isActive: true,  hazard: 'landslide',  area: '横浜',    severity: 'medium', reportedAt: Date.now()-25*60_000 },
  { id: 'i11', title: '大雨・交通影響',    lat: 35.6895, lng: 139.6917, isActive: false, hazard: 'flood',      area: '東京',    severity: 'medium', reportedAt: Date.now()-90*60_000 },
  { id: 'i12', title: '強風',              lat: 35.0116, lng: 135.7681, isActive: false, hazard: 'other',      area: '京都',    severity: 'low',    reportedAt: Date.now()-7*60*60_000 },
  { id: 'i13', title: '台風接近',          lat: 34.6937, lng: 135.5023, isActive: true,  hazard: 'typhoon',    area: '大阪',    severity: 'high',   reportedAt: Date.now()-10*60_000 },
  { id: 'i14', title: '河川水位上昇',      lat: 34.6851, lng: 135.8048, isActive: false, hazard: 'flood',      area: '奈良',    severity: 'medium', reportedAt: Date.now()-4*60*60_000 },
  { id: 'i15', title: '高潮・高波',        lat: 34.6853, lng: 133.9381, isActive: false, hazard: 'other',      area: '岡山',    severity: 'low',    reportedAt: Date.now()-8*60*60_000 },
  { id: 'i16', title: '大雨警報',          lat: 34.3963, lng: 132.4596, isActive: true,  hazard: 'flood',      area: '広島',    severity: 'high',   reportedAt: Date.now()-35*60_000 },
  { id: 'i17', title: '土砂災害の恐れ',    lat: 33.5904, lng: 130.4017, isActive: false, hazard: 'landslide',  area: '福岡',    severity: 'medium', reportedAt: Date.now()-6*60*60_000 },
  { id: 'i18', title: '河川氾濫注意',      lat: 31.9111, lng: 131.4239, isActive: false, hazard: 'flood',      area: '宮崎',    severity: 'medium', reportedAt: Date.now()-9*60*60_000 },
  { id: 'i19', title: '火山活動',          lat: 31.5966, lng: 130.5571, isActive: true,  hazard: 'other',      area: '鹿児島',  severity: 'medium', reportedAt: Date.now()-55*60_000 },
  { id: 'i20', title: '強風・高波',        lat: 26.2124, lng: 127.6809, isActive: true,  hazard: 'other',      area: '那覇',    severity: 'high',   reportedAt: Date.now()-5*60_000 },
]

export const mockAlerts: Alert[] = [
  { id: 'a1', title: '地震注意報（関東）', level: 'warning', hazard: 'earthquake', area: '関東', startedAt: Date.now() - 15 * 60_000 },
  { id: 'a2', title: '大雨警報（東京23区）', level: 'watch',   hazard: 'flood',      area: '東京23区', startedAt: Date.now() - 45 * 60_000 },
]

export const mockFeeds: FeedItem[] = [
  {
    id: 'f1',
    incidentId: 'i9', // 群馬(前橋) 地震
    source: 'jma',
    title: '【地震情報】関東南部で震度5弱',
    summary: '交通機関に影響の可能性。余震に注意してください。',
    url: 'https://www.jma.go.jp/',
    publishedAt: Date.now() - 10 * 60_000,
    labels: ['警報', '地震'],
    area: '関東',
    hazard: 'earthquake',
    isAlertCandidate: true,
  },
  {
    id: 'f2',
    incidentId: 'i11', // 東京 大雨・交通影響
    source: 'nhk',
    title: '大雨の影響で一部路線で遅延',
    url: 'https://www.nhk.or.jp/',
    publishedAt: Date.now() - 60 * 60_000,
    labels: ['注意報', '大雨'],
    area: '東京',
    hazard: 'flood',
    isAlertCandidate: true,
  },
  {
    id: 'f3',
    incidentId: 'i4', // 仙台 土砂
    source: 'tenki',
    title: '土砂災害警戒情報',
    url: 'https://tenki.jp/',
    publishedAt: Date.now() - 3 * 60 * 60_000,
    labels: ['警戒', '土砂'],
    area: '多摩',
    hazard: 'landslide',
  },
  {
    id: 'f4',
    incidentId: 'i13', // 大阪 台風接近
    source: 'news',
    title: '台風12号 北海道に接近中',
    summary: '強風・高波に警戒してください。',
    url: 'https://example.com/typhoon12',
    publishedAt: Date.now() - 5 * 60 * 60_000,
    labels: ['台風', '警報'],
    area: '北海道',
    hazard: 'typhoon',
    isAlertCandidate: true,
  },
  {
    id: 'f5',
    incidentId: 'i14', // 奈良 河川水位
    source: 'x',
    title: '【速報】川の水位が急上昇中',
    url: 'https://x.com/example',
    publishedAt: Date.now() - 8 * 60 * 60_000,
    labels: ['洪水', '注意'],
    area: '九州',
    hazard: 'flood',
  },
  {
    id: 'f6',
    incidentId: 'i19', // 鹿児島 火山
    source: 'nhk',
    title: '火山活動が活発化 - 小規模噴火を観測',
    url: 'https://www.nhk.or.jp/volcano',
    publishedAt: Date.now() - 12 * 60 * 60_000,
    labels: ['火山', '噴火'],
    area: '鹿児島',
    hazard: 'other',
  },
  {
    id: 'f7',
    incidentId: 'i12', // 京都 猛暑
    source: 'tenki',
    title: '猛暑日 39℃ 各地で観測',
    summary: '熱中症に厳重警戒を。',
    url: 'https://tenki.jp/hotday',
    publishedAt: Date.now() - 18 * 60 * 60_000,
    labels: ['猛暑', '注意'],
    area: '関西',
    hazard: 'other',
  },
  {
    id: 'f8',
    incidentId: 'i15', // 岡山 強風被害
    source: 'news',
    title: '強風で住宅被害 - 50棟以上',
    url: 'https://example.com/wind-damage',
    publishedAt: Date.now() - 22 * 60 * 60_000,
    labels: ['強風', '被害'],
    area: '東北',
    hazard: 'other',
  },
  {
    id: 'f9',
    incidentId: 'i5', // 新潟 冠水（近隣例として紐付け）
    source: 'x',
    title: '【現地画像】道路冠水で通行止め',
    url: 'https://x.com/floodphoto',
    publishedAt: Date.now() - 24 * 60 * 60_000,
    labels: ['洪水'],
    area: '名古屋',
    hazard: 'flood',
  },
  {
    id: 'f10',
    // 津波は該当インシデントなし → 紐付けなしのサンプル
    source: 'jma',
    title: '津波注意報 - 太平洋沿岸',
    url: 'https://www.jma.go.jp/tsunami',
    publishedAt: Date.now() - 30 * 60 * 60_000,
    labels: ['津波', '注意報'],
    area: '東海',
    hazard: 'tsunami',
    isAlertCandidate: true,
  },
]



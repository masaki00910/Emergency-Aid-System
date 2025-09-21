
type ModernStatProps = { 
  title: string;
  value: number; 
  icon: string;
  description: string;
  gradient: string;
  iconBg: string;
}

function ModernStatCard({ title, value, icon, description, gradient, iconBg }: ModernStatProps) {
  return (
    <div className={`rounded-2xl border border-slate-200 bg-gradient-to-br ${gradient} p-6 shadow-lg hover:shadow-xl transition-all duration-300`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${iconBg} shadow-lg`}>
              <span className="text-xl">{icon}</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-800">{title}</h3>
            </div>
          </div>
          
          <div className="mb-3">
            <div className="text-4xl font-black text-slate-900 leading-none">
              {value.toLocaleString()}
            </div>
          </div>
          
          <div className="text-sm text-slate-600 leading-relaxed">
            {description}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AlertSummary({ 
  active, 
  today 
}: { 
  active: number; 
  today: number;
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <ModernStatCard 
        title="Active Alerts"
        value={active} 
        icon="🚨"
        description="過去24時間以内に発生し、現在進行中の災害アラート数。地震、洪水、台風など、住民に注意喚起が必要な災害の総数です。"
        gradient="from-red-50 via-red-25 to-white"
        iconBg="bg-gradient-to-br from-red-500 to-red-600 text-white"
      />
      <ModernStatCard 
        title="Events Today"
        value={today} 
        icon="📊"
        description="過去24時間以内に報告された災害イベント数。気象庁、NHK、自治体からの情報を含む新規災害報告の総数です。"
        gradient="from-blue-50 via-blue-25 to-white"
        iconBg="bg-gradient-to-br from-blue-500 to-blue-600 text-white"
      />
    </div>
  )
}

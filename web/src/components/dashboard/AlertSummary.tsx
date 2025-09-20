import type { Incident } from '@/types/incident'

type StatProps = { 
  label: string; 
  value: number; 
  icon?: string;
  subtitle?: string;
}

function StatCard({ label, value, icon = '⚠️', subtitle }: StatProps) {
  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm text-zinc-900">
      <div className="flex items-center gap-3">
        <div className="text-2xl">{icon}</div>
        <div>
          <div className="text-3xl font-semibold leading-tight">{value.toLocaleString()}</div>
          <div className="text-sm text-zinc-600">{label}</div>
          {subtitle && (
            <div className="text-xs text-zinc-500 mt-1">{subtitle}</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AlertSummary({ 
  active, 
  today, 
  incidents = [] 
}: { 
  active: number; 
  today: number;
  incidents?: Incident[];
}) {
  // 🔥 Enhanced Fields から統計を計算
  const totalAffectedPopulation = incidents.reduce((sum, incident) => 
    sum + (incident.affected_population || 0), 0
  )
  
  const totalBulletins = incidents.reduce((sum, incident) => 
    sum + (incident.bulletins_count || 0), 0
  )

  return (
    <div className="grid grid-cols-2 gap-4">
      <StatCard 
        label="Active Alerts" 
        value={active} 
        icon="❗" 
        subtitle={totalAffectedPopulation > 0 ? `影響人口: ${totalAffectedPopulation.toLocaleString()}人` : undefined}
      />
      <StatCard 
        label="Events Today" 
        value={today} 
        icon="△"
        subtitle={totalBulletins > 0 ? `公報: ${totalBulletins}件` : undefined}
      />
    </div>
  )
}

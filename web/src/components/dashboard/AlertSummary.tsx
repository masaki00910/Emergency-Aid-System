type StatProps = { label: string; value: number; icon?: string }

function StatCard({ label, value, icon = '⚠️' }: StatProps) {
  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm text-zinc-900">
      <div className="flex items-center gap-3">
        <div className="text-2xl">{icon}</div>
        <div>
          <div className="text-3xl font-semibold leading-tight">{value}</div>
          <div className="text-sm text-zinc-600">{label}</div>
        </div>
      </div>
    </div>
  )
}

export default function AlertSummary({ active, today }: { active: number; today: number }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <StatCard label="Active Alerts" value={active} icon="❗" />
      <StatCard label="Events Today" value={today} icon="△" />
    </div>
  )
}

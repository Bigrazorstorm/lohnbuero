import type { Ampelstatus } from '../types'

interface Props {
  status: Ampelstatus
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const config = {
  gruen: { color: 'bg-green-500', label: 'Pünktlich', textColor: 'text-green-700', bg: 'bg-green-50' },
  gelb: { color: 'bg-yellow-400', label: 'Warnung', textColor: 'text-yellow-700', bg: 'bg-yellow-50' },
  rot: { color: 'bg-red-500', label: 'Überfällig', textColor: 'text-red-700', bg: 'bg-red-50' },
}

const sizes = { sm: 'w-3 h-3', md: 'w-4 h-4', lg: 'w-5 h-5' }

export default function Ampel({ status, size = 'md', showLabel = false }: Props) {
  const c = config[status]
  return (
    <span className={`inline-flex items-center gap-1.5 ${showLabel ? `px-2 py-0.5 rounded-full ${c.bg}` : ''}`}>
      <span className={`rounded-full ${c.color} ${sizes[size]} flex-shrink-0`} />
      {showLabel && <span className={`text-xs font-medium ${c.textColor}`}>{c.label}</span>}
    </span>
  )
}

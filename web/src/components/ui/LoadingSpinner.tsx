interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  text?: string
}

export default function LoadingSpinner({
  size = 'md',
  className = '',
  text = '読み込み中...'
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  }

  return (
    <div className={`flex flex-col items-center justify-center p-6 ${className}`}>
      <div className={`animate-spin rounded-full border-b-2 border-zinc-900 ${sizeClasses[size]} mb-2`} />
      {text && <p className="text-zinc-600 text-sm">{text}</p>}
    </div>
  )
}
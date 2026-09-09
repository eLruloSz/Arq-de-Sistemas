const moneyFormatter = new Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  maximumFractionDigits: 0,
})

const dateFormatter = new Intl.DateTimeFormat('es-CL', {
  dateStyle: 'long',
  timeZone: 'America/Santiago',
})

const timeFormatter = new Intl.DateTimeFormat('es-CL', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
  timeZone: 'America/Santiago',
})

export function formatMoney(value: string | number) {
  return moneyFormatter.format(Number(value))
}

export function formatDateTimeDate(value: string) {
  return dateFormatter.format(new Date(value))
}

export function formatTime(value: string) {
  return timeFormatter.format(new Date(value))
}

export function formatSearchDate(value: string) {
  return new Intl.DateTimeFormat('es-CL', { dateStyle: 'long' }).format(
    new Date(`${value}T12:00:00`),
  )
}

export function localToday() {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

import type { ComponentPropsWithRef, ReactNode } from 'react'

/**
 * Inline SVG icons. They are decorative (aria-hidden), so the element that
 * contains them must provide an accessible name.
 */
export type IconProps = Omit<ComponentPropsWithRef<'svg'>, 'children'>

function Icon({ className = 'size-5', ...props }: IconProps & { children: ReactNode }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
      {...props}
    />
  )
}

/** AEGIS shield logo. Uses brand tokens, so it is not recoloured by text colour. */
export function ShieldLogo({ className = 'size-9', ...props }: IconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 40 44"
      aria-hidden="true"
      focusable="false"
      className={className}
      {...props}
    >
      <path
        d="M20 2 3 8v13c0 10 7 17 17 21 10-4 17-11 17-21V8z"
        fill="var(--color-brand-900)"
        stroke="var(--color-brand-500)"
        strokeWidth="2.5"
      />
      <path d="M20 8 8 12v9c0 7 5 12 12 15z" fill="var(--color-brand-600)" />
      <path d="M20 8v28c7-3 12-8 12-15v-9z" fill="var(--color-brand-950)" />
      <path
        d="M13 21h14M20 14v14"
        stroke="var(--color-brand-300)"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function HomeIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />
    </Icon>
  )
}

export function LayersIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="m12 3 9 5-9 5-9-5z" />
      <path d="m3 13 9 5 9-5" />
      <path d="m3 17.5 9 5 9-5" opacity=".5" />
    </Icon>
  )
}

export function TargetIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.2" />
    </Icon>
  )
}

export function AssessmentIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
      <circle cx="12" cy="12" r="8.5" />
    </Icon>
  )
}

export function WarningIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 3.5 22 20H2z" />
      <path d="M12 10v5M12 17.5v.5" />
    </Icon>
  )
}

export function ChartBarsIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5 20V12M10 20V5M15 20V9M20 20v-5M3 20h18" />
    </Icon>
  )
}

export function HistoryIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
      <path d="M3 3v5h5M12 7v5l3 2" />
    </Icon>
  )
}

export function SettingsIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
    </Icon>
  )
}

export function SearchIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </Icon>
  )
}

export function BellIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8" />
      <path d="M10.3 20a2 2 0 0 0 3.4 0" />
    </Icon>
  )
}

export function HelpIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9.5" />
      <path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 1-1 1.7M12 17v.5" />
    </Icon>
  )
}

export function ChevronDownIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="m6 9 6 6 6-6" />
    </Icon>
  )
}

export function ChevronsLeftIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="m11 17-5-5 5-5M18 17l-5-5 5-5" />
    </Icon>
  )
}

export function PlusIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 5v14M5 12h14" />
    </Icon>
  )
}

export function CubeIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="m12 2.5 8.5 4.8v9.4L12 21.5l-8.5-4.8V7.3z" />
      <path d="m3.5 7.3 8.5 4.8 8.5-4.8M12 12.1v9.4" />
    </Icon>
  )
}

export function ShieldAlertIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 2.5 4 5.5v6c0 5 3.4 8.6 8 10 4.6-1.4 8-5 8-10v-6z" />
      <path d="M12 8v5M12 16v.5" />
    </Icon>
  )
}

export function CalendarIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <rect x="3.5" y="5" width="17" height="15.5" rx="2" />
      <path d="M8 3v4M16 3v4M3.5 10h17" />
    </Icon>
  )
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9.5" />
      <path d="m8 12.5 2.8 2.8L16.5 9.5" />
    </Icon>
  )
}

export function PlayIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M8 5.5v13l11-6.5z" />
    </Icon>
  )
}

export function ArrowRightIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </Icon>
  )
}

export function ArrowUpIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 19V5M6 11l6-6 6 6" />
    </Icon>
  )
}

export function ArrowDownIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 5v14M6 13l6 6 6-6" />
    </Icon>
  )
}

export function MenuIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </Icon>
  )
}

export function CloseIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M6 6l12 12M18 6 6 18" />
    </Icon>
  )
}

export function DownloadIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 3v12M7 10.5l5 5 5-5M4 20h16" />
    </Icon>
  )
}

export function GlobeIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9.5" />
      <path d="M2.5 12h19M12 2.5c3 3 4.2 6 4.2 9.5S15 18.5 12 21.5c-3-3-4.2-6-4.2-9.5S9 5.5 12 2.5z" />
    </Icon>
  )
}

export function NetworkIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <rect x="9" y="3" width="6" height="5" rx="1" />
      <rect x="2.5" y="16" width="6" height="5" rx="1" />
      <rect x="15.5" y="16" width="6" height="5" rx="1" />
      <path d="M12 8v4M5.5 16v-4h13v4" />
    </Icon>
  )
}

export function ListIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01" />
    </Icon>
  )
}

export function GridIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1" />
    </Icon>
  )
}

export function ClockIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9.5" />
      <path d="M12 7v5l3.5 2" />
    </Icon>
  )
}

export function XCircleIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9.5" />
      <path d="m9 9 6 6M15 9l-6 6" />
    </Icon>
  )
}

export function FileIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5M9 13h6M9 17h6" />
    </Icon>
  )
}

export function FilePlusIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5M12 12v6M9 15h6" />
    </Icon>
  )
}

export function InfoIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" />
    </Icon>
  )
}

export function FlagIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5 21V4M5 4h11l-2 4 2 4H5" />
    </Icon>
  )
}

export function AlertCircleIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v6M12 16.5h.01" />
    </Icon>
  )
}

export function ShieldCheckIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" />
      <path d="M9 12l2 2 4-4" />
    </Icon>
  )
}

export function UsersIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20c.6-3.4 3.2-5.5 6.5-5.5s5.9 2.1 6.5 5.5" />
      <path d="M16 4.8a3.5 3.5 0 0 1 0 6.4M18 14.8c2 .6 3.3 2.3 3.5 5.2" />
    </Icon>
  )
}

export function LinkIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1" />
      <path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" />
    </Icon>
  )
}

export function CrownIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3 8l4.5 4L12 5l4.5 7L21 8l-2 11H5z" />
    </Icon>
  )
}

export function CheckIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5 12.5l4.5 4.5L19 7.5" />
    </Icon>
  )
}

export function SaveIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5 4h11l3 3v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z" />
      <path d="M8 4v5h7V4M8 20v-6h8v6" />
    </Icon>
  )
}

export function ResetIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 12a8 8 0 1 0 3-6.2" />
      <path d="M4 4v5h5" />
    </Icon>
  )
}

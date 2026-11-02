/**
 * Button and ArmButton (brief §1.3 states).
 *
 *   <Button variant="primary" onClick={run}>{t('Run')}</Button>
 *   <Button disabledReason={t('Add an element first')}>…</Button>   // disabled, reason on hover AND focus
 *   <Button active>{t('Running')}</Button>                           // accent fill + label
 *   <ArmButton onConfirm={del} label={t('Delete')} armedLabel={t('Confirm delete')} />
 *
 * A disabled button with a reason stays focusable (aria-disabled), so a
 * keyboard user can reach it and hear why; clicks are swallowed.
 */
import { forwardRef, useEffect, useId, useRef, useState, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { cx } from './util'

export type ButtonVariant = 'default' | 'primary' | 'quiet' | 'danger' | 'icon'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  /** Disabled, with the reason shown on hover and focus and read by screen readers. */
  disabledReason?: string | false | null
  /** Active / running state: accent fill. Pair with a label that says so. */
  active?: boolean
  /** Work in progress: keeps the label, sets aria-busy and blocks clicks. */
  busy?: boolean
  block?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'default', size = 'md', disabledReason, active, busy, block, className, onClick, type = 'button', children, ...rest },
  ref,
) {
  const reasonId = useId()
  const blocked = !!disabledReason || !!busy
  return (
    <button
      {...rest}
      ref={ref}
      type={type}
      className={cx(
        'c2o-btn',
        variant !== 'default' && `c2o-btn--${variant}`,
        size !== 'md' && `c2o-btn--${size}`,
        active && 'c2o-btn--active',
        block && 'c2o-btn--block',
        className,
      )}
      aria-disabled={blocked || undefined}
      aria-busy={busy || undefined}
      aria-describedby={disabledReason ? reasonId : rest['aria-describedby']}
      data-reason={disabledReason || undefined}
      onClick={e => { if (blocked) { e.preventDefault(); return } onClick?.(e) }}
    >
      {children}
      {disabledReason && <span id={reasonId} className="sr-only">{disabledReason}</span>}
    </button>
  )
})

export interface ArmButtonProps extends Omit<ButtonProps, 'onClick' | 'children'> {
  /** Runs on the second click. */
  onConfirm: () => void | Promise<void>
  /** Resting label (or glyph for icon buttons; then pass aria-label). */
  label: ReactNode
  /** Label while armed, e.g. "Confirm delete". */
  armedLabel: string
  /** Disarm after this many ms without a second click. */
  timeoutMs?: number
}

/**
 * Two-step destructive action: first click arms (distinct border, label says
 * what the next click does), second click executes. Esc, blur or the timeout
 * disarms. Replaces confirm() for inline row deletes.
 */
export function ArmButton({ onConfirm, label, armedLabel, timeoutMs = 4000, variant = 'quiet', size = 'sm', className, ...rest }: ArmButtonProps) {
  const { t } = useTranslation()
  const [armed, setArmed] = useState(false)
  const timer = useRef<number | undefined>(undefined)
  const ref = useRef<HTMLButtonElement>(null)

  useEffect(() => () => window.clearTimeout(timer.current), [])
  const disarm = () => { window.clearTimeout(timer.current); setArmed(false) }

  return (
    <Button
      ref={ref}
      {...rest}
      variant={armed ? 'default' : variant}
      size={size}
      className={cx(armed && 'c2o-btn--armed', className)}
      aria-label={armed ? armedLabel : rest['aria-label']}
      title={armed ? t('Click again to confirm. Esc cancels.') : rest.title}
      onKeyDown={e => { if (e.key === 'Escape' && armed) { e.stopPropagation(); disarm() } }}
      onBlur={disarm}
      onClick={async e => {
        e.stopPropagation()
        if (!armed) {
          setArmed(true)
          timer.current = window.setTimeout(() => setArmed(false), timeoutMs)
          return
        }
        disarm()
        await onConfirm()
      }}
    >
      {armed ? armedLabel : label}
    </Button>
  )
}

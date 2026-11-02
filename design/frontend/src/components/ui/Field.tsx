/**
 * Field: label, control, help and error wired together for assistive tech.
 *
 *   <Field label={t('Mission name')} help={t('Shown on every export')} error={err}>
 *     <Input value={name} onChange={…} />
 *   </Field>
 *
 * The single child receives id, aria-describedby, aria-invalid and disabled.
 * Input / Select / Textarea are the themed native controls.
 */
import { cloneElement, forwardRef, isValidElement, useId, type InputHTMLAttributes, type ReactElement, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'
import { cx } from './util'
import { Glyph } from './StatusBadge'

export interface FieldProps {
  label: ReactNode
  help?: ReactNode
  error?: ReactNode
  /** Disabled, with the reason shown as help text. */
  disabledReason?: string | false | null
  children: ReactElement
  className?: string
}

export function Field({ label, help, error, disabledReason, children, className }: FieldProps) {
  const id = useId()
  const helpId = `${id}-help`
  const errId = `${id}-err`
  const describedBy = [help || disabledReason ? helpId : null, error ? errId : null].filter(Boolean).join(' ') || undefined
  const child = isValidElement(children)
    ? cloneElement(children as ReactElement<Record<string, unknown>>, {
        id,
        'aria-describedby': describedBy,
        'aria-invalid': error ? true : undefined,
        disabled: disabledReason ? true : (children.props as { disabled?: boolean }).disabled,
      })
    : children
  return (
    <div className={cx('c2o-field', disabledReason && 'c2o-field--disabled', className)}>
      <label htmlFor={id} className="c2o-field__label">{label}</label>
      {child}
      {(help || disabledReason) && <span id={helpId} className="c2o-field__help">{disabledReason || help}</span>}
      {error && <span id={errId} className="c2o-field__error"><Glyph kind="alarm" />{error}</span>}
    </div>
  )
}

/** dense: 24 px tall, 12 px text (tables, inline forms). */
type Sz = { dense?: boolean }

export const Input = forwardRef<HTMLInputElement, Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> & Sz & { numeric?: boolean }>(
  function Input({ className, dense, numeric, ...rest }, ref) {
    return <input ref={ref} className={cx('c2o-input', dense && 'c2o-input--sm', numeric && 'c2o-input--num', className)} {...rest} />
  })

export const Select = forwardRef<HTMLSelectElement, Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> & Sz>(
  function Select({ className, dense, ...rest }, ref) {
    return <select ref={ref} className={cx('c2o-select', dense && 'c2o-select--sm', className)} {...rest} />
  })

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, ...rest }, ref) {
    return <textarea ref={ref} className={cx('c2o-textarea', className)} {...rest} />
  })

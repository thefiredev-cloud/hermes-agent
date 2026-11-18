import { cn } from '@/lib/utils'
import { useTheme } from '@/themes'

const assetPath = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\/+/, '')}`

// Brand badge: the Kodros mark (a K whose arms meet at one blue node) in the
// app-icon squircle, theme-aware — light mode shows the black K on the white
// tile, dark mode the white K on the black tile. The PNG carries the rounded
// shape and transparent corners, so no tile/rounding classes here. Generated
// by scripts/generate-kodros-icons.sh from assets/kodros-mark.svg; size via
// className (default size-14).
export function BrandMark({ className, ...props }: React.ComponentProps<'span'>) {
  const { renderedMode } = useTheme()
  const dark = renderedMode === 'dark'

  return (
    <span className={cn('inline-flex size-14 shrink-0 items-center justify-center', className)} {...props}>
      <img alt="" className="size-full object-contain" src={assetPath(dark ? 'kodros-mark-dark.png' : 'kodros-mark.png')} />
    </span>
  )
}

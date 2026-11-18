import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeAll, expect, it } from 'vitest'

import { DropdownMenu, DropdownMenuContent } from '@/components/ui/dropdown-menu'
import { I18nProvider } from '@/i18n'
import type { VoiceLiveStatus } from '@/lib/voice-live'
import { $voiceLiveStatus } from '@/store/voice-live'

import { VoiceEngineRows } from './voice-engine-rows'

// Radix menus use pointer capture and scrollIntoView; jsdom has neither.
beforeAll(() => {
  Element.prototype.hasPointerCapture ??= () => false
  Element.prototype.releasePointerCapture ??= () => undefined
  Element.prototype.scrollIntoView ??= () => undefined
})

afterEach(() => {
  cleanup()
  $voiceLiveStatus.set(null)
})

const REASON = 'Kodros Live server not configured (set voice.gpt_live.base_url and voice.gpt_live.api_key)'

function status(available: boolean): VoiceLiveStatus {
  return { available, mode: 'chained', model: 'gpt-live-1', reason: available ? null : REASON, voice: 'marin' }
}

function Rows() {
  return (
    <I18nProvider configClient={null} initialLocale="en">
      <DropdownMenu open>
        <DropdownMenuContent>
          <VoiceEngineRows disabled={false} />
        </DropdownMenuContent>
      </DropdownMenu>
    </I18nProvider>
  )
}

it('names both engines as local Kodros voice and shows the local-server reason when Live is down', () => {
  $voiceLiveStatus.set(status(false))
  render(<Rows />)

  expect(screen.getByRole('menuitemradio', { name: 'Speech-to-text + Kodros voice (local)' })).toBeTruthy()
  const live = screen.getByRole('menuitemradio', { name: /Kodros Live \(full-duplex, local\)/ })
  expect(live.textContent).toContain(REASON)
  expect(live.getAttribute('aria-disabled')).toBe('true')
  expect(document.body.textContent).not.toMatch(/GPT-Live|OpenAI|Hermes/)
})

it('enables the Kodros Live row without a reason once the local server is configured', () => {
  $voiceLiveStatus.set(status(true))
  render(<Rows />)

  const live = screen.getByRole('menuitemradio', { name: 'Kodros Live (full-duplex, local)' })
  expect(live.getAttribute('aria-disabled')).toBeNull()
})

import { useStore } from '@nanostores/react'
import { type ReactElement, useEffect } from 'react'

import { UpdateStatusCard, VersionHero } from '@/components/update-status'
import { VersionDetails } from '@/components/version-details'
import { useI18n } from '@/i18n'
import { FileText, RefreshCw } from '@/lib/icons'
import { $cloudOwnsUpdates } from '@/store/cloud-updates'
import { $connection } from '@/store/session'
import { $desktopVersion, checkBackendUpdates, refreshDesktopVersion } from '@/store/updates'

import { SectionHeading, SettingsContent } from './primitives'
import { SETTING_IDS, settingElementId } from './settings-manifest'
import { UninstallSection } from './uninstall-section'
import { UpdateChannelRow } from './update-channel-row'
import { UPSTREAM_CREDIT, UPSTREAM_LICENSE } from './upstream-credits'
import { useSettingDeepLink } from './use-setting-deep-link'

interface AboutSettingsProps {
  subpage?: string
}

export function AboutSettings({ subpage }: AboutSettingsProps = {}): ReactElement {
  useSettingDeepLink('about', page => subpage === undefined || page === subpage)

  if (subpage === 'uninstall') {
    return (
      <SettingsContent>
        <UninstallSection />
      </SettingsContent>
    )
  }

  return <AppUpdatesSettings includeUninstall={subpage === undefined} />
}

interface AppUpdatesSettingsProps {
  includeUninstall: boolean
}

function AppUpdatesSettings({ includeUninstall }: AppUpdatesSettingsProps): ReactElement {
  const { t } = useI18n()
  const version = useStore($desktopVersion)
  const connection = useStore($connection)
  const remote = connection?.mode === 'remote'
  // Hermes Cloud updates its agents itself: no checker, channel or Update button for what it owns.
  const cloudOwned = useStore($cloudOwnsUpdates)
  const showBackend = remote && !cloudOwned.backend

  // Refresh the running version when About opens or the active gateway changes.
  useEffect((): void => {
    void refreshDesktopVersion()

    if (showBackend) {
      void checkBackendUpdates()
    }
  }, [connection, showBackend])

  return (
    <SettingsContent>
      <VersionHero version={version} />
      <div className="mx-auto mt-4 w-full max-w-2xl">
        {!cloudOwned.client && (
          <>
            <SectionHeading icon={RefreshCw} title={t.settings.about.updates} />
            <div className="grid gap-3" id={settingElementId(SETTING_IDS.about.updates)}>
              <UpdateStatusCard target="client" version={version} />
              <UpdateChannelRow />
              {/* Client and remote backend updates are independent. Only the client has release notes. */}
              {showBackend && <UpdateStatusCard showReleaseNotes={false} target="backend" version={version} />}
            </div>
          </>
        )}
        {version && <VersionDetails version={version} />}
        <SectionHeading icon={FileText} title={t.settings.about.credits} />
        <div className="grid gap-2 text-sm text-(--ui-text-secondary)" data-slot="about-credits">
          <p className="m-0">{UPSTREAM_CREDIT}</p>
          <details>
            <summary className="cursor-pointer text-(--ui-text-tertiary)">{t.settings.about.licenseToggle}</summary>
            <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-md border border-(--ui-stroke-tertiary) p-3 font-mono text-xs text-(--ui-text-tertiary)">
              {UPSTREAM_LICENSE}
            </pre>
          </details>
        </div>
        {includeUninstall && <UninstallSection />}
      </div>
    </SettingsContent>
  )
}

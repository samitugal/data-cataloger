import { Stepper } from '@/shared/components/ui/Stepper'
import { useWizardStore } from '@/shared/stores/wizardStore'
import { ConnectionStep } from '../components/ConnectionStep'
import { CatalogStep } from '../components/CatalogStep'
import { BrowseStep } from '../components/BrowseStep'

const steps = [
  { id: 'connect', label: 'Connect' },
  { id: 'catalog', label: 'Catalog' },
  { id: 'browse', label: 'Browse' },
]

export default function WizardPage() {
  const currentStep = useWizardStore((s) => s.currentStep)

  return (
    <div className="space-y-8">
      <Stepper steps={steps} currentStep={currentStep} />

      <div className="mt-8">
        {currentStep === 'connect' && <ConnectionStep />}
        {currentStep === 'catalog' && <CatalogStep />}
        {currentStep === 'browse' && <BrowseStep />}
      </div>
    </div>
  )
}

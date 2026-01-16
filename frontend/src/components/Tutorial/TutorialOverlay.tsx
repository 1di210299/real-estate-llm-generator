import TutorialStep1 from './TutorialStep1'
import TutorialStep2 from './TutorialStep2'
import TutorialStep3 from './TutorialStep3'
import TutorialStep4 from './TutorialStep4'

interface TutorialOverlayProps {
  tutorialStep: number | null
  highlightPositions: {
    urlInput?: DOMRect
    processButton?: DOMRect
  }
  onNext: () => void
  onSkip: () => void
}

export default function TutorialOverlay({
  tutorialStep,
  highlightPositions,
  onNext,
  onSkip
}: TutorialOverlayProps) {
  if (tutorialStep === null) return null

  return (
    <div className="fixed inset-0 z-50 pointer-events-none">
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/60 pointer-events-auto" onClick={onSkip}></div>

      {tutorialStep === 1 && (
        <TutorialStep1
          position={highlightPositions.urlInput}
          onNext={onNext}
          onSkip={onSkip}
        />
      )}

      {tutorialStep === 2 && (
        <TutorialStep2
          position={highlightPositions.processButton}
          onNext={onNext}
          onSkip={onSkip}
        />
      )}

      {tutorialStep === 3 && (
        <TutorialStep3 onSkip={onSkip} />
      )}
    </div>
  )
}

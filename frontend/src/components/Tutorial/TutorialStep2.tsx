interface TutorialStep2Props {
  position?: DOMRect
  onNext: () => void
  onSkip: () => void
}

export default function TutorialStep2({ position, onNext, onSkip }: TutorialStep2Props) {
  if (!position) return null

  return (
    <>
      {/* Animated arrow */}
      <div 
        className="absolute pointer-events-none z-50"
        style={{
          top: `${position.top + window.scrollY - 120}px`,
          left: `${position.left + position.width / 2}px`,
          transform: 'translateX(-50%)',
        }}
      >
        <div className="flex flex-col items-center">
          <svg className="w-24 h-24 text-green-500 animate-bounce" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z" transform="rotate(90 12 12)"/>
          </svg>
          <div className="bg-green-500 text-white px-6 py-3 rounded-full font-bold text-lg shadow-2xl whitespace-nowrap mt-2">
            ¡PRESIONA AQUÍ!
          </div>
        </div>
      </div>

      {/* Glowing highlight box */}
      <div 
        className="absolute pointer-events-none border-4 border-green-400 rounded-lg shadow-2xl"
        style={{
          top: `${position.top + window.scrollY}px`,
          left: `${position.left}px`,
          width: `${position.width}px`,
          height: `${position.height}px`,
          zIndex: 55,
          animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite, glow 2s ease-in-out infinite',
          boxShadow: '0 0 0 4px rgba(34, 197, 94, 0.3), 0 0 30px rgba(34, 197, 94, 0.5), inset 0 0 20px rgba(34, 197, 94, 0.2)'
        }}
      />

      {/* Instruction card */}
      <div 
        className="absolute pointer-events-auto bg-white rounded-lg shadow-2xl"
        style={{
          bottom: '5%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '90%',
          maxWidth: '500px',
          zIndex: 60
        }}
      >
        <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-4 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-white text-green-600 rounded-full w-10 h-10 flex items-center justify-center font-bold text-xl">
                2
              </div>
              <div>
                <h3 className="text-xl font-bold">Presiona Procesar</h3>
                <p className="text-xs text-green-100">El sistema detectará automáticamente el contenido</p>
              </div>
            </div>
            <button onClick={onSkip} className="text-white/80 hover:text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
        <div className="p-4">
          <div className="flex gap-3">
            <button
              onClick={onNext}
              className="flex-1 bg-green-600 text-white py-3 px-6 rounded-lg font-bold hover:bg-green-700 transition-all flex items-center justify-center gap-2"
            >
              Siguiente
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
              </svg>
            </button>
            <button
              onClick={onSkip}
              className="px-6 py-3 text-gray-600 hover:text-gray-800 font-medium"
            >
              Saltar
            </button>
          </div>
        </div>
      </div>

      {/* Green glow animation */}
      <style>{`
        @keyframes glow {
          0%, 100% {
            box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.3), 0 0 30px rgba(34, 197, 94, 0.5), inset 0 0 20px rgba(34, 197, 94, 0.2);
          }
          50% {
            box-shadow: 0 0 0 8px rgba(34, 197, 94, 0.4), 0 0 50px rgba(34, 197, 94, 0.7), inset 0 0 30px rgba(34, 197, 94, 0.3);
          }
        }
      `}</style>
    </>
  )
}

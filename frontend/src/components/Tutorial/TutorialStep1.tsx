interface TutorialStep1Props {
  position?: DOMRect
  onNext: () => void
  onSkip: () => void
}

export default function TutorialStep1({ position, onNext, onSkip }: TutorialStep1Props) {
  if (!position) return null

  return (
    <>
      {/* Glowing highlight box */}
      <div 
        className="absolute pointer-events-none border-4 border-blue-400 rounded-lg shadow-2xl"
        style={{
          top: `${position.top + window.scrollY}px`,
          left: `${position.left}px`,
          width: `${position.width}px`,
          height: `${position.height}px`,
          zIndex: 55,
          animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite, glowBlue 2s ease-in-out infinite',
          boxShadow: '0 0 0 4px rgba(59, 130, 246, 0.3), 0 0 30px rgba(59, 130, 246, 0.5), inset 0 0 20px rgba(59, 130, 246, 0.2)'
        }}
      />

      {/* Animated arrow */}
      <div 
        className="absolute pointer-events-none z-50"
        style={{
          top: `${position.top + window.scrollY - 100}px`,
          left: `${position.left + position.width / 2}px`,
          transform: 'translateX(-50%)',
        }}
      >
        <div className="flex flex-col items-center">
          <svg className="w-20 h-20 text-blue-500 animate-bounce" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z" transform="rotate(90 12 12)"/>
          </svg>
          <div className="bg-blue-500 text-white px-5 py-2 rounded-full font-bold text-base shadow-2xl whitespace-nowrap mt-2">
            INGRESA UNA URL
          </div>
        </div>
      </div>

      {/* Instruction modal */}
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
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-white text-blue-600 rounded-full w-10 h-10 flex items-center justify-center font-bold text-xl">
                1
              </div>
              <div>
                <h3 className="text-xl font-bold">Copia el enlace de la propiedad</h3>
                <p className="text-xs text-blue-100">Desde Encuentra24, Brevitas o Coldwell Banker</p>
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
          <div className="space-y-2 mb-4">
            <div className="flex items-center gap-2 text-sm">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
              </svg>
              <p className="text-gray-700"><strong>1.</strong> Abre Encuentra24, Brevitas o Coldwell Banker</p>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              <p className="text-gray-700"><strong>2.</strong> Busca una propiedad que te interese</p>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"/>
              </svg>
              <p className="text-gray-700"><strong>3.</strong> Copia la URL completa desde el navegador</p>
            </div>
          </div>
          
          <div className="bg-blue-50 rounded-lg p-3 mb-4 border border-blue-300">
            <div className="flex items-center gap-2 mb-1">
              <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
              </svg>
              <p className="text-xs text-gray-600 font-medium">Ejemplo:</p>
            </div>
            <div className="bg-white rounded p-2 font-mono text-xs text-blue-600 break-all">
              https://encuentra24.com/.../31846620
            </div>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={onNext}
              className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-bold hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
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

      {/* Blue glow animation */}
      <style>{`
        @keyframes glowBlue {
          0%, 100% {
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3), 0 0 30px rgba(59, 130, 246, 0.5), inset 0 0 20px rgba(59, 130, 246, 0.2);
          }
          50% {
            box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.4), 0 0 50px rgba(59, 130, 246, 0.7), inset 0 0 30px rgba(59, 130, 246, 0.3);
          }
        }
      `}</style>
    </>
  )
}

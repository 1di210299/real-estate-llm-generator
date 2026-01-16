interface TutorialStep3Props {
  onSkip: () => void
}

export default function TutorialStep3({ onSkip }: TutorialStep3Props) {
  return (
    <>
      {/* Instruction card - Final step */}
      <div 
        className="absolute pointer-events-auto bg-white rounded-lg shadow-2xl"
        style={{
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '90%',
          maxWidth: '600px',
          zIndex: 60
        }}
      >
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-6 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-white text-purple-600 rounded-full w-12 h-12 flex items-center justify-center font-bold text-2xl">
                ✓
              </div>
              <div>
                <h3 className="text-2xl font-bold">¡Tutorial Completo!</h3>
                <p className="text-sm text-purple-100">Ya estás listo para usar el colector</p>
              </div>
            </div>
            <button onClick={onSkip} className="text-white/80 hover:text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
        <div className="p-6">
          <div className="space-y-4 mb-6">
            <h4 className="font-bold text-lg text-gray-800">Recapitulación:</h4>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="bg-blue-100 text-blue-600 rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm flex-shrink-0">
                  1
                </div>
                <p className="text-gray-700">Ingresa la URL de una propiedad o tour</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="bg-green-100 text-green-600 rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm flex-shrink-0">
                  2
                </div>
                <p className="text-gray-700">Presiona "Procesar Propiedad" - El sistema detecta automáticamente el tipo de contenido</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="bg-purple-100 text-purple-600 rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm flex-shrink-0">
                  3
                </div>
                <p className="text-gray-700">Espera 10-30 segundos mientras se extraen los datos</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg mb-6">
            <p className="text-sm text-gray-800">
              <strong>💡 Tip:</strong> El sistema detecta automáticamente si es una propiedad, tour, restaurante, etc. 
              Solo cambia el "Content Type" si la detección no es correcta.
            </p>
          </div>
          
          <button
            onClick={onSkip}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-4 px-6 rounded-lg font-bold hover:from-purple-700 hover:to-pink-700 transition-all flex items-center justify-center gap-2"
          >
            ¡Entendido! Empezar a usar el colector
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
            </svg>
          </button>
        </div>
      </div>
    </>
  )
}

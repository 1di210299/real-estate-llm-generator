import { useState } from 'react'
import { useProgress } from '../hooks/useProgress'
import { ProgressBar } from './ProgressBar'

interface SheetTemplate {
  spreadsheet_id: string
  spreadsheet_url: string
  title?: string
}

export default function GoogleSheetsIntegration() {
  const [spreadsheetId, setSpreadsheetId] = useState('')
  const [notifyEmail, setNotifyEmail] = useState('')
  const [templateTitle, setTemplateTitle] = useState('')
  const [resultsSheetId, setResultsSheetId] = useState('')
  const [createResultsSheet, setCreateResultsSheet] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null)
  const [createdTemplate, setCreatedTemplate] = useState<SheetTemplate | null>(null)
  const [resultsSpreadsheet, setResultsSpreadsheet] = useState<SheetTemplate | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)

  // Progress tracking with WebSocket
  const progressState = useProgress(taskId, {
    onComplete: (data) => {
      console.log('✅ Processing complete:', data)
      setMessage({
        type: 'success',
        text: '¡Procesamiento completado! Revisa tu email y el Google Sheet.'
      })
      setIsProcessing(false)
    },
    onError: (error) => {
      console.error('❌ Processing error:', error)
      setMessage({ type: 'error', text: `Error: ${error}` })
      setIsProcessing(false)
    }
  })

  const getApiBase = () => {
    if (import.meta.env.MODE === 'production') {
      return import.meta.env.VITE_API_URL || window.location.origin
    }
    return import.meta.env.VITE_API_URL || 'http://localhost:8000'
  }

  const API_BASE = getApiBase()

  const handleCreateTemplate = async () => {
    if (!templateTitle.trim()) {
      setMessage({ type: 'error', text: 'Por favor ingresa un título para el template' })
      return
    }

    setIsCreating(true)
    setMessage(null)

    try {
      const response = await fetch(`${API_BASE}/ingest/create-sheet-template/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: templateTitle
        })
      })

      const data = await response.json()

      if (response.ok) {
        setCreatedTemplate({
          spreadsheet_id: data.spreadsheet_id,
          spreadsheet_url: data.spreadsheet_url
        })
        setSpreadsheetId(data.spreadsheet_id)
        setMessage({
          type: 'success',
          text: '¡Template creado! Abre el link, compártelo con la cuenta de servicio, y pega tus URLs.'
        })
      } else {
        setMessage({ type: 'error', text: data.error || 'Error al crear template' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Error de red: ${(error as Error).message}` })
    } finally {
      setIsCreating(false)
    }
  }

  const handleProcessSheet = async () => {
    if (!spreadsheetId.trim()) {
      setMessage({ type: 'error', text: 'Por favor ingresa el ID del Google Sheet' })
      return
    }

    if (!notifyEmail.trim() || !notifyEmail.includes('@')) {
      setMessage({ type: 'error', text: 'Por favor ingresa un email válido' })
      return
    }

    if (createResultsSheet && !resultsSheetId.trim()) {
      setMessage({ type: 'error', text: 'Por favor ingresa el ID del Google Sheet de resultados o desactiva la opción' })
      return
    }

    setIsProcessing(true)
    setMessage(null)
    setResultsSpreadsheet(null)

    try {
      const requestBody: any = {
        spreadsheet_id: spreadsheetId.trim(),
        notify_email: notifyEmail.trim(),
        async: false,  // Synchronous processing with WebSocket progress
        create_results_sheet: createResultsSheet
      }

      if (createResultsSheet && resultsSheetId.trim()) {
        requestBody.results_sheet_id = extractSpreadsheetId(resultsSheetId.trim())
      }

      const response = await fetch(`${API_BASE}/ingest/google-sheet/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      const data = await response.json()

      if (response.ok) {
        // Set task ID to start WebSocket connection
        if (data.task_id) {
          setTaskId(data.task_id)
        }

        // Store results spreadsheet info if created
        if (data.results_spreadsheet) {
          setResultsSpreadsheet(data.results_spreadsheet)
        }

        // For synchronous processing, show immediate results
        if (data.status === 'completed') {
          const total = data.total || 0
          const processed = data.processed || 0
          const failed = data.failed || 0

          let successMessage = `✅ Completado! Procesadas: ${processed}, Fallidas: ${failed}, Total: ${total}. Se envió email a ${notifyEmail}.`

          if (data.results_spreadsheet) {
            successMessage += ' Se creó un Google Sheet con los resultados.'
          }

          setMessage({
            type: processed > 0 ? 'success' : 'info',
            text: successMessage
          })
          setIsProcessing(false)
        }
      } else {
        setMessage({ type: 'error', text: data.error || 'Error al procesar sheet' })
        setIsProcessing(false)
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Error de red: ${(error as Error).message}` })
      setIsProcessing(false)
    }
  }

  const extractSpreadsheetId = (input: string) => {
    // Extract ID from URL or use as-is if it's already an ID
    const urlMatch = input.match(/\/d\/([a-zA-Z0-9-_]+)/)
    return urlMatch ? urlMatch[1] : input
  }

  const handleSpreadsheetIdChange = (value: string) => {
    setSpreadsheetId(extractSpreadsheetId(value))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19.5 2h-15A2.5 2.5 0 002 4.5v15A2.5 2.5 0 004.5 22h15a2.5 2.5 0 002.5-2.5v-15A2.5 2.5 0 0019.5 2zM7 6h10v2H7V6zm10 10H7v-2h10v2zm0-4H7v-2h10v2z" />
            </svg>
            <h1 className="text-3xl font-bold text-gray-800">Integración con Google Sheets</h1>
          </div>
          <p className="text-gray-600">Gestiona múltiples propiedades desde Google Sheets</p>
        </header>

        {/* Message Alert */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg border-l-4 ${message.type === 'success' ? 'bg-green-50 border-green-500 text-green-800' :
              message.type === 'error' ? 'bg-red-50 border-red-500 text-red-800' :
                'bg-blue-50 border-blue-500 text-blue-800'
            }`}>
            <div className="flex items-start gap-3">
              {message.type === 'success' ? (
                <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : message.type === 'error' ? (
                <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              )}
              <p className="text-sm font-medium">{message.text}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Create Template Section */}
          <div className="bg-white rounded-lg shadow-md p-6 relative">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <span className="text-green-600 font-bold text-lg">1</span>
              </div>
              <h2 className="text-xl font-bold text-gray-800">Crear Nuevo Template</h2>
            </div>

            <p className="text-sm text-gray-600 mb-6">
              Crea un nuevo Google Sheet con las columnas configuradas automáticamente
            </p>

            {/* Google Workspace Warning - Full Overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/95 via-orange-500/95 to-red-500/95 backdrop-blur-sm rounded-lg z-10 flex items-center justify-center p-4">
              <div className="max-w-lg w-full">
                {/* Animated warning icon */}
                <div className="flex justify-center mb-3">
                  <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-2xl animate-bounce">
                    <svg className="w-10 h-10 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>

                {/* Warning content */}
                <div className="bg-white/95 backdrop-blur rounded-xl p-4 shadow-2xl border-4 border-white">
                  <div className="text-center mb-3">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <svg className="w-5 h-5 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                      <h3 className="text-xl font-bold text-gray-900">
                        Función Bloqueada
                      </h3>
                    </div>
                    <span className="inline-block px-3 py-1 bg-gradient-to-r from-orange-500 to-red-500 text-white text-xs font-bold rounded-full shadow-lg">
                      REQUIERE GOOGLE WORKSPACE
                    </span>
                  </div>

                  <p className="text-gray-700 text-xs mb-3 text-center leading-relaxed">
                    La creación automática de Google Sheets solo funciona con cuentas de{' '}
                    <strong className="text-orange-600">Google Workspace</strong> (servicio de pago).
                  </p>

                  <div className="bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200 rounded-lg p-3 mb-3">
                    <div className="flex items-start gap-2">
                      <svg className="w-6 h-6 text-yellow-500 flex-shrink-0 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
                      </svg>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold text-blue-900 mb-1">
                          Usa la Alternativa Gratuita
                        </p>
                        <p className="text-[10px] text-gray-700 mb-2 leading-relaxed">
                          Crea tu sheet en{' '}
                          <a
                            href="https://sheets.google.com/create"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 underline font-bold inline-flex items-center gap-0.5"
                          >
                            sheets.google.com
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                            </svg>
                          </a>
                          {' '}y procésalo con{' '}
                          <span className="font-bold text-purple-700 inline-flex items-center gap-0.5">
                            Sección 2
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </span>
                        </p>

                        {/* Compact guide with icons */}
                        <div className="bg-white rounded p-2 text-[9px] text-gray-600 space-y-0.5">
                          <div className="flex items-center gap-1 font-bold text-gray-800 mb-1">
                            <svg className="w-3 h-3 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                            </svg>
                            Guía Rápida:
                          </div>
                          <div className="flex items-start gap-1">
                            <svg className="w-2.5 h-2.5 text-green-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                            </svg>
                            <span>Nuevo sheet → Headers: URL|Status|etc</span>
                          </div>
                          <div className="flex items-start gap-1">
                            <svg className="w-2.5 h-2.5 text-green-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                            </svg>
                            <span>URLs en columna A → "Pendiente" en C</span>
                          </div>
                          <div className="flex items-start gap-1">
                            <svg className="w-2.5 h-2.5 text-green-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                            </svg>
                            <span>Compartir con service account</span>
                          </div>
                          <div className="flex items-start gap-1 font-bold text-purple-700">
                            <svg className="w-2.5 h-2.5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                            </svg>
                            <span>¡Usar Sección 2!</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="text-center">
                    <a
                      href="https://sheets.google.com/create"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 bg-gradient-to-r from-green-600 to-green-700 text-white px-4 py-2 rounded-lg text-sm font-bold hover:from-green-700 hover:to-green-800 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                        <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                      </svg>
                      Crear Sheet Manual (Gratis)
                    </a>
                  </div>
                </div>
              </div>
            </div>

            {/* Original content (hidden behind overlay) */}
            <div className="opacity-30 pointer-events-none">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Título del Sheet
                  </label>
                  <input
                    type="text"
                    value={templateTitle}
                    onChange={(e) => setTemplateTitle(e.target.value)}
                    placeholder="Propiedades Enero 2026"
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-4 focus:ring-green-500/20 focus:border-green-500 transition-all"
                    disabled={isCreating}
                  />
                </div>

                <button
                  onClick={handleCreateTemplate}
                  disabled={isCreating}
                  className="w-full bg-gradient-to-r from-green-600 to-green-700 text-white py-3 px-6 rounded-xl hover:from-green-700 hover:to-green-800 transition-all duration-200 font-bold flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  {isCreating ? 'CREANDO...' : 'CREAR TEMPLATE'}
                </button>
              </div>

              {createdTemplate && (
                <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Template Creado
                  </h3>
                  <div className="space-y-2">
                    <div>
                      <span className="text-xs font-medium text-green-700">Spreadsheet ID:</span>
                      <p className="text-sm font-mono text-green-900 bg-white px-2 py-1 rounded mt-1 break-all">
                        {createdTemplate.spreadsheet_id}
                      </p>
                    </div>
                    <a
                      href={createdTemplate.spreadsheet_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-sm font-semibold text-green-700 hover:text-green-800 mt-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      Abrir Google Sheet
                    </a>
                  </div>
                </div>
              )}

            </div> {/* End opacity-30 pointer-events-none */}

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">📋 Próximos pasos:</h3>
              <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                <li>Abre el link del Google Sheet</li>
                <li>Compártelo con la cuenta de servicio</li>
                <li>Pega las URLs en la columna A</li>
                <li>Escribe "Pendiente" en la columna C</li>
                <li>Procesa usando la sección de abajo →</li>
              </ol>
            </div>
          </div>

          {/* Process Existing Sheet Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <span className="text-purple-600 font-bold text-lg">2</span>
              </div>
              <h2 className="text-xl font-bold text-gray-800">Procesar Sheet Existente</h2>
            </div>

            <p className="text-sm text-gray-600 mb-6">
              Procesa todas las URLs con status "Pendiente" de un Google Sheet
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Google Sheet ID o URL
                </label>
                <input
                  type="text"
                  value={spreadsheetId}
                  onChange={(e) => handleSpreadsheetIdChange(e.target.value)}
                  placeholder="1abc123xyz o https://docs.google.com/spreadsheets/d/..."
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-4 focus:ring-purple-500/20 focus:border-purple-500 font-mono text-sm transition-all"
                  disabled={isProcessing}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Puedes pegar el ID o la URL completa del sheet
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Email para notificación
                </label>
                <input
                  type="email"
                  value={notifyEmail}
                  onChange={(e) => setNotifyEmail(e.target.value)}
                  placeholder="asistente@example.com"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-4 focus:ring-purple-500/20 focus:border-purple-500 transition-all"
                  disabled={isProcessing}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Recibirás un email cuando el procesamiento termine
                </p>
              </div>

              <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <input
                  type="checkbox"
                  id="createResultsSheet"
                  checked={createResultsSheet}
                  onChange={(e) => setCreateResultsSheet(e.target.checked)}
                  disabled={isProcessing}
                  className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="createResultsSheet" className="flex-1 cursor-pointer">
                  <span className="text-sm font-semibold text-blue-900 block mb-1">
                    📊 Usar Google Sheet de Resultados
                  </span>
                  <p className="text-xs text-blue-700">
                    Escribe los resultados en un Google Sheet separado para fácil revisión y análisis.
                    Crea el sheet manualmente y compártelo con la service account primero.
                  </p>
                </label>
              </div>

              {createResultsSheet && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <label className="block text-sm font-semibold text-amber-900 mb-2">
                    📋 Google Sheet ID de Resultados
                  </label>
                  <input
                    type="text"
                    value={resultsSheetId}
                    onChange={(e) => setResultsSheetId(e.target.value)}
                    placeholder="1abc123xyz o https://docs.google.com/spreadsheets/d/..."
                    className="w-full px-4 py-3 border-2 border-amber-300 rounded-lg focus:ring-4 focus:ring-amber-500/20 focus:border-amber-500 font-mono text-sm transition-all"
                    disabled={isProcessing}
                  />
                  <div className="mt-3 p-3 bg-white border border-amber-200 rounded-lg">
                    <p className="text-xs font-semibold text-amber-900 mb-2">⚠️ Pasos requeridos:</p>
                    <ol className="text-xs text-amber-800 space-y-1 list-decimal list-inside">
                      <li>Crea un Google Sheet nuevo con headers (ver documentación)</li>
                      <li>Comparte con: <code className="bg-amber-100 px-1 rounded text-[10px]">property-ingestion-service@smart-arc-466414-p9.iam.gserviceaccount.com</code></li>
                      <li>Dale permisos de <strong>Editor</strong></li>
                      <li>Copia el ID del sheet aquí</li>
                    </ol>
                  </div>
                </div>
              )}

              <button
                onClick={handleProcessSheet}
                disabled={isProcessing}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white py-3 px-6 rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all duration-200 font-bold flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                {isProcessing ? 'PROCESANDO...' : 'PROCESAR SHEET'}
              </button>
            </div>

            {/* Progress Bar - shown when processing */}
            {isProcessing && taskId && (
              <div className="mt-6">
                <ProgressBar progress={progressState} />
              </div>
            )}

            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h3 className="text-sm font-semibold text-yellow-900 mb-2">⚡ Qué sucede:</h3>
              <ul className="text-sm text-yellow-800 space-y-1 list-disc list-inside">
                <li>Lee todas las filas con "Pendiente"</li>
                <li>Procesa cada URL automáticamente</li>
                <li>Actualiza el status en tiempo real</li>
                <li>Envía email con resultados al terminar</li>
              </ul>
            </div>

            {spreadsheetId && (
              <div className="mt-4">
                <a
                  href={`https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-purple-700 hover:text-purple-800"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  Abrir este Sheet en Google
                </a>
              </div>
            )}

            {resultsSpreadsheet && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Google Sheet de Resultados Creado
                </h3>
                <div className="space-y-2">
                  <div>
                    <span className="text-xs font-medium text-green-700">Título:</span>
                    <p className="text-sm text-green-900 font-semibold">
                      {resultsSpreadsheet.title}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-green-700">Spreadsheet ID:</span>
                    <p className="text-sm font-mono text-green-900 bg-white px-2 py-1 rounded mt-1 break-all">
                      {resultsSpreadsheet.spreadsheet_id}
                    </p>
                  </div>
                  <a
                    href={resultsSpreadsheet.spreadsheet_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm font-semibold text-green-700 hover:text-green-800 mt-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    Ver Resultados en Google Sheets
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Instructions Section */}
        <div className="mt-8 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-8 border border-indigo-100">
          <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-3">
            <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            ¿Cómo funciona?
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg p-5 shadow-sm">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-3">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <h3 className="font-bold text-gray-800 mb-2">1. Crear Template</h3>
              <p className="text-sm text-gray-600">
                Crea un Google Sheet con las columnas ya configuradas. Solo necesitas el título.
              </p>
            </div>

            <div className="bg-white rounded-lg p-5 shadow-sm">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-3">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </div>
              <h3 className="font-bold text-gray-800 mb-2">2. Agregar URLs</h3>
              <p className="text-sm text-gray-600">
                Abre el sheet, pega URLs en columna A y escribe "Pendiente" en columna C.
              </p>
            </div>

            <div className="bg-white rounded-lg p-5 shadow-sm">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-3">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="font-bold text-gray-800 mb-2">3. Procesar</h3>
              <p className="text-sm text-gray-600">
                Pega el ID del sheet, tu email, y presiona procesar. Recibirás email cuando termine.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

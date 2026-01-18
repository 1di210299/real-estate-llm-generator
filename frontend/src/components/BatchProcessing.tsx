import { useState, useRef } from 'react'

interface BatchItem {
  id: string
  url: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  progress: number
  result?: any
  error?: string
}

export default function BatchProcessing() {
  const [urls, setUrls] = useState('')
  const [resultsSheetId, setResultsSheetId] = useState('')
  const [useResultsSheet, setUseResultsSheet] = useState(false)
  const [batchItems, setBatchItems] = useState<BatchItem[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentProcessingIndex, setCurrentProcessingIndex] = useState(-1)
  const [batchId, setBatchId] = useState('')
  const [selectedItem, setSelectedItem] = useState<BatchItem | null>(null)
  const [showModal, setShowModal] = useState(false)
  const shouldCancelRef = useRef(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  console.log('🔍 BatchProcessing - Estados actuales:')
  console.log('  - selectedItem:', selectedItem)
  console.log('  - showModal:', showModal)
  console.log('  - batchItems completados:', batchItems.filter(i => i.status === 'completed').length)

  const getApiBase = () => {
    if (import.meta.env.MODE === 'production') {
      return import.meta.env.VITE_API_URL || window.location.origin
    }
    return import.meta.env.VITE_API_URL || 'http://localhost:8000'
  }

  const API_BASE = getApiBase()

  const extractSpreadsheetId = (input: string) => {
    // Extract ID from URL or use as-is if it's already an ID
    const urlMatch = input.match(/\/d\/([a-zA-Z0-9-_]+)/)
    return urlMatch ? urlMatch[1] : input
  }

  const handleExportToGoogleSheets = async () => {
    if (!resultsSheetId.trim()) {
      alert('Por favor ingresa el link del Google Sheet')
      return
    }

    const completedItems = batchItems.filter(item => item.status === 'completed' && item.result)
    if (completedItems.length === 0) {
      alert('No hay resultados completados para exportar')
      return
    }

    try {
      const sheetId = extractSpreadsheetId(resultsSheetId)
      const response = await fetch(`${API_BASE}/ingest/batch-export/sheets/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sheet_id: sheetId,
          results: completedItems.map(item => item.result)
        })
      })

      if (!response.ok) throw new Error('Error al exportar a Google Sheets')

      alert(`✅ ${completedItems.length} propiedades exportadas exitosamente a Google Sheets`)
    } catch (error) {
      console.error('Export error:', error)
      alert('❌ Error al exportar a Google Sheets. Verifica que el sheet esté compartido correctamente.')
    }
  }

  const handleSaveToDatabase = async () => {
    const completedItems = batchItems.filter(item => item.status === 'completed' && item.result)
    if (completedItems.length === 0) {
      alert('No hay resultados completados para guardar')
      return
    }

    try {
      const response = await fetch(`${API_BASE}/ingest/batch-export/database/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          results: completedItems.map(item => item.result)
        })
      })

      if (!response.ok) throw new Error('Error al guardar en base de datos')

      alert(`✅ ${completedItems.length} propiedades guardadas exitosamente en la base de datos`)
    } catch (error) {
      console.error('Database save error:', error)
      alert('❌ Error al guardar en la base de datos')
    }
  }

  const handleDownloadExcel = () => {
    const completedItems = batchItems.filter(item => item.status === 'completed' && item.result)
    if (completedItems.length === 0) {
      alert('No hay resultados completados para descargar')
      return
    }

    try {
      // Convert results to CSV format (Excel compatible)
      const headers = ['URL', 'Precio USD', 'Ubicación', 'Tipo', 'Título', 'Descripción', 'Características']
      const rows = completedItems.map(item => {
        const r = item.result
        return [
          item.url,
          r.price_usd || 'N/A',
          r.location || 'N/A',
          r.property_type || 'N/A',
          r.title || 'N/A',
          (r.description || 'N/A').replace(/"/g, '""'), // Escape quotes
          (r.features || []).join('; ')
        ]
      })

      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n')

      // Create download link
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `propiedades_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      alert(`✅ ${completedItems.length} propiedades descargadas en formato CSV`)
    } catch (error) {
      console.error('Excel download error:', error)
      alert('❌ Error al descargar el archivo')
    }
  }

  const handleStartBatch = async () => {
    console.log('🚀 handleStartBatch called!')

    const urlList = urls
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0)

    console.log(`📋 Found ${urlList.length} URLs to process`)

    if (urlList.length === 0) {
      alert('Por favor ingresa al menos una URL')
      return
    }

    if (urlList.length > 50) {
      alert('Máximo 50 URLs por lote')
      return
    }

    // Removed Google Sheets validation - will be handled in export options after processing

    // Generate unique batch ID for cancellation tracking
    const newBatchId = `batch-${Date.now()}`
    setBatchId(newBatchId)

    const items: BatchItem[] = urlList.map((url, index) => ({
      id: `${newBatchId}-${index}`,
      url,
      status: 'pending',
      progress: 0
    }))

    console.log('✨ Created batch items:', items.length)
    console.log('🆔 Batch ID:', newBatchId)

    setBatchItems(items)
    setIsProcessing(true)
    setCurrentProcessingIndex(0)
    shouldCancelRef.current = false

    console.log('🔧 Starting sequential processing...')
    // Process URLs sequentially with real-time updates
    processSequentially(items, 0)
  }

  const processSequentially = async (items: BatchItem[], currentIndex: number) => {
    console.log(`🔄 Processing item ${currentIndex + 1}/${items.length}`)

    // Check if user requested to stop
    if (shouldCancelRef.current) {
      console.log('🛑 Process cancelled by user')
      setIsProcessing(false)
      setCurrentProcessingIndex(-1)
      shouldCancelRef.current = false
      return
    }

    if (currentIndex >= items.length) {
      console.log('✅ All items processed!')
      setIsProcessing(false)
      setCurrentProcessingIndex(-1)
      return
    }

    const currentItem = items[currentIndex]
    setCurrentProcessingIndex(currentIndex)

    console.log(`▶️ Starting: ${currentItem.url}`)

    // Update status to processing with initial progress
    setBatchItems(prev =>
      prev.map((item, idx) =>
        idx === currentIndex
          ? { ...item, status: 'processing', progress: 10 }
          : item
      )
    )

    // Simulate scraping phase (animate progress)
    console.log('⏳ Progress: 10% → 30%')
    await new Promise(resolve => setTimeout(resolve, 400))

    // Check for cancellation after delay
    if (shouldCancelRef.current) {
      console.log('🛑 Process cancelled during animation')
      setIsProcessing(false)
      setCurrentProcessingIndex(-1)
      shouldCancelRef.current = false
      return
    }

    setBatchItems(prev =>
      prev.map((item, idx) =>
        idx === currentIndex
          ? { ...item, progress: 30 }
          : item
      )
    )

    console.log('⏳ Progress: 30% → 50%')
    await new Promise(resolve => setTimeout(resolve, 300))

    // Check for cancellation after delay
    if (shouldCancelRef.current) {
      console.log('🛑 Process cancelled during animation')
      setIsProcessing(false)
      setCurrentProcessingIndex(-1)
      shouldCancelRef.current = false
      return
    }

    setBatchItems(prev =>
      prev.map((item, idx) =>
        idx === currentIndex
          ? { ...item, progress: 50 }
          : item
      )
    )

    try {
      console.log('📡 Calling API: /ingest/url/')

      // Create new AbortController for this request
      abortControllerRef.current = new AbortController()

      const response = await fetch(`${API_BASE}/ingest/url/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: currentItem.url,
          source_website: 'auto',
          use_websocket: false,
          batch_id: batchId
        }),
        signal: abortControllerRef.current.signal
      })

      // Update progress: processing data
      console.log('⏳ Progress: 50% → 80%')
      setBatchItems(prev =>
        prev.map((item, idx) =>
          idx === currentIndex
            ? { ...item, progress: 80 }
            : item
        )
      )

      await new Promise(resolve => setTimeout(resolve, 300))

      const data = await response.json()
      console.log('📦 Response received:', data)

      if (response.ok) {
        console.log('✅ Success! Progress: 80% → 100%')
        // Success - animate to completed
        setBatchItems(prev =>
          prev.map((item, idx) =>
            idx === currentIndex
              ? {
                ...item,
                status: 'completed',
                progress: 100,
                result: data.property
              }
              : item
          )
        )

        // Write to Google Sheets if enabled
        if (useResultsSheet && resultsSheetId.trim()) {
          try {
            const sheetId = extractSpreadsheetId(resultsSheetId.trim())
            await fetch(`${API_BASE}/ingest/batch/`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                urls: [currentItem.url],
                results_sheet_id: sheetId,
                async: false
              })
            })
          } catch (sheetError) {
            console.error('Error writing to Google Sheets:', sheetError)
          }
        }
      } else {
        console.log('❌ Error response from API')
        // Error - update status
        setBatchItems(prev =>
          prev.map((item, idx) =>
            idx === currentIndex
              ? {
                ...item,
                status: 'error',
                progress: 0,
                error: data.error || 'Error desconocido'
              }
              : item
          )
        )
      }
    } catch (error) {
      console.error('💥 Exception caught:', error)

      // Check if error is due to abort (user cancellation)
      if ((error as Error).name === 'AbortError') {
        console.log('🛑 Request aborted by user')
        // Don't mark as error, was intentional cancellation
        return
      }

      // Network or other error
      setBatchItems(prev =>
        prev.map((item, idx) =>
          idx === currentIndex
            ? {
              ...item,
              status: 'error',
              progress: 0,
              error: (error as Error).message || 'Error de conexión'
            }
            : item
        )
      )
    }

    // Wait before processing next item (so user can see the completion)
    console.log('⏸️  Waiting 600ms before next item...')
    await new Promise(resolve => setTimeout(resolve, 600))

    // Check again if user cancelled during the wait
    if (shouldCancelRef.current) {
      console.log('🛑 Process cancelled by user during wait')
      setIsProcessing(false)
      setCurrentProcessingIndex(-1)
      shouldCancelRef.current = false
      return
    }

    // Process next item
    console.log(`➡️  Moving to next item (${currentIndex + 2}/${items.length})`)
    processSequentially(items, currentIndex + 1)
  }

  const handleStopBatch = async () => {
    console.log('🛑 Stop button clicked')
    shouldCancelRef.current = true

    // Abort ongoing HTTP request
    if (abortControllerRef.current) {
      console.log('🚫 Aborting current HTTP request')
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }

    // Notify backend to cancel batch
    if (batchId) {
      try {
        console.log('📡 Notifying backend to cancel batch:', batchId)
        await fetch(`${API_BASE}/ingest/cancel-batch/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ batch_id: batchId })
        })
        console.log('✅ Backend notified of cancellation')
      } catch (error) {
        console.error('⚠️ Failed to notify backend:', error)
        // Continue with local cancellation even if backend notification fails
      }
    }

    // Mark current processing item as pending again
    setBatchItems(prev =>
      prev.map((item, idx) =>
        idx === currentProcessingIndex && item.status === 'processing'
          ? { ...item, status: 'pending', progress: 0 }
          : item
      )
    )
  }

  const handleClear = () => {
    setBatchItems([])
    setUrls('')
  }

  const getStatusIcon = (status: BatchItem['status']) => {
    switch (status) {
      case 'pending':
        return (
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'processing':
        return (
          <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )
      case 'completed':
        return (
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        )
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        )
    }
  }

  const completedCount = batchItems.filter(item => item.status === 'completed').length
  const errorCount = batchItems.filter(item => item.status === 'error').length
  const processingCount = batchItems.filter(item => item.status === 'processing').length

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
      <div className="max-w-[1800px] mx-auto px-4 py-6">
        {/* Header con gradiente */}
        <header className="mb-6 relative">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 to-blue-600/10 rounded-2xl blur-3xl"></div>
          <div className="relative bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-purple-100 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="bg-gradient-to-br from-purple-600 to-indigo-600 p-3 rounded-xl shadow-lg">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">Procesamiento en Lote</h1>
                  <p className="text-sm text-gray-600 mt-1 flex items-center gap-2">
                    <svg className="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Extrae datos de múltiples propiedades automáticamente
                  </p>
                </div>
              </div>
              {isProcessing && (
                <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl shadow-lg animate-pulse">
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <div>
                    <span className="font-bold block">Procesando...</span>
                    <span className="text-xs text-blue-100">{currentProcessingIndex + 1} de {batchItems.length}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-2">
          {/* Input Section */}
          <div className="lg:col-span-3">
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl border border-purple-100 p-5 sticky top-4">
              <div className="mb-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="bg-gradient-to-br from-purple-500 to-indigo-500 p-2 rounded-lg">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h2 className="text-lg font-bold text-gray-800">Lista de URLs</h2>
                </div>
                <div className="h-1 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full"></div>
              </div>

              <div className="mb-5">
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
                  <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  URLs de Propiedades
                </label>
                <div className="relative">
                  <textarea
                    value={urls}
                    onChange={(e) => setUrls(e.target.value)}
                    rows={Math.max(6, Math.min(20, urls.split('\n').length))}
                    placeholder="https://encuentra24.com/property/...&#10;https://brevitas.com/property/...&#10;https://coldwellbankercostarica.com/..."
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500/30 focus:border-purple-500 font-mono text-xs resize-none shadow-sm transition-all hover:border-gray-300 bg-gray-50/50"
                    disabled={isProcessing}
                  />
                  {urls.trim().length > 0 && (
                    <div className="absolute -bottom-2 right-2 px-3 py-1 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-xs font-bold rounded-full shadow-lg">
                      <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {urls.split('\n').filter(url => url.trim().length > 0).length} URLs
                    </div>
                  )}
                </div>
              </div>

              {/* Removed Google Sheets checkbox - will show after processing */}

              <div className="flex gap-3">
                {isProcessing ? (
                  <button
                    onClick={handleStopBatch}
                    className="flex-1 bg-gradient-to-r from-red-500 to-red-600 text-white py-4 px-4 rounded-xl hover:from-red-600 hover:to-red-700 transition-all duration-200 font-bold text-sm flex items-center justify-center gap-3 shadow-xl hover:shadow-2xl hover:scale-105 transform"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span>DETENER</span>
                  </button>
                ) : (
                  <button
                    onClick={handleStartBatch}
                    className="flex-1 bg-gradient-to-r from-purple-600 via-purple-600 to-indigo-600 text-white py-4 px-4 rounded-xl hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 font-bold text-sm flex items-center justify-center gap-3 shadow-xl hover:shadow-2xl hover:scale-105 transform"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span>PROCESAR</span>
                  </button>
                )}

                {batchItems.length > 0 && (
                  <button
                    onClick={handleClear}
                    disabled={isProcessing}
                    className="px-4 py-4 text-gray-600 hover:text-red-600 border-2 border-gray-200 rounded-xl hover:bg-red-50 hover:border-red-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
                    title="Limpiar todo"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Stats */}
              {batchItems.length > 0 && (
                <div className="mt-5 pt-5 border-t-2 border-gray-100">
                  <div className="flex items-center gap-2 mb-3">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <h3 className="text-sm font-bold text-gray-800">Estadísticas</h3>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-gradient-to-br from-gray-100 to-gray-50 px-3 py-2 rounded-lg border border-gray-200 shadow-sm">
                      <span className="text-xs text-gray-500 block">Total</span>
                      <span className="text-xl font-bold text-gray-800">{batchItems.length}</span>
                    </div>
                    {processingCount > 0 && (
                      <div className="bg-gradient-to-br from-blue-100 to-blue-50 px-3 py-2 rounded-lg border border-blue-200 shadow-sm">
                        <span className="text-xs text-blue-600 block">Procesando</span>
                        <span className="text-xl font-bold text-blue-700">{processingCount}</span>
                      </div>
                    )}
                    <div className="bg-gradient-to-br from-green-100 to-green-50 px-3 py-2 rounded-lg border border-green-200 shadow-sm">
                      <span className="text-xs text-green-600 block">Completadas</span>
                      <span className="text-xl font-bold text-green-700">{completedCount}</span>
                    </div>
                    {errorCount > 0 && (
                      <div className="bg-gradient-to-br from-red-100 to-red-50 px-3 py-2 rounded-lg border border-red-200 shadow-sm">
                        <span className="text-xs text-red-600 block">Errores</span>
                        <span className="text-xl font-bold text-red-700">{errorCount}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Export Options - Show when processing is complete */}
              {!isProcessing && completedCount > 0 && (
                <div className="mt-5 pt-5 border-t-2 border-gray-100">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="bg-gradient-to-br from-green-500 to-emerald-500 p-2 rounded-lg">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                    </div>
                    <h3 className="text-sm font-bold text-gray-800">Exportar Resultados</h3>
                  </div>

                  {/* Google Sheets Option */}
                  <div className="mb-3 p-4 bg-gradient-to-br from-blue-50 to-cyan-50 border-2 border-blue-200 rounded-xl hover:border-blue-300 hover:shadow-md transition-all">
                    <div className="flex items-start gap-3 mb-3">
                      <input
                        type="checkbox"
                        id="exportGoogleSheets"
                        checked={useResultsSheet}
                        onChange={(e) => setUseResultsSheet(e.target.checked)}
                        className="mt-1.5 w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                      />
                      <label htmlFor="exportGoogleSheets" className="flex-1 cursor-pointer">
                        <div className="flex items-center gap-2 mb-1">
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <span className="text-sm font-bold text-blue-900">Google Sheets</span>
                          <span className="px-2 py-0.5 bg-blue-600 text-white text-xs rounded-full font-bold">{completedCount}</span>
                        </div>
                        <p className="text-xs text-blue-700">
                          Exporta automáticamente a una hoja de cálculo en la nube
                        </p>
                      </label>
                    </div>
                    {useResultsSheet && (
                      <div className="mt-3 space-y-2 animate-slideDown">
                        <div className="relative">
                          <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                          </svg>
                          <input
                            type="text"
                            value={resultsSheetId}
                            onChange={(e) => setResultsSheetId(e.target.value)}
                            placeholder="https://docs.google.com/spreadsheets/d/..."
                            className="w-full pl-11 pr-4 py-3 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 text-xs"
                          />
                        </div>
                        <button
                          onClick={handleExportToGoogleSheets}
                          disabled={!resultsSheetId.trim()}
                          className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-bold transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                          Exportar Ahora
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Database Option */}
                  <div className="mb-3 p-4 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl hover:border-green-300 hover:shadow-md transition-all cursor-pointer">
                    <button
                      onClick={handleSaveToDatabase}
                      className="w-full text-left"
                    >
                      <div className="flex items-center gap-3 mb-1">
                        <div className="bg-green-600 p-2 rounded-lg">
                          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <span className="text-sm font-bold text-green-900 block">Base de Datos</span>
                          <p className="text-xs text-green-700">Guarda permanentemente en PostgreSQL</p>
                        </div>
                        <span className="px-3 py-1 bg-green-600 text-white text-xs rounded-full font-bold">{completedCount}</span>
                      </div>
                    </button>
                  </div>

                  {/* Excel Download Option */}
                  <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200 rounded-xl hover:border-purple-300 hover:shadow-md transition-all cursor-pointer">
                    <button
                      onClick={handleDownloadExcel}
                      className="w-full text-left"
                    >
                      <div className="flex items-center gap-3 mb-1">
                        <div className="bg-purple-600 p-2 rounded-lg">
                          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <span className="text-sm font-bold text-purple-900 block">Archivo CSV (Excel)</span>
                          <p className="text-xs text-purple-700">Descarga un archivo .csv local</p>
                        </div>
                        <span className="px-3 py-1 bg-purple-600 text-white text-xs rounded-full font-bold">{completedCount}</span>
                      </div>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-9">
            {batchItems.length === 0 ? (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-purple-100 p-16 text-center">
                <div className="relative inline-block mb-6">
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full blur-2xl opacity-20 animate-pulse"></div>
                  <svg className="relative w-32 h-32 text-purple-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-gray-700 mb-3">Listo para procesar</h3>
                <p className="text-gray-500 mb-6 max-w-md mx-auto">Pega las URLs de las propiedades en el panel izquierdo y presiona <span className="font-bold text-purple-600">PROCESAR</span> para comenzar</p>
                <div className="flex items-center justify-center gap-8 text-sm text-gray-400">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Automático</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span>Rápido</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Preciso</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl border border-purple-100 overflow-hidden">
                <div className="p-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
                  <div className="flex items-center gap-3">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                    <h2 className="text-lg font-bold">Resultados del Procesamiento</h2>
                    <div className="ml-auto flex items-center gap-2">
                      <span className="px-3 py-1 bg-white/20 rounded-full text-sm font-bold">{batchItems.length} total</span>
                    </div>
                  </div>
                </div>
                <div className="divide-y divide-gray-200 max-h-[70vh] overflow-y-auto">
                  {batchItems.map((item, index) => (
                    <div
                      key={item.id}
                      className={`p-1.5 transition-all duration-300 ${index === currentProcessingIndex ? 'bg-blue-50 border-l-4 border-blue-500 shadow-md' : 'hover:bg-gray-50'
                        }`}
                    >
                      <div className="flex items-start gap-2">
                        <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center font-bold text-[10px] transition-all ${item.status === 'completed' ? 'bg-green-100 text-green-700' :
                          item.status === 'error' ? 'bg-red-100 text-red-700' :
                            item.status === 'processing' ? 'bg-blue-100 text-blue-700 border-2 border-blue-400' :
                              'bg-gray-200 text-gray-600'
                          }`}>
                          {index + 1}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            {getStatusIcon(item.status)}
                            <span className={`text-xs font-bold uppercase tracking-wide ${item.status === 'completed' ? 'text-green-600' :
                              item.status === 'error' ? 'text-red-600' :
                                item.status === 'processing' ? 'text-blue-600' :
                                  'text-gray-500'
                              }`}>
                              {item.status === 'pending' ? 'Pendiente' :
                                item.status === 'processing' ? 'Procesando' :
                                  item.status === 'completed' ? 'Completado' :
                                    'Error'}
                            </span>
                            {item.status === 'processing' && (
                              <span className="text-sm text-blue-600 font-bold ml-auto bg-blue-100 px-2 py-0.5 rounded">
                                {item.progress}%
                              </span>
                            )}
                          </div>

                          <p className="text-[10px] text-gray-600 break-all mb-1 font-mono">
                            {item.url}
                          </p>

                          {item.status === 'processing' && (
                            <div className="mt-1">
                              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden shadow-inner">
                                <div
                                  className="bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 h-2 rounded-full transition-all duration-500 ease-out flex items-center justify-center"
                                  style={{ width: `${item.progress}%` }}
                                >
                                  {item.progress >= 30 && (
                                    <span className="text-[8px] text-white font-bold">{item.progress}%</span>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-1.5 mt-1">
                                <div className="flex-shrink-0 w-3 h-3">
                                  <svg className="w-3 h-3 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                  </svg>
                                </div>
                                <p className="text-xs text-blue-700 font-semibold">
                                  {item.progress < 30 ? 'Iniciando proceso...' :
                                    item.progress < 50 ? 'Scrapeando página...' :
                                      item.progress < 80 ? 'Extrayendo datos...' :
                                        'Finalizando...'}
                                </p>
                              </div>
                            </div>
                          )}

                          {item.status === 'completed' && item.result && (
                            <div
                              onClick={(_e) => {
                                console.log('🖱️ Click en resultado completado!')
                                console.log('📦 Item:', item)
                                console.log('📊 Result:', item.result)
                                console.log('🎯 Setting selectedItem...')
                                setSelectedItem(item)
                                console.log('👁️ Setting showModal to true...')
                                setShowModal(true)
                                console.log('✅ Estados actualizados!')
                              }}
                              className="mt-2 p-3 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border-2 border-green-200 cursor-pointer hover:border-green-400 hover:shadow-md transition-all"
                            >
                              <div className="grid grid-cols-2 gap-3 text-sm">
                                <div className="flex items-start gap-2">
                                  <svg className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                                  </svg>
                                  <div className="flex-1 min-w-0">
                                    <span className="text-xs text-gray-600 font-medium block mb-0.5">Nombre</span>
                                    <p className="font-bold text-gray-900 truncate">{item.result.title || item.result.property_name || 'N/A'}</p>
                                  </div>
                                </div>
                                <div className="flex items-start gap-2">
                                  <svg className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                  <div className="flex-1">
                                    <span className="text-xs text-gray-600 font-medium block mb-0.5">Precio</span>
                                    <p className="font-bold text-green-700">${item.result.price_usd?.toLocaleString() || 'N/A'}</p>
                                  </div>
                                </div>
                                <div className="flex items-start gap-2">
                                  <svg className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                  </svg>
                                  <div className="flex-1 min-w-0">
                                    <span className="text-xs text-gray-600 font-medium block mb-0.5">Ubicación</span>
                                    <p className="font-bold text-gray-900 truncate">{item.result.location || 'N/A'}</p>
                                  </div>
                                </div>
                                <div className="flex items-start gap-2">
                                  <svg className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                  </svg>
                                  <div className="flex-1">
                                    <span className="text-xs text-gray-600 font-medium block mb-0.5">Tipo</span>
                                    <p className="font-bold text-gray-900">{item.result.property_type || 'N/A'}</p>
                                  </div>
                                </div>
                              </div>
                              <div className="mt-3 pt-3 border-t border-green-200 text-center">
                                <span className="text-xs text-green-700 font-semibold flex items-center justify-center gap-1">
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                  </svg>
                                  Click para ver todos los detalles
                                </span>
                              </div>
                            </div>
                          )}

                          {item.status === 'error' && item.error && (
                            <div className="mt-1 p-1.5 bg-red-50 rounded border border-red-200">
                              <p className="text-[10px] text-red-700">{item.error}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal Detalles */}
      {showModal && selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden transform transition-all animate-slideUp" onClick={(e) => e.stopPropagation()}>

            {/* Header con gradiente */}
            <div className="bg-gradient-to-r from-purple-600 via-purple-500 to-indigo-600 text-white p-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <div>
                  <h2 className="text-2xl font-bold">Detalles de Propiedad</h2>
                  <p className="text-purple-100 text-sm mt-0.5">Información completa extraída</p>
                </div>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="w-10 h-10 rounded-full hover:bg-white/20 transition-colors flex items-center justify-center group"
              >
                <svg className="w-6 h-6 group-hover:rotate-90 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Contenido */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)] bg-gradient-to-br from-gray-50 to-white">

              {/* URL de origen */}
              <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <div className="flex-1">
                    <p className="text-xs font-semibold text-blue-900 mb-1">URL DE ORIGEN</p>
                    <a
                      href={selectedItem.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800 hover:underline break-all font-medium flex items-center gap-1"
                    >
                      {selectedItem.url}
                      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                </div>
              </div>

              {/* Datos principales con iconos */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {(() => {
                  const result = selectedItem.result || {}
                  const iconMap: Record<string, string> = {
                    title: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
                    price_usd: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
                    location: 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z',
                    property_type: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
                    bedrooms: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
                    bathrooms: 'M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z',
                    lot_size_m2: 'M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4',
                    square_meters: 'M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4',
                    description: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
                    amenities: 'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z'
                  }

                  const getIcon = (key: string) => {
                    const path = iconMap[key] || 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
                    return (
                      <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={path} />
                      </svg>
                    )
                  }

                  const formatValue = (key: string, value: any) => {
                    if (key === 'price_usd' && typeof value === 'string') {
                      return `$${parseFloat(value).toLocaleString('en-US')}`
                    }
                    if (Array.isArray(value)) {
                      return value.join(', ')
                    }
                    return String(value)
                  }

                  const getColorClass = (key: string) => {
                    if (key === 'price_usd') return 'from-green-50 to-emerald-50 border-green-200'
                    if (key === 'title') return 'from-purple-50 to-indigo-50 border-purple-200'
                    if (key === 'location') return 'from-blue-50 to-cyan-50 border-blue-200'
                    if (key === 'property_type') return 'from-orange-50 to-amber-50 border-orange-200'
                    return 'from-gray-50 to-slate-50 border-gray-200'
                  }

                  return Object.entries(result)
                    .filter(([k, v]) => v && k !== 'user_roles' && k !== 'tenant_id' && k !== 'source_website')
                    .map(([key, value]) => (
                      <div
                        key={key}
                        className={`p-4 bg-gradient-to-br ${getColorClass(key)} border rounded-xl hover:shadow-md transition-all group`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="text-gray-600 group-hover:text-purple-600 transition-colors mt-0.5">
                            {getIcon(key)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">
                              {key.replace(/_/g, ' ')}
                            </h4>
                            <p className={`text-sm font-medium text-gray-800 ${key === 'description' ? 'line-clamp-3' : ''}`}>
                              {formatValue(key, value)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                })()}
              </div>

              {/* JSON completo expandible */}
              <details className="group">
                <summary className="cursor-pointer p-4 bg-gradient-to-r from-gray-800 to-gray-700 text-white rounded-xl hover:from-gray-700 hover:to-gray-600 transition-all flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <svg className="w-5 h-5 group-open:rotate-90 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                    </svg>
                    <span className="font-semibold">Ver JSON Completo</span>
                  </div>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                </summary>
                <div className="mt-3 p-4 bg-gray-900 rounded-xl border border-gray-700 overflow-x-auto">
                  <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">
                    {JSON.stringify(selectedItem.result, null, 2)}
                  </pre>
                </div>
              </details>
            </div>

            {/* Footer con acciones */}
            <div className="bg-gray-50 border-t border-gray-200 p-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Datos extraídos automáticamente</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(selectedItem.result, null, 2))
                    const btn = document.activeElement as HTMLButtonElement
                    const original = btn.innerHTML
                    btn.innerHTML = '✓ Copiado'
                    setTimeout(() => btn.innerHTML = original, 2000)
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copiar JSON
                </button>
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import './DataCollector.css'
import { ProgressBar } from './ProgressBar'
import { useProgressWebSocket } from '../hooks/useProgressWebSocket'
import { useLanguage } from '../contexts/LanguageContext'
import TutorialOverlay from './Tutorial/TutorialOverlay'

interface PropertyData {
  id?: string
  property_name?: string
  listing_id?: string
  listing_status?: string
  price_usd?: number
  property_type?: string
  property_type_display?: string
  location?: string
  latitude?: number
  longitude?: number
  bedrooms?: number
  bathrooms?: number
  square_meters?: number
  lot_size_m2?: number
  date_listed?: string
  status?: string
  status_display?: string
  description?: string
  source_url?: string
  source_website?: string
  created_at?: string
  extraction_confidence?: number
  [key: string]: any
}

interface RecentProperty {
  id: string
  title: string
  location: string
  price_usd: number | null
  bedrooms: number | null
  bathrooms: number | null
  source_website: string
  created_at: string
}

interface CategoryConfig {
  name: string
  icon: string
  color: string
}

interface WebsiteConfig {
  id: string
  name: string
  url: string | null
  color: string
  active: boolean
  has_extractor: boolean
}

interface ContentType {
  key: string
  label: string
  icon: string
  description: string
}

function App() {
  const { t } = useLanguage();
  const [inputType, setInputType] = useState<'url' | 'text'>('url')
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [extractedProperty, setExtractedProperty] = useState<PropertyData | null>(null)
  const [error, setError] = useState('')
  const [showResults, setShowResults] = useState(false)
  const [properties, setProperties] = useState<PropertyData[]>([])
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const [confidence, setConfidence] = useState(0)
  const [supportedWebsites, setSupportedWebsites] = useState<WebsiteConfig[]>([])
  const [websitesLoading, setWebsitesLoading] = useState(true)
  const [contentTypes, setContentTypes] = useState<ContentType[]>([])
  const [selectedContentType, setSelectedContentType] = useState('real_estate')
  const [propertiesProcessedToday, setPropertiesProcessedToday] = useState<number>(0)
  const [recentProperties, setRecentProperties] = useState<RecentProperty[]>([])
  const [tutorialStep, setTutorialStep] = useState<number | null>(null)
  const [showTutorialButton, setShowTutorialButton] = useState(true)
  const [highlightPositions, setHighlightPositions] = useState<{
    urlInput?: DOMRect;
    processButton?: DOMRect;
  }>({})

  // WebSocket progress tracking
  const { progress, isConnected, connect, disconnect: _disconnect, reset } = useProgressWebSocket({
    onComplete: (data) => {
      console.log('✅ Backend response:', data);
      if (data && data.property) {
        console.log('📦 Property data keys:', Object.keys(data.property));
        console.log('📦 Full property data:', data.property);
        
        // Include content_type and page_type info in the property
        const propertyWithContentType = {
          ...data.property,
          content_type: data.content_type,
          content_type_confidence: data.content_type_confidence,
          content_type_detection_method: data.content_type_detection_method,
          page_type: data.page_type,
          page_type_confidence: data.page_type_confidence,
          page_type_detection_method: data.page_type_detection_method
        };
        
        console.log('🎯 Final property with types:', propertyWithContentType);
        setExtractedProperty(propertyWithContentType);
        setConfidence(data.extraction_confidence || 0.9);
        setShowResults(true);
        // Reload stats after successful processing
        loadIngestionStats();
      }
      setLoading(false);
    },
    onError: (errorMsg) => {
      console.error('❌ WebSocket error:', errorMsg);
      setError(errorMsg);
      setLoading(false);
    },
  });

  // API Base URL configuration
  const getApiBase = () => {
    let baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    
    console.log('🔧 [API CONFIG] Raw VITE_API_URL:', import.meta.env.VITE_API_URL)
    console.log('🔧 [API CONFIG] Initial baseUrl:', baseUrl)
    
    // Remover trailing slash si existe
    if (baseUrl.endsWith('/')) {
      baseUrl = baseUrl.slice(0, -1)
    }
    
    // Remover /api si ya viene incluido en VITE_API_URL (DigitalOcean lo agrega automáticamente)
    if (baseUrl.endsWith('/api')) {
      baseUrl = baseUrl.slice(0, -4)
      console.log('🔧 [API CONFIG] Removed /api suffix, new baseUrl:', baseUrl)
    }
    
    console.log('✅ [API CONFIG] Final API_BASE:', baseUrl)
    return baseUrl
  }

  const API_BASE = getApiBase()
  console.log('🌐 [API CONFIG] API_BASE será usado en todas las requests:', API_BASE)

  const CATEGORIES: Record<string, CategoryConfig> = {
    'nuevos-proyectos': {
      name: 'Proyectos Nuevos',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4zm7 5a1 1 0 00-2 0v1H8a1 1 0 000 2h1v1a1 1 0 002 0v-1h1a1 1 0 000-2h-1V9z" clip-rule="evenodd"></path></svg>',
      color: '#8b5cf6'
    },
    'venta-casas': {
      name: 'Casas en Venta',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path></svg>',
      color: '#10b981'
    },
    'venta-apartamentos': {
      name: 'Apartamentos en Venta',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z" clip-rule="evenodd"></path></svg>',
      color: '#3b82f6'
    },
    'venta-negocios': {
      name: 'Negocios en Venta',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clip-rule="evenodd"></path><path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z"></path></svg>',
      color: '#f59e0b'
    },
    'venta-lotes': {
      name: 'Lotes/Terrenos',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path></svg>',
      color: '#059669'
    },
    'venta-fincas': {
      name: 'Fincas en Venta',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 3.5a1.5 1.5 0 013 0V4a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-.5a1.5 1.5 0 000 3h.5a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-.5a1.5 1.5 0 00-3 0v.5a1 1 0 01-1 1H6a1 1 0 01-1-1v-3a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H4a1 1 0 001-1V6a1 1 0 011-1h3a1 1 0 001-1v-.5z"></path></svg>',
      color: '#84cc16'
    },
    'alquiler-casas': {
      name: 'Casas en Alquiler',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z"></path><path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707l-2-2A1 1 0 0015 7h-1z"></path></svg>',
      color: '#06b6d4'
    },
    'alquiler-apartamentos': {
      name: 'Apartamentos en Alquiler',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M11 17a1 1 0 001.447.894l4-2A1 1 0 0017 15V9.236a1 1 0 00-1.447-.894l-4 2a1 1 0 00-.553.894V17zM15.211 6.276a1 1 0 000-1.788l-4.764-2.382a1 1 0 00-.894 0L4.789 4.488a1 1 0 000 1.788l4.764 2.382a1 1 0 00.894 0l4.764-2.382zM4.447 8.342A1 1 0 003 9.236V15a1 1 0 00.553.894l4 2A1 1 0 009 17v-5.764a1 1 0 00-.553-.894l-4-2z"></path></svg>',
      color: '#0ea5e9'
    },
    'alquiler-locales': {
      name: 'Locales Comerciales',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M13 7H7v6h6V7z"></path><path fill-rule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clip-rule="evenodd"></path></svg>',
      color: '#8b5cf6'
    },
    other: {
      name: 'Otros',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path></svg>',
      color: '#6b7280'
    }
  }

  useEffect(() => {
    loadSupportedWebsites()
    loadHistoryFromBackend()
    loadIngestionStats()
    loadContentTypes()
  }, [])
  
  const loadContentTypes = async () => {
    try {
      const url = `${API_BASE}/ingest/content-types/`
      console.log('📥 [FETCH] Loading content types from:', url)
      const response = await fetch(url)
      const data = await response.json()
      if (data.status === 'success') {
        setContentTypes(data.content_types)
        console.log('✅ Content types loaded:', data.content_types.length)
      }
    } catch (error) {
      console.error('Error loading content types:', error)
    }
  }

  const loadIngestionStats = async () => {
    try {
      const url = `${API_BASE}/ingest/stats/`
      console.log('📥 [FETCH] Loading ingestion stats from:', url)
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      console.log('📥 [FETCH] Stats received:', data)
      setPropertiesProcessedToday(data.properties_today || 0)
      setRecentProperties(data.recent_properties || [])
    } catch (error) {
      console.error('Error loading ingestion stats:', error)
    }
  }

  const startTutorial = () => {
    setTutorialStep(1)
    setShowTutorialButton(false)
    // Calculate positions after state updates
    setTimeout(calculateHighlightPositions, 100)
  }

  const nextTutorialStep = () => {
    if (tutorialStep !== null && tutorialStep < 3) {
      setTutorialStep(tutorialStep + 1)
      setTimeout(calculateHighlightPositions, 100)
    } else {
      setTutorialStep(null)
      setShowTutorialButton(true)
    }
  }

  const skipTutorial = () => {
    setTutorialStep(null)
    setShowTutorialButton(true)
  }

  const calculateHighlightPositions = () => {
    const urlInput = document.getElementById('propertyUrlInput')
    const processButton = document.getElementById('processPropertyButton')
    
    const positions: any = {}
    
    if (urlInput) {
      positions.urlInput = urlInput.getBoundingClientRect()
    }
    if (processButton) {
      positions.processButton = processButton.getBoundingClientRect()
    }
    
    setHighlightPositions(positions)
  }
  
  const loadSupportedWebsites = async () => {
    try {
      const url = `${API_BASE}/ingest/supported-websites/`
      console.log('📥 [FETCH] Loading supported websites from:', url)
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      console.log('📥 [FETCH] Supported websites:', data.websites)
      setSupportedWebsites(data.websites)
      setWebsitesLoading(false)
    } catch (error) {
      console.error('Error loading supported websites:', error)
      setWebsitesLoading(false)
    }
  }

  const getCategoryFromUrl = (url: string): string => {
    if (!url) return 'other'
    const urlLower = url.toLowerCase()
    
    if (urlLower.includes('proyectos-nuevos')) return 'proyectos-nuevos'
    if (urlLower.includes('venta-de-propiedades-casas') || urlLower.includes('venta-casas')) return 'venta-casas'
    if (urlLower.includes('venta-de-propiedades-apartamentos') || urlLower.includes('venta-apartamentos')) return 'venta-apartamentos'
    if (urlLower.includes('venta-de-propiedades-negocios')) return 'venta-negocios'
    if (urlLower.includes('venta-de-propiedades-lotes-y-terrenos') || urlLower.includes('lotes')) return 'venta-lotes'
    if (urlLower.includes('venta-de-propiedades-fincas')) return 'venta-fincas'
    if (urlLower.includes('alquiler-casas')) return 'alquiler-casas'
    if (urlLower.includes('alquiler-apartamentos')) return 'alquiler-apartamentos'
    if (urlLower.includes('alquiler-locales-comerciales')) return 'alquiler-locales'
    
    if (urlLower.includes('coldwellbanker')) {
      if (urlLower.includes('house-for-sale') || urlLower.includes('casa-en-venta')) return 'venta-casas'
      if (urlLower.includes('apartment-for-sale') || urlLower.includes('apartamento-en-venta')) return 'venta-apartamentos'
      if (urlLower.includes('land-for-sale') || urlLower.includes('terreno-en-venta') || urlLower.includes('lote-en-venta')) return 'venta-lotes'
      if (urlLower.includes('farm-for-sale') || urlLower.includes('finca-en-venta')) return 'venta-fincas'
      if (urlLower.includes('commercial-for-sale') || urlLower.includes('comercial-en-venta')) return 'venta-negocios'
      if (urlLower.includes('house-for-rent') || urlLower.includes('casa-alquiler')) return 'alquiler-casas'
      if (urlLower.includes('apartment-for-rent') || urlLower.includes('apartamento-alquiler')) return 'alquiler-apartamentos'
      if (urlLower.includes('commercial-for-rent') || urlLower.includes('local-alquiler')) return 'alquiler-locales'
      return 'venta-casas'
    }
    
    return 'other'
  }



  const toggleWebsiteGroup = (category: string) => {
    setCollapsedGroups(prev => {
      const newSet = new Set(prev)
      if (newSet.has(category)) {
        newSet.delete(category)
      } else {
        newSet.add(category)
      }
      return newSet
    })
  }

  const loadHistoryFromBackend = async () => {
    try {
      const url = `${API_BASE}/properties/?page_size=100&ordering=-created_at`
      console.log('📥 [FETCH] Loading history from:', url)
      const response = await fetch(url)
      console.log('📥 [FETCH] Response status:', response.status, response.ok ? '✅' : '❌')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      console.log('📥 [FETCH] Data received:', data.results?.length || 0, 'properties')
      if (data.results) {
        setProperties(data.results)
      }
    } catch (error) {
      console.error('Error loading history:', error)
    }
  }

  const loadPropertyFromHistory = async (propertyId: string) => {
    try {
      const response = await fetch(`${API_BASE}/properties/${propertyId}/`)
      const property = await response.json()
      setExtractedProperty(property)
      setConfidence(property.extraction_confidence || 0.9)
      setShowResults(true)
      setTimeout(() => {
        document.getElementById('resultsSection')?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
    } catch (error) {
      alert('Error loading property: ' + (error as Error).message)
    }
  }

  const clearHistory = async () => {
    if (!confirm('Are you sure you want to delete all saved properties?')) {
      return
    }
    try {
      const response = await fetch(`${API_BASE}/properties/?page_size=100`)
      const data = await response.json()
      for (const prop of data.results) {
        await fetch(`${API_BASE}/properties/${prop.id}/`, { method: 'DELETE' })
      }
      alert('History cleared successfully')
      loadHistoryFromBackend()
    } catch (error) {
      alert('Error clearing history: ' + (error as Error).message)
    }
  }

  const processProperty = async () => {
    if (inputType === 'url' && !url) {
      alert('Please enter a URL')
      return
    }
    if (inputType === 'text' && !text) {
      alert('Please enter text')
      return
    }

    setLoading(true)
    setShowResults(false)
    setError('')
    reset()

    try {
      // Primero iniciar el job en el backend y obtener task_id
      const endpoint = inputType === 'url' ? `${API_BASE}/ingest/url/` : `${API_BASE}/ingest/text/`
      console.log('📤 [FETCH] Starting processing job:', endpoint)
      const body = inputType === 'url' 
        ? { url, content_type: selectedContentType, use_websocket: true }
        : { text, content_type: selectedContentType, use_websocket: true }
      console.log('📤 [FETCH] Request body:', body)

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (response.ok) {
        if (data.task_id) {
          // Conectar al WebSocket con el task_id
          console.log('🔌 Connecting to WebSocket with task_id:', data.task_id);
          connect(data.task_id);
        } else if (data.property) {
          // Fallback: respuesta inmediata sin WebSocket
          console.log('⚠️  No task_id, using immediate response');
          const propertyWithContentType = {
            ...data.property,
            content_type: data.content_type,
            content_type_confidence: data.content_type_confidence,
            content_type_detection_method: data.content_type_detection_method,
            page_type: data.page_type,
            page_type_confidence: data.page_type_confidence,
            page_type_detection_method: data.page_type_detection_method
          };
          setExtractedProperty(propertyWithContentType);
          setConfidence(data.extraction_confidence || 0.9);
          setShowResults(true);
          setLoading(false);
        }
        setError('')
      } else {
        setError(data.error || 'Failed to process property')
        setLoading(false)
      }
    } catch (error) {
      setError('Network error: ' + (error as Error).message)
      setLoading(false)
    }
  }

  const viewFullDetails = async () => {
    if (!extractedProperty) {
      alert('No property data to save')
      return
    }
    
    try {
      const response = await fetch(`${API_BASE}/ingest/save/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_data: extractedProperty
        })
      })

      const data = await response.json()
      
      console.log('Save response status:', response.status)
      console.log('Save response data:', data)
      
      if (response.status === 409) {
        // Duplicate property
        alert(`⚠️ Duplicate Property Detected\n\nThis property already exists in the database:\n\nName: ${data.property_name || 'Unknown'}\nID: ${data.property_id}\n\nThe property was NOT saved again.`)
        return
      }
      
      if (response.ok && data.status === 'success') {
        alert(`✓ Property saved successfully!\n\nProperty ID: ${data.property_id}\nName: ${data.property.property_name}`)
        loadHistoryFromBackend()
        resetForm()
      } else {
        console.error('Save error details:', data)
        alert(`Error saving property: ${data.message || data.error || 'Unknown error'}`)
      }
    } catch (error) {
      alert(`Network error: ${(error as Error).message}`)
    }
  }

  const resetForm = () => {
    setUrl('')
    setText('')
    setShowResults(false)
    setExtractedProperty(null)
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const groupedByCategory: Record<string, PropertyData[]> = {}
  properties.forEach(prop => {
    const category = getCategoryFromUrl(prop.source_url || '')
    if (!groupedByCategory[category]) {
      groupedByCategory[category] = []
    }
    groupedByCategory[category].push(prop)
  })

  const categoryPriority = [
    'proyectos-nuevos', 'venta-casas', 'venta-apartamentos', 
    'venta-negocios', 'venta-lotes', 'venta-fincas',
    'alquiler-casas', 'alquiler-apartamentos', 'alquiler-locales',
    'other'
  ]

  const sortedCategories = Object.keys(groupedByCategory).sort((a, b) => 
    categoryPriority.indexOf(a) - categoryPriority.indexOf(b)
  )

  return (
    <div className="bg-gray-50 flex h-screen overflow-hidden">
      {/* Left Sidebar - Permanent */}
      <div className="w-80 bg-white shadow-xl flex flex-col h-full flex-shrink-0">
        <div className="p-4 border-b">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path>
            </svg>
            Saved Properties
          </h2>
          <p className="text-xs text-gray-500 mt-1">Organized by category</p>
        </div>
        <div className="flex-1 overflow-y-auto sidebar-scrollbar p-4">
          {properties.length === 0 ? (
            <div className="text-center py-8">
              <svg className="w-16 h-16 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <p className="text-gray-500 text-sm">No properties saved yet</p>
              <p className="text-gray-400 text-xs mt-1">Start by processing a property URL</p>
            </div>
          ) : (
            sortedCategories.map(category => {
              const props = groupedByCategory[category]
              const config = CATEGORIES[category] || CATEGORIES.other
              const isCollapsed = collapsedGroups.has(category)
              
              return (
                <div key={category} className="website-group">
                  <div className="website-header" onClick={() => toggleWebsiteGroup(category)}>
                    <div style={{ color: config.color }} dangerouslySetInnerHTML={{ __html: config.icon }} />
                    <span className="font-semibold text-gray-800 text-sm">{config.name}</span>
                    <span className="property-count">({props.length})</span>
                    <svg className="w-4 h-4 text-gray-500 transform transition-transform" style={{ marginLeft: '4px', transform: isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)' }}>
                      <path fill="currentColor" d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
                    </svg>
                  </div>
                  {!isCollapsed && (
                    <div className="property-list space-y-2">
                      {props.map(prop => (
                        <div 
                          key={prop.id}
                          className="ml-4 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition cursor-pointer border-l-2" 
                          style={{ borderColor: config.color }}
                          onClick={() => loadPropertyFromHistory(prop.id!)}
                        >
                          <div className="flex justify-between items-start mb-1">
                            <h3 className="font-semibold text-xs text-gray-800 truncate flex-1" title={prop.property_name || 'Untitled'}>
                              {(prop.property_name || 'Untitled').substring(0, 40)}{(prop.property_name || '').length > 40 ? '...' : ''}
                            </h3>
                            <span className="text-xs text-gray-400 ml-2" style={{ fontSize: '0.65rem' }}>
                              {new Date(prop.created_at!).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mb-1 truncate">{prop.location || 'N/A'}</p>
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-bold" style={{ color: config.color }}>
                              ${prop.price_usd ? parseFloat(String(prop.price_usd)).toLocaleString() : 'N/A'}
                            </span>
                            <span className="text-xs px-2 py-0.5 bg-white rounded" style={{ fontSize: '0.65rem' }}>
                              {prop.property_type || 'N/A'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
        <div className="p-4 border-t space-y-2">
          <button onClick={loadHistoryFromBackend} className="w-full bg-blue-100 text-blue-700 py-2 px-4 rounded hover:bg-blue-200 transition text-sm flex items-center justify-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Refresh
          </button>
          <button onClick={clearHistory} className="w-full bg-red-100 text-red-700 py-2 px-4 rounded hover:bg-red-200 transition text-sm">
            Clear All History
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <div className="w-full px-8 py-8 pb-16 min-h-full">
          {/* Header */}
          <header className="mb-8">
            <div className="flex items-center justify-between">
              <div id="headerTitle">
                <h1 className="text-3xl font-bold text-gray-800 mb-2">Property Data Collector</h1>
                <p className="text-gray-600">Paste a property URL or text to automatically extract structured data</p>
              </div>
              <div className="flex items-center gap-4">
                {/* Properties Processed Today Counter */}
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 border-2 border-blue-200 rounded-lg px-6 py-3 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className="bg-blue-500 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold text-lg">
                      {propertiesProcessedToday}
                    </div>
                    <div>
                      <div className="text-xs text-blue-600 font-medium uppercase tracking-wide">
                        {t.dataCollector.propertiesProcessedToday}
                      </div>
                      <div className="text-lg font-bold text-blue-900">
                        {propertiesProcessedToday}
                      </div>
                    </div>
                  </div>
                </div>
                
                {showResults && (
                  <button onClick={resetForm} className="bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-4 rounded-lg transition flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                    </svg>
                    Back to Search
                  </button>
                )}
              </div>
            </div>
          </header>

          {/* Instructions Section - Interactive Tutorial Button */}
          {!showResults && !loading && showTutorialButton && (
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg shadow-lg p-4 mb-4 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="bg-white/20 rounded-full p-2">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">¿Primera vez usando el colector?</h3>
                    <p className="text-sm text-blue-100">Sigue el tutorial interactivo paso a paso</p>
                  </div>
                </div>
                <button
                  onClick={startTutorial}
                  className="bg-white text-blue-600 px-6 py-3 rounded-lg font-bold hover:bg-blue-50 transition-all transform hover:scale-105 shadow-lg"
                >
                  🎯 Iniciar Tutorial
                </button>
              </div>
            </div>
          )}

          {/* Interactive Tutorial Overlay */}
          <TutorialOverlay
            tutorialStep={tutorialStep}
            highlightPositions={highlightPositions}
            onNext={nextTutorialStep}
            onSkip={skipTutorial}
          />

          {/* Recent Properties Section */}
          {recentProperties.length > 0 && !showResults && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                {t.dataCollector.recentProperties || 'Últimas Propiedades Agregadas'}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {recentProperties.map((prop) => {
                  const timeAgo = new Date(prop.created_at).toLocaleString('es-ES', {
                    day: '2-digit',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit'
                  });
                  
                  return (
                    <div 
                      key={prop.id} 
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow bg-white"
                    >
                      <div className="flex flex-col gap-3">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-800 truncate mb-2" title={prop.title}>
                            {prop.title}
                          </h3>
                          <div className="flex items-center gap-4 text-sm mb-2">
                            <p className="text-gray-600 flex items-center gap-1">
                              📍 {prop.location}
                            </p>
                            <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                              {prop.source_website}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            {prop.bedrooms && (
                              <span className="flex items-center gap-1">
                                🛏️ {prop.bedrooms}
                              </span>
                            )}
                            {prop.bathrooms && (
                              <span className="flex items-center gap-1">
                                🚿 {prop.bathrooms}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex justify-between items-center pt-3 border-t border-gray-100">
                          <div className="text-lg font-bold text-blue-600">
                            {prop.price_usd ? `$${prop.price_usd.toLocaleString()}` : 'N/A'}
                          </div>
                          <div className="text-xs text-gray-400">
                            {timeAgo}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Input Section */}
          {!showResults && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Input Type
                </label>
                <div className="flex gap-4">
                  <label className="inline-flex items-center">
                    <input 
                      type="radio" 
                      name="inputType" 
                      value="url" 
                      checked={inputType === 'url'}
                      onChange={() => setInputType('url')}
                      className="form-radio text-blue-600" 
                    />
                    <span className="ml-2">URL</span>
                  </label>
                  <label className="inline-flex items-center">
                    <input 
                      type="radio" 
                      name="inputType" 
                      value="text" 
                      checked={inputType === 'text'}
                      onChange={() => setInputType('text')}
                      className="form-radio text-blue-600" 
                    />
                    <span className="ml-2">Text/HTML</span>
                  </label>
                </div>
              </div>

              {/* URL Input */}
              {inputType === 'url' && (
                <div className="mb-4" id="urlInputContainer">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t.dataCollector.propertyUrl}
                  </label>
                  <input 
                    id="propertyUrlInput"
                    type="url" 
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://encuentra24.com/property/..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              )}

              {/* Content Type Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content Type
                </label>
                <select
                  value={selectedContentType}
                  onChange={(e) => setSelectedContentType(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  {contentTypes.map((type) => (
                    <option key={type.key} value={type.key}>
                      {type.icon} {type.label}
                    </option>
                  ))}
                </select>
                {contentTypes.find(t => t.key === selectedContentType) && (
                  <p className="mt-1 text-xs text-gray-500">
                    {contentTypes.find(t => t.key === selectedContentType)?.description}
                  </p>
                )}
              </div>

              {/* Text Input */}
              {inputType === 'text' && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t.dataCollector.propertyText}
                  </label>
                  <textarea 
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    rows={10}
                    placeholder={t.dataCollector.propertyTextPlaceholder}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              )}

              <button 
                id="processPropertyButton"
                onClick={processProperty}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition duration-200 font-semibold flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
                {t.dataCollector.processProperty}
              </button>
            </div>
          )}

          {/* Loading Spinner / Progress Bar */}
          {loading && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <ProgressBar 
                progress={progress.progress}
                status={progress.status}
                stage={progress.stage}
                substage={progress.substage}
              />
              {isConnected && (
                <div className="mt-4 text-center">
                  <p className="text-xs text-green-600">
                    🟢 {t.dataCollector.connectedRealtime}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Results Section */}
          {showResults && extractedProperty && (
            <div id="resultsSection" className="mb-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-800">{t.dataCollector.extractedData}</h2>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    confidence >= 0.8 ? 'bg-green-100 text-green-800' :
                    confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {Math.round(confidence * 100)}% {t.dataCollector.confidence}
                  </span>
                </div>
                
                {/* Source Website Badge */}
                <div className="mb-6 flex items-center gap-4 text-sm flex-wrap">
                  {extractedProperty.source_website && (
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600">{t.dataCollector.source}:</span>
                      <span className="px-3 py-1 bg-gray-100 rounded-full font-medium">
                        {extractedProperty.source_website}
                      </span>
                    </div>
                  )}
                  
                  {/* Content Type Badge */}
                  {(extractedProperty as any).content_type && (
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600">Type:</span>
                      <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">
                        {contentTypes.find(t => t.key === (extractedProperty as any).content_type)?.icon} {' '}
                        {contentTypes.find(t => t.key === (extractedProperty as any).content_type)?.label || (extractedProperty as any).content_type}
                      </span>
                    </div>
                  )}
                  
                  {/* Page Type Badge - NEW */}
                  {(extractedProperty as any).page_type && (
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600">Página:</span>
                      <span className={`px-3 py-1 rounded-full font-medium ${
                        (extractedProperty as any).page_type === 'specific' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-purple-100 text-purple-800'
                      }`}>
                        {(extractedProperty as any).page_type === 'specific' ? '📄 Específica' : '📚 General'}
                      </span>
                    </div>
                  )}
                  
                  {/* Detection Confidence Badge */}
                  {(extractedProperty as any).page_type_confidence && (
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600">Confianza:</span>
                      <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full font-medium text-xs">
                        {Math.round((extractedProperty as any).page_type_confidence * 100)}%
                      </span>
                    </div>
                  )}
                </div>

                {/* Property Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {(() => {
                    const contentType = extractedProperty.content_type || 'real_estate';
                    const pageType = (extractedProperty as any).page_type || 'specific';
                    
                    // GENERAL PAGE TEMPLATES
                    if (pageType === 'general') {
                      // Tour Guide Page
                      if (contentType === 'tour') {
                        const tourTypes = (extractedProperty as any).tour_types_available || (extractedProperty as any).tour_types || [];
                        const priceRange = (extractedProperty as any).price_range 
                          ? `$${(extractedProperty as any).price_range.min_usd || 'N/A'} - $${(extractedProperty as any).price_range.max_usd || 'N/A'}`
                          : (extractedProperty as any).typical_price_range;
                        const featuredCount = (extractedProperty as any).featured_tours?.length || (extractedProperty as any).total_tours_mentioned || (extractedProperty as any).featured_items_count;
                        
                        return [
                          { label: 'Destino', value: (extractedProperty as any).destination },
                          { label: 'Ubicación', value: extractedProperty.location },
                          { label: 'Tipos de Tours', value: Array.isArray(tourTypes) && tourTypes.length > 0 ? tourTypes.join(', ') : t.common.na },
                          { label: 'Rango de Precios', value: priceRange },
                          { label: 'Mejor Temporada', value: (extractedProperty as any).best_season },
                          { label: 'Tours Destacados', value: featuredCount ? `${featuredCount} tours` : t.common.na },
                        ];
                      }
                      // Restaurant Guide Page
                      else if (contentType === 'restaurant') {
                        return [
                          { label: 'Destino', value: (extractedProperty as any).destination },
                          { label: 'Ubicación', value: extractedProperty.location },
                          { label: 'Tipos de Cocina', value: (extractedProperty as any).cuisine_types ? (extractedProperty as any).cuisine_types.join(', ') : t.common.na },
                          { label: 'Rango de Precios', value: (extractedProperty as any).typical_price_range },
                          { label: 'Restaurantes Destacados', value: (extractedProperty as any).featured_items_count ? `${(extractedProperty as any).featured_items_count} restaurantes` : t.common.na },
                        ];
                      }
                      // Real Estate Guide Page
                      else if (contentType === 'real_estate') {
                        return [
                          { label: 'Destino', value: (extractedProperty as any).destination },
                          { label: 'Ubicación', value: extractedProperty.location },
                          { label: 'Tipos de Propiedades', value: (extractedProperty as any).property_types ? (extractedProperty as any).property_types.join(', ') : t.common.na },
                          { label: 'Rango de Precios', value: (extractedProperty as any).typical_price_range },
                          { label: 'Propiedades Destacadas', value: (extractedProperty as any).featured_items_count ? `${(extractedProperty as any).featured_items_count} propiedades` : t.common.na },
                        ];
                      }
                      // Default General Page
                      return [
                        { label: 'Destino', value: (extractedProperty as any).destination },
                        { label: 'Ubicación', value: extractedProperty.location },
                        { label: 'Elementos Destacados', value: (extractedProperty as any).featured_items_count || t.common.na },
                      ];
                    }
                    
                    // SPECIFIC PAGE TEMPLATES
                    // Define fields based on content type
                    if (contentType === 'tour') {
                      return [
                        { label: 'Nombre del Tour', value: extractedProperty.tour_name || extractedProperty.title },
                        { label: 'Tipo de Tour', value: extractedProperty.tour_type },
                        { label: 'Precio (USD)', value: extractedProperty.price_usd ? `$${parseFloat(String(extractedProperty.price_usd)).toLocaleString()}` : t.common.na },
                        { label: 'Duración', value: extractedProperty.duration_hours ? `${extractedProperty.duration_hours} horas` : t.common.na },
                        { label: 'Dificultad', value: extractedProperty.difficulty_level },
                        { label: 'Ubicación', value: extractedProperty.location },
                        { label: 'Edad Mínima', value: extractedProperty.minimum_age ? `${extractedProperty.minimum_age} años` : t.common.na },
                        { label: 'Máx. Participantes', value: extractedProperty.max_participants },
                        { label: 'Pickup Incluido', value: extractedProperty.pickup_included === true ? 'Sí' : extractedProperty.pickup_included === false ? 'No' : t.common.na },
                        { label: 'Idiomas', value: extractedProperty.languages_available ? extractedProperty.languages_available.join(', ') : t.common.na },
                        { label: 'Qué Incluye', value: extractedProperty.included_items ? extractedProperty.included_items.join(', ') : t.common.na },
                        { label: 'Cancelación', value: extractedProperty.cancellation_policy },
                      ];
                    } else if (contentType === 'restaurant') {
                      return [
                        { label: 'Nombre', value: extractedProperty.restaurant_name || extractedProperty.title },
                        { label: 'Tipo de Cocina', value: extractedProperty.cuisine_type },
                        { label: 'Rango de Precio', value: extractedProperty.price_range },
                        { label: 'Precio Promedio', value: extractedProperty.average_price_per_person ? `$${extractedProperty.average_price_per_person}` : t.common.na },
                        { label: 'Ubicación', value: extractedProperty.location },
                        { label: 'Horario', value: extractedProperty.hours_of_operation },
                        { label: 'Ambiente', value: extractedProperty.atmosphere },
                        { label: 'Reservas', value: extractedProperty.reservations_required === true ? 'Requeridas' : extractedProperty.reservations_required === false ? 'No requeridas' : t.common.na },
                        { label: 'Platillos Destacados', value: extractedProperty.signature_dishes ? extractedProperty.signature_dishes.join(', ') : t.common.na },
                        { label: 'Opciones Dietéticas', value: extractedProperty.dietary_options ? extractedProperty.dietary_options.join(', ') : t.common.na },
                        { label: 'Código de Vestimenta', value: extractedProperty.dress_code },
                        { label: 'Teléfono', value: extractedProperty.contact_phone },
                      ];
                    } else if (contentType === 'transportation') {
                      return [
                        { label: 'Nombre', value: extractedProperty.transport_name || extractedProperty.title },
                        { label: 'Tipo', value: extractedProperty.transport_type },
                        { label: 'Ruta', value: extractedProperty.route },
                        { label: 'Precio (USD)', value: extractedProperty.price_usd ? `$${parseFloat(String(extractedProperty.price_usd)).toLocaleString()}` : t.common.na },
                        { label: 'Duración', value: extractedProperty.duration_hours ? `${extractedProperty.duration_hours} horas` : t.common.na },
                        { label: 'Horario', value: extractedProperty.schedule },
                        { label: 'Frecuencia', value: extractedProperty.frequency },
                        { label: 'Punto de Recogida', value: extractedProperty.pickup_location },
                        { label: 'Punto de Entrega', value: extractedProperty.dropoff_location },
                        { label: 'Reserva', value: extractedProperty.booking_required === true ? 'Requerida' : extractedProperty.booking_required === false ? 'No requerida' : t.common.na },
                        { label: 'Equipaje', value: extractedProperty.luggage_allowance },
                        { label: 'Teléfono', value: extractedProperty.contact_phone },
                      ];
                    } else if (contentType === 'local_tips') {
                      return [
                        { label: 'Título', value: extractedProperty.tip_title || extractedProperty.title },
                        { label: 'Categoría', value: extractedProperty.category },
                        { label: 'Ubicación', value: extractedProperty.location },
                        { label: 'Costo Estimado', value: extractedProperty.cost_estimate },
                        { label: 'Mejor Época', value: extractedProperty.best_time },
                        { label: 'Consejos Prácticos', value: extractedProperty.practical_advice ? extractedProperty.practical_advice.join(', ') : t.common.na },
                        { label: 'Qué Evitar', value: extractedProperty.things_to_avoid ? extractedProperty.things_to_avoid.join(', ') : t.common.na },
                        { label: 'Costumbres Locales', value: extractedProperty.local_customs ? extractedProperty.local_customs.join(', ') : t.common.na },
                      ];
                    } else {
                      // Default: real_estate
                      return [
                        { label: t.dataCollector.propertyName, value: extractedProperty.title || extractedProperty.property_name },
                        { label: t.dataCollector.listingId, value: extractedProperty.listing_id },
                        { label: t.dataCollector.listingStatus, value: extractedProperty.listing_status || extractedProperty.listing_type },
                        { label: t.dataCollector.price, value: extractedProperty.price_usd ? `$${parseFloat(String(extractedProperty.price_usd)).toLocaleString()}` : t.common.na },
                        { label: t.dataCollector.type, value: extractedProperty.property_type_display || extractedProperty.property_type },
                        { 
                          label: t.dataCollector.location, 
                          value: extractedProperty.location || extractedProperty.address || (extractedProperty.city && extractedProperty.province ? `${extractedProperty.city}, ${extractedProperty.province}` : null),
                          isLocation: true,
                          lat: extractedProperty.latitude,
                          lng: extractedProperty.longitude
                        },
                        { label: t.dataCollector.bedrooms, value: extractedProperty.bedrooms },
                        { label: t.dataCollector.bathrooms, value: extractedProperty.bathrooms },
                        { label: t.dataCollector.squareMeters, value: extractedProperty.area_m2 || extractedProperty.square_meters },
                        { label: t.dataCollector.lotSize, value: extractedProperty.lot_size_m2 },
                        { label: t.dataCollector.dateListed, value: extractedProperty.date_listed },
                        { label: t.dataCollector.status, value: extractedProperty.status_display || extractedProperty.status },
                      ];
                    }
                  })().map((field, index) => {
                    const displayValue = field.value || t.common.na
                    
                    if ('isLocation' in field && field.isLocation && field.lat && field.lng) {
                      const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${field.lat},${field.lng}`
                      return (
                        <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                          <p className="text-sm text-gray-600">{field.label}</p>
                          <p className="text-lg font-semibold text-gray-800">{displayValue}</p>
                          <a href={mapsUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center mt-1 text-sm text-blue-600 hover:text-blue-800">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            </svg>
                            {t.dataCollector.viewOnMaps} ({field.lat}, {field.lng})
                          </a>
                        </div>
                      )
                    }
                    
                    return (
                      <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                        <p className="text-sm text-gray-600">{field.label}</p>
                        <p className={`text-lg font-semibold ${displayValue === t.common.na ? 'text-gray-400 italic' : 'text-gray-800'}`}>{displayValue}</p>
                      </div>
                    )
                  })}
                </div>

                {/* Overview Section - Only for General Pages */}
                {(extractedProperty as any).page_type === 'general' && (extractedProperty as any).overview && (
                  <div className="mb-6 bg-gradient-to-br from-purple-50 to-indigo-50 border-l-4 border-purple-500 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-purple-900 mb-3 flex items-center gap-2">
                      📚 Resumen General
                    </h3>
                    <p className="text-gray-700 leading-relaxed">
                      {(extractedProperty as any).overview}
                    </p>
                  </div>
                )}

                {/* Tips Section - Only for General Pages */}
                {(extractedProperty as any).page_type === 'general' && (extractedProperty as any).tips && (extractedProperty as any).tips.length > 0 && (
                  <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-500 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-yellow-900 mb-3 flex items-center gap-2">
                      💡 Consejos y Recomendaciones
                    </h3>
                    <ul className="space-y-2">
                      {(extractedProperty as any).tips.map((tip: string, index: number) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-yellow-600 mt-1">•</span>
                          <span className="text-gray-700">{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Featured Items Section - Only for General Pages */}
                {(extractedProperty as any).page_type === 'general' && (
                  (() => {
                    // Check multiple possible field names for featured items
                    const featuredItems = (extractedProperty as any).featured_items 
                      || (extractedProperty as any).featured_tours 
                      || [];
                    
                    if (!Array.isArray(featuredItems) || featuredItems.length === 0) {
                      return null;
                    }
                    
                    return (
                      <div className="mb-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                          ⭐ Elementos Destacados
                          <span className="text-sm font-normal text-gray-500">
                            ({featuredItems.length} items)
                          </span>
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                          {featuredItems.map((item: any, index: number) => (
                            <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow bg-white">
                              <h4 className="font-semibold text-gray-800 mb-2 truncate" title={item.name || item.title}>
                                {item.name || item.title || `Item ${index + 1}`}
                              </h4>
                              {(item.price || item.price_usd) && (
                                <p className="text-sm text-green-600 font-medium mb-1">
                                  {item.price || `$${item.price_usd}`}
                                </p>
                              )}
                              {item.rating && (
                                <p className="text-sm text-yellow-600 mb-2">
                                  ⭐ {item.rating}
                                </p>
                              )}
                              {(item.url || item.source_url) && (
                                <a 
                                  href={item.url || item.source_url} 
                                  target="_blank" 
                                  rel="noopener noreferrer" 
                                  className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                                >
                                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                                  </svg>
                                  Ver detalle
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })()
                )}

                {/* Regions Section - Only for General Tour/Real Estate Pages */}
                {(extractedProperty as any).page_type === 'general' && (extractedProperty as any).regions && (extractedProperty as any).regions.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      🗺️ Regiones y Destinos
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {(extractedProperty as any).regions.map((region: any, index: number) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gradient-to-br from-blue-50 to-cyan-50">
                          <h4 className="font-semibold text-blue-900 mb-2">
                            {region.name}
                          </h4>
                          {region.description && (
                            <p className="text-sm text-gray-700 mb-3">
                              {region.description}
                            </p>
                          )}
                          {region.popular_activities && region.popular_activities.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-gray-600 mb-1">Actividades populares:</p>
                              <div className="flex flex-wrap gap-1">
                                {region.popular_activities.map((activity: string, idx: number) => (
                                  <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                    {activity}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Seasonal Activities - Only for General Pages */}
                {(extractedProperty as any).page_type === 'general' && (extractedProperty as any).seasonal_activities && (extractedProperty as any).seasonal_activities.length > 0 && (
                  <div className="mb-6 bg-gradient-to-br from-green-50 to-emerald-50 border-l-4 border-green-500 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-green-900 mb-4 flex items-center gap-2">
                      📅 Actividades por Temporada
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {(extractedProperty as any).seasonal_activities.map((season: any, index: number) => (
                        <div key={index} className="bg-white rounded-lg p-4 border border-green-200">
                          <h4 className="font-semibold text-green-800 mb-2">
                            {season.season}
                          </h4>
                          {season.why_this_season && (
                            <p className="text-sm text-gray-600 mb-2 italic">
                              {season.why_this_season}
                            </p>
                          )}
                          {season.recommended_activities && season.recommended_activities.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {season.recommended_activities.map((activity: string, idx: number) => (
                                <span key={idx} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                                  {activity}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* FAQs Section - Only for General Pages */}
                {(extractedProperty as any).page_type === 'general' && (extractedProperty as any).faqs && (extractedProperty as any).faqs.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      ❓ Preguntas Frecuentes
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {(extractedProperty as any).faqs.map((faq: any, index: number) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
                          <h4 className="font-semibold text-gray-800 mb-2 flex items-start gap-2">
                            <span className="text-indigo-600 flex-shrink-0">Q:</span>
                            <span>{faq.question}</span>
                          </h4>
                          <p className="text-sm text-gray-700 ml-5">
                            <span className="font-medium text-indigo-600">A:</span> {faq.answer}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* What to Pack - Only for General Pages */}
                {(extractedProperty as any).page_type === 'general' && (extractedProperty as any).what_to_pack && (extractedProperty as any).what_to_pack.length > 0 && (
                  <div className="mb-6 bg-orange-50 border-l-4 border-orange-500 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-orange-900 mb-3 flex items-center gap-2 flex-wrap">
                      <span>🎒 Qué Llevar</span>
                    </h3>
                    <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
                      {(extractedProperty as any).what_to_pack.map((item: string, index: number) => (
                        <li key={index} className="flex items-center gap-2">
                          <span className="text-orange-600">✓</span>
                          <span className="text-gray-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Description */}
                {extractedProperty.description && (
                  <div className="col-span-2 border-l-4 border-blue-500 pl-4 py-2 mb-6">
                    <p className="text-sm text-gray-600">{t.dataCollector.description}</p>
                    <p className="text-gray-800">{extractedProperty.description.substring(0, 200)}{extractedProperty.description.length > 200 ? '...' : ''}</p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-4 pt-6 border-t">
                  <button onClick={viewFullDetails} className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition">
                    ✓ {t.dataCollector.saveToDatabase}
                  </button>
                  <button onClick={() => alert('Edit functionality will open a detailed form')} className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition">
                    ✎ {t.dataCollector.editDetails}
                  </button>
                  <button onClick={resetForm} className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition">
                    + {t.dataCollector.newProperty}
                  </button>
                </div>
              </div>

              {/* Error Section */}
              {error && (
                <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
                  <h3 className="text-red-800 font-semibold mb-2">{t.dataCollector.extractionError}</h3>
                  <p className="text-red-700">{error}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
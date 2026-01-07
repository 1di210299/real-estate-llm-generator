import { useState, useEffect } from 'react'
import './DataCollector.css'

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

interface CategoryConfig {
  name: string
  icon: string
  color: string
}

interface WebsiteConfig {
  name: string
  icon: string
  color: string
}

function App() {
  const [inputType, setInputType] = useState<'url' | 'text'>('url')
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')
  const [sourceWebsite, setSourceWebsite] = useState('encuentra24')
  const [loading, setLoading] = useState(false)
  const [extractedProperty, setExtractedProperty] = useState<PropertyData | null>(null)
  const [error, setError] = useState('')
  const [showResults, setShowResults] = useState(false)
  const [properties, setProperties] = useState<PropertyData[]>([])
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const [confidence, setConfidence] = useState(0)

  // API Base URL configuration with intelligent fallback
  const getApiBase = () => {
    let baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    
    // Remover trailing slash si existe
    baseUrl = baseUrl.replace(/\/$/, '')
    
    // Si ya tiene /api, retornar tal cual
    if (baseUrl.endsWith('/api')) {
      return baseUrl
    }
    
    // Si no tiene /api, agregarlo
    return `${baseUrl}/api`
  }

  const API_BASE = getApiBase()

  const WEBSITES: Record<string, WebsiteConfig> = {
    encuentra24: {
      name: 'Encuentra24',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path></svg>',
      color: '#10b981'
    },
    crrealestate: {
      name: 'CR Real Estate',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z" clip-rule="evenodd"></path></svg>',
      color: '#3b82f6'
    },
    coldwellbanker: {
      name: 'Coldwell Banker',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clip-rule="evenodd"></path><path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z"></path></svg>',
      color: '#8b5cf6'
    },
    other: {
      name: 'Other Sources',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path></svg>',
      color: '#6b7280'
    }
  }

  const CATEGORIES: Record<string, CategoryConfig> = {
    'proyectos-nuevos': {
      name: 'New Projects',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4zm7 5a1 1 0 00-2 0v1H8a1 1 0 000 2h1v1a1 1 0 002 0v-1h1a1 1 0 000-2h-1V9z" clip-rule="evenodd"></path></svg>',
      color: '#8b5cf6'
    },
    'venta-casas': {
      name: 'Houses for Sale',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path></svg>',
      color: '#10b981'
    },
    'venta-apartamentos': {
      name: 'Apartments for Sale',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z" clip-rule="evenodd"></path></svg>',
      color: '#3b82f6'
    },
    'venta-negocios': {
      name: 'Businesses for Sale',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clip-rule="evenodd"></path><path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z"></path></svg>',
      color: '#f59e0b'
    },
    'venta-lotes': {
      name: 'Lots/Land',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path></svg>',
      color: '#059669'
    },
    'venta-fincas': {
      name: 'Farms for Sale',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 3.5a1.5 1.5 0 013 0V4a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-.5a1.5 1.5 0 000 3h.5a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-.5a1.5 1.5 0 00-3 0v.5a1 1 0 01-1 1H6a1 1 0 01-1-1v-3a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H4a1 1 0 001-1V6a1 1 0 011-1h3a1 1 0 001-1v-.5z"></path></svg>',
      color: '#84cc16'
    },
    'alquiler-casas': {
      name: 'Houses for Rent',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z"></path><path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707l-2-2A1 1 0 0015 7h-1z"></path></svg>',
      color: '#06b6d4'
    },
    'alquiler-apartamentos': {
      name: 'Apartments for Rent',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M11 17a1 1 0 001.447.894l4-2A1 1 0 0017 15V9.236a1 1 0 00-1.447-.894l-4 2a1 1 0 00-.553.894V17zM15.211 6.276a1 1 0 000-1.788l-4.764-2.382a1 1 0 00-.894 0L4.789 4.488a1 1 0 000 1.788l4.764 2.382a1 1 0 00.894 0l4.764-2.382zM4.447 8.342A1 1 0 003 9.236V15a1 1 0 00.553.894l4 2A1 1 0 009 17v-5.764a1 1 0 00-.553-.894l-4-2z"></path></svg>',
      color: '#0ea5e9'
    },
    'alquiler-locales': {
      name: 'Commercial for Rent',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M13 7H7v6h6V7z"></path><path fill-rule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clip-rule="evenodd"></path></svg>',
      color: '#8b5cf6'
    },
    other: {
      name: 'Other',
      icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path></svg>',
      color: '#6b7280'
    }
  }

  useEffect(() => {
    loadHistoryFromBackend()
  }, [])

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

  const getWebsiteFromUrl = (url: string): string => {
    if (!url) return 'other'
    const urlLower = url.toLowerCase()
    
    if (urlLower.includes('encuentra24')) return 'encuentra24'
    if (urlLower.includes('crrealestate') || urlLower.includes('cr-realestate')) return 'crrealestate'
    if (urlLower.includes('coldwellbanker')) return 'coldwellbanker'
    
    return 'other'
  }

  const autoDetectWebsite = () => {
    if (url) {
      const detected = getWebsiteFromUrl(url)
      setSourceWebsite(detected)
    }
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
      const response = await fetch(`${API_BASE}/v1/properties/?page_size=100&ordering=-created_at`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      if (data.results) {
        setProperties(data.results)
      }
    } catch (error) {
      console.error('Error loading history:', error)
    }
  }

  const loadPropertyFromHistory = async (propertyId: string) => {
    try {
      const response = await fetch(`${API_BASE}/v1/properties/${propertyId}/`)
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
      const response = await fetch(`${API_BASE}/v1/properties/?page_size=100`)
      const data = await response.json()
      for (const prop of data.results) {
        await fetch(`${API_BASE}/v1/properties/${prop.id}/`, { method: 'DELETE' })
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

    try {
      const endpoint = inputType === 'url' ? `${API_BASE}/v1/ingest/url/` : `${API_BASE}/v1/ingest/text/`
      const body = inputType === 'url' 
        ? { url, source_website: sourceWebsite } 
        : { text, source_website: sourceWebsite }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (response.ok) {
        setExtractedProperty(data.property)
        setConfidence(data.extraction_confidence || 0.9)
        setShowResults(true)
        setError('')
      } else {
        setError(data.error || 'Failed to process property')
      }
    } catch (error) {
      setError('Network error: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const viewFullDetails = async () => {
    if (!extractedProperty) {
      alert('No property data to save')
      return
    }
    
    try {
      const response = await fetch(`${API_BASE}/v1/ingest/save/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_data: extractedProperty
        })
      })

      const data = await response.json()
      
      if (response.ok && data.status === 'success') {
        alert(`✓ Property saved successfully!\n\nProperty ID: ${data.property_id}\nName: ${data.property.property_name}`)
        loadHistoryFromBackend()
        resetForm()
      } else {
        alert(`Error saving property: ${data.error || 'Unknown error'}`)
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
    <div className="bg-gray-50 flex">
      {/* Left Sidebar - Permanent */}
      <div className="w-80 bg-white shadow-xl flex flex-col h-screen sticky top-0">
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
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-6 py-8 max-w-5xl">
          {/* Header */}
          <header className="mb-8">
            <div className="flex items-center justify-between">
              <div id="headerTitle">
                <h1 className="text-3xl font-bold text-gray-800 mb-2">Property Data Collector</h1>
                <p className="text-gray-600">Paste a property URL or text to automatically extract structured data</p>
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
          </header>

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

              {/* Website Source Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Source Website
                </label>
                <select 
                  value={sourceWebsite}
                  onChange={(e) => setSourceWebsite(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  <option value="encuentra24">Encuentra24</option>
                  <option value="crrealestate">CR Real Estate</option>
                  <option value="coldwellbanker">Coldwell Banker</option>
                  <option value="other">Other / Manual</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">Select the website you're scraping from</p>
              </div>

              {/* URL Input */}
              {inputType === 'url' && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Property URL
                  </label>
                  <input 
                    type="url" 
                    value={url}
                    onChange={(e) => {
                      setUrl(e.target.value)
                      autoDetectWebsite()
                    }}
                    placeholder="https://encuentra24.com/property/..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              )}

              {/* Text Input */}
              {inputType === 'text' && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Property Text/HTML
                  </label>
                  <textarea 
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    rows={10}
                    placeholder="Paste property description, HTML, or text here..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              )}

              <button 
                onClick={processProperty}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition duration-200 font-semibold flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
                Process Property
              </button>
            </div>
          )}

          {/* Loading Spinner */}
          {loading && (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <div className="spinner"></div>
              <p className="text-gray-600 mt-4">Processing property data...</p>
              <p className="text-sm text-gray-500 mt-2">Scraping from <span className="font-semibold">{WEBSITES[sourceWebsite]?.name || 'Unknown'}</span></p>
              <p className="text-xs text-gray-400 mt-1">This may take 10-30 seconds</p>
            </div>
          )}

          {/* Results Section */}
          {showResults && extractedProperty && (
            <div id="resultsSection" className="mb-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-800">Extracted Property Data</h2>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    confidence >= 0.8 ? 'bg-green-100 text-green-800' :
                    confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {Math.round(confidence * 100)}% Confidence
                  </span>
                </div>
                
                {/* Source Website Badge */}
                <div className="mb-6 flex items-center gap-2 text-sm">
                  <span className="text-gray-600">Source:</span>
                  <span className="px-3 py-1 bg-gray-100 rounded-full font-medium">
                    {WEBSITES[extractedProperty.source_website || 'other']?.name || 'Other'}
                  </span>
                </div>

                {/* Property Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {[
                    { label: 'Property Name', value: extractedProperty.property_name },
                    { label: 'Listing ID', value: extractedProperty.listing_id },
                    { label: 'Listing Status', value: extractedProperty.listing_status },
                    { label: 'Price (USD)', value: extractedProperty.price_usd ? `$${parseFloat(String(extractedProperty.price_usd)).toLocaleString()}` : 'N/A' },
                    { label: 'Type', value: extractedProperty.property_type_display || extractedProperty.property_type },
                    { 
                      label: 'Location', 
                      value: extractedProperty.location,
                      isLocation: true,
                      lat: extractedProperty.latitude,
                      lng: extractedProperty.longitude
                    },
                    { label: 'Bedrooms', value: extractedProperty.bedrooms },
                    { label: 'Bathrooms', value: extractedProperty.bathrooms },
                    { label: 'Square Meters', value: extractedProperty.square_meters },
                    { label: 'Lot Size (m²)', value: extractedProperty.lot_size_m2 },
                    { label: 'Date Listed', value: extractedProperty.date_listed },
                    { label: 'Status', value: extractedProperty.status_display || extractedProperty.status },
                  ].map((field, index) => {
                    const displayValue = field.value || 'N/A'
                    
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
                            Ver en Google Maps ({field.lat}, {field.lng})
                          </a>
                        </div>
                      )
                    }
                    
                    return (
                      <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                        <p className="text-sm text-gray-600">{field.label}</p>
                        <p className={`text-lg font-semibold ${displayValue === 'N/A' ? 'text-gray-400 italic' : 'text-gray-800'}`}>{displayValue}</p>
                      </div>
                    )
                  })}
                </div>

                {/* Description */}
                {extractedProperty.description && (
                  <div className="col-span-2 border-l-4 border-blue-500 pl-4 py-2 mb-6">
                    <p className="text-sm text-gray-600">Description</p>
                    <p className="text-gray-800">{extractedProperty.description.substring(0, 200)}{extractedProperty.description.length > 200 ? '...' : ''}</p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-4 pt-6 border-t">
                  <button onClick={viewFullDetails} className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition">
                    ✓ Save to Database
                  </button>
                  <button onClick={() => alert('Edit functionality will open a detailed form')} className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition">
                    ✎ Edit Details
                  </button>
                  <button onClick={resetForm} className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition">
                    + New Property
                  </button>
                </div>
              </div>

              {/* Error Section */}
              {error && (
                <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
                  <h3 className="text-red-800 font-semibold mb-2">⚠️ Extraction Error</h3>
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
import React from 'react';

interface PropertyData {
  id?: string;
  property_name?: string;
  location?: string;
  price_usd?: string;
  property_type?: string;
  url?: string;
  category?: string;
}

interface SidebarProps {
  properties: PropertyData[];
  onSelectProperty: (id: string) => void;
  onRefresh: () => void;
  onClearAll: () => void;
}

export function Sidebar({ properties, onSelectProperty, onRefresh, onClearAll }: SidebarProps) {
  const groupedByCategory = properties.reduce((acc, prop) => {
    const category = prop.category || getCategoryFromUrl(prop.url || '') || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(prop);
    return acc;
  }, {} as Record<string, PropertyData[]>);

  return (
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
      
      <div className="flex-1 overflow-y-auto p-4">
        {Object.keys(groupedByCategory).length === 0 ? (
          <div className="text-center py-8">
            <svg className="w-16 h-16 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <p className="text-gray-500 text-sm">No properties saved yet</p>
          </div>
        ) : (
          Object.entries(groupedByCategory).map(([category, props]) => (
            <CategoryGroup
              key={category}
              category={category}
              properties={props}
              onSelectProperty={onSelectProperty}
            />
          ))
        )}
      </div>
      
      <div className="p-4 border-t space-y-2">
        <button
          onClick={onRefresh}
          className="w-full bg-blue-100 text-blue-700 py-2 px-4 rounded hover:bg-blue-200 transition text-sm flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          Refresh
        </button>
        <button
          onClick={onClearAll}
          className="w-full bg-red-100 text-red-700 py-2 px-4 rounded hover:bg-red-200 transition text-sm"
        >
          Clear All History
        </button>
      </div>
    </div>
  );
}

function CategoryGroup({ category, properties, onSelectProperty }: { category: string; properties: PropertyData[]; onSelectProperty: (id: string) => void }) {
  const config = CATEGORIES[category] || CATEGORIES.other;
  
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg mb-2">
        <div style={{ color: config.color }} dangerouslySetInnerHTML={{ __html: config.icon }} />
        <span className="font-semibold text-gray-800 text-sm">{config.name}</span>
        <span className="ml-auto text-xs text-gray-500">({properties.length})</span>
      </div>
      <div className="space-y-2 ml-2">
        {properties.map((prop) => (
          <div
            key={prop.id}
            onClick={() => prop.id && onSelectProperty(prop.id)}
            className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition cursor-pointer border-l-2"
            style={{ borderColor: config.color }}
          >
            <h3 className="font-semibold text-xs text-gray-800 truncate">
              {prop.property_name || 'Untitled'}
            </h3>
            <p className="text-xs text-gray-600 truncate">{prop.location || 'N/A'}</p>
            <div className="flex justify-between items-center mt-1">
              <span className="text-sm font-bold" style={{ color: config.color }}>
                ${prop.price_usd ? parseFloat(prop.price_usd).toLocaleString() : 'N/A'}
              </span>
              <span className="text-xs bg-white px-2 py-0.5 rounded">
                {prop.property_type || 'N/A'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getCategoryFromUrl(url: string): string {
  if (!url) return 'other';
  const urlLower = url.toLowerCase();
  
  if (urlLower.includes('proyectos-nuevos')) return 'proyectos-nuevos';
  if (urlLower.includes('venta-casas')) return 'venta-casas';
  if (urlLower.includes('venta-apartamentos')) return 'venta-apartamentos';
  if (urlLower.includes('coldwellbanker')) return 'venta-casas';
  
  return 'other';
}

const CATEGORIES: Record<string, { name: string; icon: string; color: string }> = {
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
  'other': {
    name: 'Other',
    icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path></svg>',
    color: '#6b7280'
  }
};

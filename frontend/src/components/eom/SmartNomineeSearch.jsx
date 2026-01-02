import { useState, useMemo, useRef, useEffect } from 'react'

/**
 * Smart Search Filter for EOM Nominee Selection
 * Provides intelligent search and filtering to quickly find nominees
 */
const SmartNomineeSearch = ({ 
  nominees = [], 
  value, 
  onChange, 
  placeholder = "Search for nominee by name, email, department, or role..." 
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [filters, setFilters] = useState({
    department: '',
    role: '',
    segment: ''
  })
  const searchInputRef = useRef(null)
  const dropdownRef = useRef(null)

  // Get unique departments, roles, and segments from nominees
  const availableFilters = useMemo(() => {
    const departments = [...new Set(nominees.map(n => n.department).filter(Boolean))].sort()
    const roles = [...new Set(nominees.map(n => n.role_title || n.title).filter(Boolean))].sort()
    const segments = [...new Set(nominees.map(n => n.segment).filter(Boolean))].sort()
    return { departments, roles, segments }
  }, [nominees])

  // Filter nominees based on search query and filters
  const filteredNominees = useMemo(() => {
    let filtered = nominees

    // Apply text search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(nominee => {
        const name = (nominee.name || nominee.full_name || '').toLowerCase()
        const email = (nominee.email || '').toLowerCase()
        const department = (nominee.department || '').toLowerCase()
        const role = ((nominee.role_title || nominee.title) || '').toLowerCase()
        
        return name.includes(query) || 
               email.includes(query) || 
               department.includes(query) || 
               role.includes(query)
      })
    }

    // Apply filters
    if (filters.department) {
      filtered = filtered.filter(n => n.department === filters.department)
    }
    if (filters.role) {
      filtered = filtered.filter(n => (n.role_title || n.title) === filters.role)
    }
    if (filters.segment) {
      filtered = filtered.filter(n => n.segment === filters.segment)
    }

    return filtered
  }, [nominees, searchQuery, filters])

  // Get selected nominee details
  const selectedNominee = useMemo(() => {
    return nominees.find(n => n.email === value)
  }, [nominees, value])

  // Handle selection
  const handleSelect = (nominee) => {
    onChange(nominee.email)
    setSearchQuery('')
    setIsOpen(false)
  }

  // Clear selection
  const handleClear = () => {
    onChange('')
    setSearchQuery('')
    setIsOpen(false)
  }

  // Handle input focus
  const handleFocus = () => {
    setIsOpen(true)
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target) &&
        searchInputRef.current &&
        !searchInputRef.current.contains(event.target)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Highlight matching text
  const highlightMatch = (text, query) => {
    if (!query.trim()) return text
    
    const parts = text.split(new RegExp(`(${query})`, 'gi'))
    return parts.map((part, i) => 
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i} className="bg-ese-accent-mustard/30 px-1 rounded">
          {part}
        </mark>
      ) : part
    )
  }

  return (
    <div className="relative">
      {/* Search Input */}
      <div className="relative">
        <input
          ref={searchInputRef}
          type="text"
          value={searchQuery || (selectedNominee ? `${selectedNominee.name || selectedNominee.full_name} (${selectedNominee.email})` : '')}
          onChange={(e) => {
            setSearchQuery(e.target.value)
            setIsOpen(true)
            if (!e.target.value) {
              onChange('')
            }
          }}
          onFocus={handleFocus}
          placeholder={placeholder}
          className="w-full px-4 py-3 pl-10 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none"
        />
        <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
          <svg className="w-5 h-5 text-ese-ink-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        {value && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-ese-ink-blue hover:text-ese-ink-navy"
            title="Clear selection"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Filters Bar */}
      <div className="mt-2 flex flex-wrap gap-2">
        <select
          value={filters.department}
          onChange={(e) => setFilters({ ...filters, department: e.target.value })}
          className="px-3 py-1.5 text-sm border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-500"
        >
          <option value="">All Departments</option>
          {availableFilters.departments.map(dept => (
            <option key={dept} value={dept}>{dept}</option>
          ))}
        </select>

        <select
          value={filters.role}
          onChange={(e) => setFilters({ ...filters, role: e.target.value })}
          className="px-3 py-1.5 text-sm border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-500"
        >
          <option value="">All Roles</option>
          {availableFilters.roles.map(role => (
            <option key={role} value={role}>{role}</option>
          ))}
        </select>

        <select
          value={filters.segment}
          onChange={(e) => setFilters({ ...filters, segment: e.target.value })}
          className="px-3 py-1.5 text-sm border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-500"
        >
          <option value="">All Segments</option>
          {availableFilters.segments.map(segment => (
            <option key={segment} value={segment}>
              {segment.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </option>
          ))}
        </select>

        {(filters.department || filters.role || filters.segment) && (
          <button
            onClick={() => setFilters({ department: '', role: '', segment: '' })}
            className="px-3 py-1.5 text-sm text-ese-ink-blue hover:text-ese-ink-navy underline"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Results Count */}
      {searchQuery && (
        <p className="mt-2 text-sm text-ese-ink-blue">
          {filteredNominees.length} {filteredNominees.length === 1 ? 'result' : 'results'} found
        </p>
      )}

      {/* Dropdown Results */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-2 bg-white border border-ese-accent-beige rounded-lg shadow-lg max-h-96 overflow-y-auto"
        >
          {filteredNominees.length === 0 ? (
            <div className="p-4 text-center text-ese-ink-blue">
              <p className="mb-2">No nominees found</p>
              <p className="text-xs">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="py-2">
              {filteredNominees.map((nominee) => {
                const isSelected = nominee.email === value
                return (
                  <button
                    key={nominee.email}
                    onClick={() => handleSelect(nominee)}
                    className={`
                      w-full text-left px-4 py-3 hover:bg-ese-lang-50 transition-colors
                      ${isSelected ? 'bg-ese-accent-mustard/20 border-l-4 border-ese-accent-mustard' : ''}
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-ese-ink-navy mb-1">
                          {searchQuery ? highlightMatch(nominee.name || nominee.full_name || nominee.email, searchQuery) : (nominee.name || nominee.full_name || nominee.email)}
                        </div>
                        <div className="text-sm text-ese-ink-blue space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-ese-ink-medium font-mono text-xs">ID:</span>
                            <span className="font-mono">{nominee.email ? nominee.email.split('@')[0] : 'N/A'}</span>
                            {searchQuery && nominee.email && (
                              <span className="text-ese-ink-medium">•</span>
                            )}
                            {searchQuery && nominee.email && (
                              <span>{highlightMatch(nominee.email, searchQuery)}</span>
                            )}
                          </div>
                          {nominee.department && (
                            <div className="flex items-center gap-2">
                              <span className="text-ese-ink-medium">Division:</span>
                              {searchQuery ? highlightMatch(nominee.department, searchQuery) : nominee.department}
                            </div>
                          )}
                          {(nominee.role_title || nominee.title) && (
                            <div className="flex items-center gap-2">
                              <span className="text-ese-ink-medium">Position:</span>
                              {searchQuery ? highlightMatch(nominee.role_title || nominee.title, searchQuery) : (nominee.role_title || nominee.title)}
                            </div>
                          )}
                        </div>
                      </div>
                      {isSelected && (
                        <div className="ml-2 text-ese-accent-mustard">
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        </div>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Selected Nominee Info */}
      {selectedNominee && !isOpen && (
        <div className="mt-2 p-3 bg-ese-lang-50 rounded-lg border border-ese-lang-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-ese-ink-navy">
                {selectedNominee.name || selectedNominee.full_name}
              </p>
              <p className="text-sm text-ese-ink-blue">
                <span className="font-mono">ID: {selectedNominee.email ? selectedNominee.email.split('@')[0] : 'N/A'}</span>
                {' • '}
                {selectedNominee.email}
              </p>
              <p className="text-xs text-ese-ink-medium mt-1">
                {selectedNominee.department && `Division: ${selectedNominee.department}`}
                {selectedNominee.department && (selectedNominee.role_title || selectedNominee.title) && ' • '}
                {(selectedNominee.role_title || selectedNominee.title) && `Position: ${selectedNominee.role_title || selectedNominee.title}`}
              </p>
            </div>
            <button
              onClick={handleClear}
              className="text-ese-ink-blue hover:text-ese-ink-navy text-sm"
            >
              Change
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default SmartNomineeSearch

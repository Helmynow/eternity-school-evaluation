import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { supabase } from '../../lib/supabase'
import AnnouncementBanner from '../common/AnnouncementBanner'
// Logo path - public assets are served at root
const logoPath = '/assets/media/logo-no-bound.png'

const Layout = ({ children }) => {
  const { user, role, signOut, isCEO, isPNC, isDepartmentHead } = useAuth()
  const location = useLocation()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleSignOut = async () => {
    await signOut()
    window.location.href = '/'
  }

  const navItems = [
    { 
      path: '/', 
      label: 'Dashboard', 
      icon: '/assets/icons/dashboard.png', 
      roles: ['ceo', 'pnc', 'department_head', 'staff'],
      isDashboard: true
    },
    { 
      path: '/survey', 
      label: 'Survey', 
      icon: '/assets/icons/assessment.png', 
      roles: ['ceo', 'pnc', 'department_head', 'staff']
    },
    ]

  const adminNavItems = [
    { 
      path: '/admin/dashboard', 
      label: 'Admin Dashboard', 
      icon: '/assets/icons/Analytics.png', 
      roles: ['ceo', 'pnc'] 
    },
    { 
      path: '/admin/cycles', 
      label: 'Cycles', 
      icon: '/assets/icons/calander.png', 
      roles: ['ceo', 'pnc'] 
    },
    { 
      path: '/admin/staff', 
      label: 'Staff', 
      icon: '/assets/icons/users.png', 
      roles: ['ceo', 'pnc'] 
    },
    { 
      path: '/admin/objections', 
      label: 'Objections', 
      icon: '/assets/icons/warning_alert.png', 
      roles: ['ceo', 'pnc'] 
    },
    { 
      path: '/admin/announcements', 
      label: 'Announcements', 
      icon: '/assets/icons/notification.png', 
      roles: ['ceo', 'pnc'] 
    },
    { 
      path: '/admin/import', 
      label: 'Import', 
      icon: '/assets/icons/upload.png', 
      roles: ['ceo', 'pnc'] 
    },
    { 
      path: '/admin/integration', 
      label: 'Integration', 
      icon: '/assets/icons/communication.png', 
      roles: ['ceo'] 
    },
    { 
      path: '/admin/settings', 
      label: 'Settings', 
      icon: '/assets/icons/change.png', 
      roles: ['ceo'] 
    },
  ]

  const utilityNavItems = [
    { 
      path: '/reports', 
      label: 'Reports', 
      icon: '/assets/icons/Analytics.png', 
      roles: ['ceo', 'pnc', 'department_head', 'staff'] 
    },
    { 
      path: '/history', 
      label: 'History', 
      icon: '/assets/icons/review.png', 
      roles: ['ceo', 'pnc', 'department_head', 'staff'] 
    },
    { 
      path: '/notifications', 
      label: 'Notifications', 
      icon: '/assets/icons/notification.png', 
      roles: ['ceo', 'pnc', 'department_head', 'staff'] 
    },
  ]

  const allNavItems = [
    ...navItems,
    { 
      path: '/eom/nominate', 
      label: 'EOM Nominate', 
      icon: '/assets/icons/announcments.png', 
      roles: ['ceo', 'pnc', 'department_head'] 
    },
    { 
      path: '/eom/vote', 
      label: 'EOM Vote', 
      icon: '/assets/icons/vote.png', 
      roles: ['ceo', 'pnc', 'department_head'] 
    },
    { 
      path: '/mre/evaluate', 
      label: 'MRE Evaluate', 
      icon: '/assets/icons/assessment.png', 
      roles: ['ceo', 'pnc', 'department_head', 'staff'] 
    },
    ...utilityNavItems,
    ...adminNavItems,
  ]

  const filteredNavItems = allNavItems.filter(item => {
    if (item.roles.includes('all')) return true
    if (isCEO) return true
    if (isPNC && item.roles.includes('pnc')) return true
    if (isDepartmentHead && item.roles.includes('department_head')) return true
    if (item.roles.includes('staff')) return true
    return false
  })

  return (
    <div className="min-h-screen bg-ese-ink-white flex flex-col">
      {/* Global Header */}
      <header className="bg-white border-b border-ese-accent-beige shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-3">
              <img 
                src={logoPath} 
                alt="Eternity School Logo" 
                className="h-10 w-auto"
                onError={(e) => {
                  e.target.style.display = 'none'
                }}
              />
              <span className="hidden">ESE</span>
              <div className="flex flex-col">
                <span className="text-sm font-heading font-bold text-ese-lang-900">
                  EVALVision
                </span>
                <span className="text-xs text-ese-ink-blue">
                  Eternity School Evaluation
                </span>
              </div>
            </Link>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-ese-accent-beige transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-ese-lang-500 flex items-center justify-center text-white font-semibold">
                  {user?.email?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className="hidden md:block text-sm text-ese-ink-navy">
                  {user?.email || 'User'}
                </span>
                <span className="text-xs px-2 py-1 rounded-full bg-ese-accent-mustard text-ese-ink-navy font-medium">
                  {role?.toUpperCase() || 'STAFF'}
                </span>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-ese-accent-beige py-1 z-50">
                  <div className="px-4 py-2 border-b border-ese-accent-beige">
                    <p className="text-sm font-medium text-ese-ink-navy">{user?.email}</p>
                    <p className="text-xs text-ese-ink-blue capitalize">{role}</p>
                  </div>
                  <button
                    onClick={handleSignOut}
                    className="w-full text-left px-4 py-2 text-sm text-ese-ink-navy hover:bg-ese-accent-beige transition-colors"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Bar - Card Style */}
      <nav className="ese-nav-card-band">
        <div className="ese-nav-card-container">
          {filteredNavItems.map((item) => {
            const isActive = location.pathname === item.path
            const activeClass = isActive 
              ? (item.isDashboard ? 'ese-nav-card--active-dashboard' : 'ese-nav-card--active')
              : ''
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`ese-nav-card ${activeClass}`}
              >
                <div className="ese-nav-card__icon">
                  <div className="ese-nav-card__icon-graphic">
                    <img 
                      src={item.icon} 
                      alt={item.label}
                      className="ese-nav-card__icon-img"
                      onError={(e) => {
                        // Fallback if icon doesn't load
                        e.target.style.display = 'none'
                        e.target.parentElement.innerHTML = `<span style="font-size: 1.5rem;">${item.label.charAt(0)}</span>`
                      }}
                    />
                  </div>
                </div>
                <span className="ese-nav-card__label">{item.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        <AnnouncementBanner />
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-ese-ink-offwhite border-t border-ese-accent-beige py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-ese-ink-blue">
          <p>Eternity School of Egypt - Evaluation & Recognition System</p>
          <p className="text-xs mt-1">"Developing lifelong learners"</p>
        </div>
      </footer>
    </div>
  )
}

export default Layout


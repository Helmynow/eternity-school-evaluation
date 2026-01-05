import PropTypes from 'prop-types'
import { useAuth } from '../../hooks/useAuth'

const roleHierarchy = {
  staff: 1,
  department_head: 2,
  pnc: 3,
  ceo: 4,
}

const normalizeRole = (role) => (typeof role === 'string' ? role.toLowerCase() : null)

const getEffectiveRole = ({ role, isCEO, isPNC, isDepartmentHead }) => {
  // Prefer explicit role value if present
  const normalized = normalizeRole(role)
  if (normalized && roleHierarchy[normalized]) return normalized

  // Fall back to derived flags (email heuristics in useAuth)
  if (isCEO) return 'ceo'
  if (isPNC) return 'pnc'
  if (isDepartmentHead) return 'department_head'
  return 'staff'
}

const computeMinRequiredLevel = (roles) => {
  if (!Array.isArray(roles) || roles.length === 0) return roleHierarchy.staff
  if (roles.includes('all')) return roleHierarchy.staff

  const levels = roles
    .map(normalizeRole)
    .map((r) => roleHierarchy[r])
    .filter(Boolean)

  // If an unknown role is provided, be conservative and require CEO.
  if (levels.length === 0) return roleHierarchy.ceo
  return Math.min(...levels)
}

const AccessDenied = ({ title, subtitle }) => (
  <div className="p-6 text-center">
    <p className="text-ese-ink-medium text-lg">{title}</p>
    {subtitle ? <p className="text-ese-ink-light mt-2">{subtitle}</p> : null}
  </div>
)

AccessDenied.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string,
}

/**
 * Enforces role-based access at the router level.
 *
 * `roles` matches the app's role names: ceo, pnc, department_head, staff.
 *
 * Semantics: a user with higher role always passes (CEO passes everything).
 */
const RequireRole = ({ roles, children, deniedTitle = 'Access Denied', deniedSubtitle = 'Insufficient permissions' }) => {
  const { user, role, loading, isCEO, isPNC, isDepartmentHead } = useAuth()

  // App.jsx already gates by auth, but keep this defensive.
  if (!user) {
    return <AccessDenied title={deniedTitle} subtitle="Please sign in." />
  }

  if (loading) {
    return (
      <div className="min-h-[240px] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ese-lang-900" />
      </div>
    )
  }

  const effectiveRole = getEffectiveRole({ role, isCEO, isPNC, isDepartmentHead })
  const userLevel = roleHierarchy[effectiveRole] || 0
  const minRequiredLevel = computeMinRequiredLevel(roles)

  if (userLevel < minRequiredLevel) {
    return <AccessDenied title={deniedTitle} subtitle={deniedSubtitle} />
  }

  return children
}

RequireRole.propTypes = {
  roles: PropTypes.arrayOf(PropTypes.string).isRequired,
  children: PropTypes.node.isRequired,
  deniedTitle: PropTypes.string,
  deniedSubtitle: PropTypes.string,
}

export default RequireRole

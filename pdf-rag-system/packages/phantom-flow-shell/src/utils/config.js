/**
 * Configuration helpers for defining modules and roles.
 * 
 * @typedef {Object} ModuleFeature
 * @property {string} id - Unique feature ID
 * @property {string} name - Display name
 * @property {string} [desc] - Description
 * 
 * @typedef {Object} ModuleDefinition
 * @property {string} id - Unique module ID
 * @property {string} title - Display title
 * @property {import('vue').Component} icon - Lucide icon component
 * @property {string} [category] - Category for grouping
 * @property {import('vue').Component} component - The Vue component to render
 * @property {ModuleFeature[]} [features] - Sub-features (tabs)
 * 
 * @typedef {Object} RoleDefinition
 * @property {string} id - Unique role ID
 * @property {string} name - Display name
 * @property {string} [group] - Role group
 * @property {string} [groupName] - Role group display name
 * @property {string} [description] - Description
 * @property {string[]} defaultModules - Module IDs enabled by default
 * @property {string} [color] - Theme color
 */

/**
 * Define a module for the shell.
 * @param {ModuleDefinition} def
 * @returns {ModuleDefinition}
 */
export function defineModule(def) {
  if (!def.id) throw new Error('[PhantomFlow] defineModule: id is required')
  if (!def.title) throw new Error('[PhantomFlow] defineModule: title is required')
  if (!def.icon) throw new Error('[PhantomFlow] defineModule: icon is required')
  if (!def.component) throw new Error('[PhantomFlow] defineModule: component is required')
  return {
    features: [],
    category: 'default',
    ...def,
  }
}

/**
 * Define a role for the shell.
 * @param {RoleDefinition} def
 * @returns {RoleDefinition}
 */
export function defineRole(def) {
  if (!def.id) throw new Error('[PhantomFlow] defineRole: id is required')
  if (!def.name) throw new Error('[PhantomFlow] defineRole: name is required')
  return {
    defaultModules: [],
    ...def,
  }
}

/**
 * Persistence helpers — thin wrappers around localStorage.
 */
export const storage = {
  getEnabledModules() {
    const saved = localStorage.getItem('pf_modules')
    if (saved) { try { return JSON.parse(saved) } catch { return null } }
    return null
  },
  saveEnabledModules(ids) {
    localStorage.setItem('pf_modules', JSON.stringify(ids))
  },
  getEnabledFeatures() {
    const saved = localStorage.getItem('pf_features')
    if (saved) { try { return JSON.parse(saved) } catch { return null } }
    return null
  },
  saveEnabledFeatures(ids) {
    localStorage.setItem('pf_features', JSON.stringify(ids))
  },
  getUserRole() {
    return localStorage.getItem('pf_role') || null
  },
  saveUserRole(roleId) {
    localStorage.setItem('pf_role', roleId)
  },
  getUser() {
    try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} }
  },
  getToken() {
    return localStorage.getItem('access_token') || null
  },
  clear() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    localStorage.removeItem('pf_role')
    localStorage.removeItem('pf_modules')
    localStorage.removeItem('pf_features')
  },
}

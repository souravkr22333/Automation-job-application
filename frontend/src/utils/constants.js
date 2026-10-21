export const APP_CONFIG = {
  name: 'AutoApply AI',
  version: '1.0.0',
  company: 'AutoApply Inc.',
};

export const JOB_TYPES = {
  FULL_TIME: 'full-time',
  PART_TIME: 'part-time',
  CONTRACT: 'contract',
  REMOTE: 'remote',
  INTERNSHIP: 'internship',
};

export const APPLICATION_STATUS = {
  APPLIED: 'applied',
  REVIEWING: 'reviewing',
  INTERVIEWING: 'interviewing',
  OFFERED: 'offered',
  REJECTED: 'rejected',
};

export const ATS_SCORE_RANGES = {
  EXCELLENT: { min: 90, max: 100, label: 'Excellent' },
  GOOD: { min: 70, max: 89, label: 'Good' },
  AVERAGE: { min: 50, max: 69, label: 'Average' },
  NEEDS_IMPROVEMENT: { min: 0, max: 49, label: 'Needs Improvement' },
};

export const STORAGE_KEYS = {
  TOKEN: 'token',
  USER: 'user',
  THEME: 'theme',
  SETTINGS: 'settings',
};
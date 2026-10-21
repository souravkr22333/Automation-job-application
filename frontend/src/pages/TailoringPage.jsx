/**
 * TailoringPage - Main page for template-based resume tailoring with AI assistance.
 * Combines all tailoring components: template selection, AI suggestions,
 * side-by-side comparison, ATS optimizer, version management, and export.
 */

import React, { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import TemplateSelector from '../components/tailoring/TemplateSelector';
import SideBySideComparison from '../components/tailoring/SideBySideComparison';
import AISuggestions from '../components/tailoring/AISuggestions';
import ATSOptimizer from '../components/tailoring/ATSOptimizer';
import VersionManager from '../components/tailoring/VersionManager';
import ExportOptions from '../components/tailoring/ExportOptions';
import useTailoring from '../hooks/useTailoring';
import { useAuth } from '../contexts/AuthContext';

const TailoringPage = () => {
  const { resumeId: paramResumeId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('template');
  const [jobDescription, setJobDescription] = useState('');
  const [jobId, setJobId] = useState('');

  const {
    // Template
    templates,
    selectedTemplate,
    templateLoading,
    selectTemplate,
    applyTemplate,

    // Tailoring
    tailoringStatus,
    tailoredText,
    changes,
    keywordsAdded,
    tailorError,
    startTailoring,
    batchTailor,
    resetTailoring,

    // ATS
    atsScore,
    atsIssues,
    atsRecommendations,
    matchedKeywords,
    missingKeywords,
    atsLoading,
    checkATS,
    optimizeATS,

    // Version
    versions,
    selectedVersion,
    versionLoading,
    selectVersion,
    compareVersions,
    comparisonResult,
    comparing,
    rollbackVersion,
    createVersion,

    // Export
    downloadPDF,
    downloadDOCX,
    downloadTXT,
  } = useTailoring(paramResumeId);

  // For SideBySideComparison, use the original resume text from the latest version
  const originalText = versions.length > 1 ? versions[versions.length - 1]?.parsed_text : '';
  const currentText = tailoredText || versions[0]?.parsed_text || '';

  // ============================================================
  // HANDLERS
  // ============================================================

  const handleTemplateSelect = useCallback(async (template) => {
    selectTemplate(template);
    if (paramResumeId) {
      try {
        await applyTemplate(template.id);
      } catch (error) {
        console.error('Failed to apply template:', error);
      }
    }
  }, [paramResumeId, selectTemplate, applyTemplate]);

  const handleTailor = useCallback(async () => {
    if (!jobId && !jobDescription) {
      alert('Please provide a Job ID or paste a job description to tailor for.');
      return;
    }
    try {
      await startTailoring(jobId || jobDescription, selectedTemplate?.id);
      setActiveTab('compare');
    } catch (error) {
      console.error('Tailoring failed:', error);
    }
  }, [jobId, jobDescription, selectedTemplate, startTailoring]);

  const handleCheckATS = useCallback(async () => {
    if (!jobDescription) {
      alert('Please paste a job description to check ATS compatibility.');
      return;
    }
    try {
      await checkATS(jobDescription);
      setActiveTab('ats');
    } catch (error) {
      console.error('ATS check failed:', error);
    }
  }, [jobDescription, checkATS]);

  const handleAtsOptimize = useCallback(async () => {
    if (!jobDescription) {
      alert('Please paste a job description to optimize for ATS.');
      return;
    }
    try {
      await optimizeATS(jobDescription);
      setActiveTab('compare');
    } catch (error) {
      console.error('ATS optimization failed:', error);
    }
  }, [jobDescription, optimizeATS]);

  const handleSuggestions = useCallback(() => {
    // Mock suggestions for demonstration
    return [
      {
        id: '1',
        type: 'keyword',
        title: 'Add missing keywords',
        description: 'The job description mentions several keywords missing from your resume.',
        details: true,
        currentText: 'Proficient in software development',
        suggestedText: 'Proficient in React, TypeScript, and Node.js development',
        impact: 'high',
        effort: 'low'
      },
      {
        id: '2',
        type: 'structure',
        title: 'Reorganize experience section',
        description: 'Your most relevant experience should appear first.',
        details: true,
        currentText: 'Experience section ordered chronologically',
        suggestedText: 'Reordered to highlight most relevant roles first',
        impact: 'medium',
        effort: 'medium'
      },
      {
        id: '3',
        type: 'content',
        title: 'Quantify achievements',
        description: 'Add specific metrics to your bullet points.',
        details: true,
        currentText: 'Led development team',
        suggestedText: 'Led a team of 5 developers, delivering 3 major releases on schedule',
        impact: 'high',
        effort: 'medium'
      }
    ];
  }, []);

  // ============================================================
  // TABS CONFIGURATION
  // ============================================================

  const tabs = [
    { id: 'template', label: 'Template', icon: '🎨', description: 'Choose a resume template' },
    { id: 'tailor', label: 'Tailor', icon: '✂️', description: 'AI-powered tailoring' },
    { id: 'compare', label: 'Compare', icon: '📊', description: 'See changes side-by-side' },
    { id: 'ats', label: 'ATS', icon: '⚡', description: 'Optimize for ATS' },
    { id: 'suggestions', label: 'AI Suggestions', icon: '💡', description: 'Improvement ideas' },
    { id: 'versions', label: 'Versions', icon: '📚', description: 'Version history' },
    { id: 'export', label: 'Export', icon: '📥', description: 'Download your resume' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Resume Tailoring Studio
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                AI-powered resume optimization with template-based styling
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {tailoringStatus === 'done' && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200">
                  ✓ Tailored
                </span>
              )}
              {atsScore !== null && (
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  atsScore >= 80 ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200' :
                  atsScore >= 60 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200' :
                  'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                }`}>
                  ATS: {atsScore}
                </span>
              )}
              <button
                onClick={resetTailoring}
                className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center space-x-2 overflow-x-auto pb-2">
            {tabs.map((tab, idx) => (
              <React.Fragment key={tab.id}>
                <button
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all
                    ${activeTab === tab.id
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-200 dark:shadow-blue-900/50'
                      : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }
                  `}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
                {idx < tabs.length - 1 && (
                  <div className="w-4 h-px bg-gray-300 dark:bg-gray-600" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6">
            {/* Template Selection Tab */}
            {activeTab === 'template' && (
              <TemplateSelector
                templates={templates}
                selectedTemplate={selectedTemplate}
                onSelect={handleTemplateSelect}
                loading={templateLoading}
              />
            )}

            {/* Tailor Resume Tab */}
            {activeTab === 'tailor' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    AI-Powered Resume Tailoring
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                    Provide a job ID or paste a job description to tailor your resume for a specific position.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Job ID */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Job ID (optional)
                    </label>
                    <input
                      type="text"
                      value={jobId}
                      onChange={(e) => setJobId(e.target.value)}
                      placeholder="e.g., 550e8400-e29b-41d4-a716-446655440000"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
                    />
                  </div>

                  {/* Template selection in this tab */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Template (optional)
                    </label>
                    <select
                      value={selectedTemplate?.id || ''}
                      onChange={(e) => {
                        const t = templates.find(t => t.id === e.target.value);
                        if (t) selectTemplate(t);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
                    >
                      <option value="">No template (default format)</option>
                      {templates.map((t) => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Job Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Or Paste Job Description
                  </label>
                  <textarea
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    rows={8}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm font-mono"
                    placeholder="Paste the full job description here for AI-powered analysis and tailoring..."
                  />
                </div>

                {/* Action */}
                <div className="flex items-center space-x-4">
                  <button
                    onClick={handleTailor}
                    disabled={tailoringStatus === 'tailoring' || (!jobId && !jobDescription.trim())}
                    className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
                  >
                    {tailoringStatus === 'tailoring' ? (
                      <span className="flex items-center space-x-2">
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        <span>Tailoring...</span>
                      </span>
                    ) : (
                      '✨ Tailor Resume'
                    )}
                  </button>

                  <button
                    onClick={() => setActiveTab('ats')}
                    className="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    Check ATS First
                  </button>
                </div>

                {/* Error state */}
                {tailorError && (
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-sm text-red-700 dark:text-red-300">
                      ❌ {tailorError}
                    </p>
                  </div>
                )}

                {/* Success state */}
                {tailoringStatus === 'done' && (
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <p className="text-sm text-green-700 dark:text-green-300">
                      ✓ Resume tailored successfully! View the changes in the Compare tab.
                    </p>
                    {keywordsAdded && keywordsAdded.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {keywordsAdded.map((kw, idx) => (
                          <span key={idx} className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-200 rounded-full">
                            +{kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Side-by-Side Comparison Tab */}
            {activeTab === 'compare' && (
              <SideBySideComparison
                originalText={originalText}
                tailoredText={currentText}
                changes={changes}
                keywordsAdded={keywordsAdded}
              />
            )}

            {/* ATS Optimizer Tab */}
            {activeTab === 'ats' && (
              <ATSOptimizer
                atsScore={atsScore}
                issues={atsIssues}
                recommendations={atsRecommendations}
                matchedKeywords={matchedKeywords}
                missingKeywords={missingKeywords}
                loading={atsLoading}
                onCheckATS={handleCheckATS}
                onOptimize={handleAtsOptimize}
                onGetSuggestions={handleSuggestions}
                jobDescription={jobDescription}
                setJobDescription={setJobDescription}
              />
            )}

            {/* AI Suggestions Tab */}
            {activeTab === 'suggestions' && (
              <AISuggestions
                suggestions={handleSuggestions()}
                onAccept={(id) => console.log('Accepted:', id)}
                onReject={(id) => console.log('Rejected:', id)}
                onModify={(id) => console.log('Modify:', id)}
                loading={false}
              />
            )}

            {/* Version Manager Tab */}
            {activeTab === 'versions' && (
              <VersionManager
                versions={versions}
                selectedVersion={selectedVersion}
                loading={versionLoading}
                onSelectVersion={selectVersion}
                onCompare={compareVersions}
                onRollback={rollbackVersion}
                onCreateVersion={createVersion}
              />
            )}

            {/* Export Options Tab */}
            {activeTab === 'export' && (
              <ExportOptions
                onExportPDF={downloadPDF}
                onExportDOCX={downloadDOCX}
                onExportTXT={downloadTXT}
                templates={templates}
                selectedTemplate={selectedTemplate}
                disabled={!currentText}
                tailoringStatus={tailoringStatus}
                versionCount={versions.length}
              />
            )}
          </div>
        </div>

        {/* Tips Footer */}
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/10 dark:to-purple-900/10 rounded-xl border border-blue-100 dark:border-blue-900/30">
          <div className="flex items-start space-x-3">
            <span className="text-xl">💡</span>
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                Tips for Best Results
              </h4>
              <ul className="mt-1 text-xs text-gray-500 dark:text-gray-400 space-y-1">
                <li>• Select a template first to see how your resume will look</li>
                <li>• Paste the full job description for the most accurate tailoring</li>
                <li>• Check ATS score before and after tailoring to see improvement</li>
                <li>• Create version snapshots before major changes</li>
                <li>• Export as PDF for applications, DOCX for further editing</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TailoringPage;

